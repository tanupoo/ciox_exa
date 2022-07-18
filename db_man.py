import redis
import json
from datetime import datetime
import dateutil.parser
import dateutil.tz
import time
from time_util import get_time_isoformat, get_time_now

# XXX should be taken from the value of TZ env.
tz_info = dateutil.tz.gettz("Asia/Tokyo")

PREFIX_RAW = "pt:"
PREFIX_RETX = "retx:"
PREFIX_READY = "rdy:"

class DBConnector:

    def __init__(self, db_info, config):
        """
        db_info: { "IPAddr": str, "IPPort": int }
        config
        """
        self.logger = config.logger
        self.config = config
        self.conn = redis.Redis(db_info.IPAddr, db_info.IPPort)

    def get_key_raw(self, point_id):
        return f"{PREFIX_RAW}{point_id}"

    def get_key_ready(self, server_id):
        return f"{PREFIX_READY}{server_id}"

    def get_key_retx(self, server_id):
        return f"{PREFIX_RETX}{server_id}"

    def post_data_raw(self, point_data):
        """
        point_data: [ ( <PointID>, <Value> ), ... ]
        DB hashkey:
            see self.get_key_raw()
        DB key:
            **str** "<TS[seconds]>,<PointID>,<Value>"
        DB score:
            <TS[microseconds]>
        """
        dt = get_time_now(30)
        ts = get_time_isoformat(dt=dt)
        score = dt.timestamp()
        for x in point_data:
            point_id = x[0]
            value = x[1]
            hashkey = self.get_key_raw(point_id)
            key = f"{ts},{point_id},{value}"
            self.logger.debug(f"ZADD: {hashkey}, {key}, {score}")
            self.conn.zadd(hashkey, {key: score})

    def get_data_raw(self, points, cur_ts):
        """
        points: [ <PointID>, ... ]
        return:
            {
                <PointID>: [ (score, "val", "ts"), ... ], ...
            }
        Note: the type of ** val ** is str.
        """
        result = {}
        for pid in points:
            hashkey = self.get_key_raw(pid)
            stored_data = self.conn.zrange(hashkey, 0, cur_ts,
                                           byscore=True, withscores=True)
            pv = result.setdefault(pid, [])
            for xv in stored_data:
                # e.g. [(b'2022-07-09T22:27:53.011748+09:00,06_78_91:XB,81',
                #        1657373273.011748), ... ]
                (ts,pid,val) = [v.decode() for v in xv[0].split(b",")]
                pv.append((xv[1], val, ts))
        return result

    def del_data_raw(self, points, cur_ts):
        """
        points: [ <PointID>, ... ]
        """
        for pid in points:
            hashkey = self.get_key_raw(pid)
            self.conn.zremrangebyscore(hashkey, 0, cur_ts)

    def _post_data_queue(self, key, data):
        """
        data:
        """
        self.conn.rpush(key, json.dumps(data))

    def _get_data_queue(self, key):
        """
        return:
            [
                { "PointID": <PointID>, "Values": [...], TSLastValue: <TS> },
                ...
            ]
        """
        v = self.conn.rpop(key)
        if v is not None:
            return json.loads(v)
        else:
            return []

    def post_data_ready(self, server_id, out_data):
        """
        point_data: List[PointDataWithTS]
        """
        key = self.get_key_ready(server_id)
        self._post_data_queue(key, out_data)

    def get_data_ready(self, server_id):
        """
        return all record marked to READY and bound to the server_id.
        """
        return self._get_data_queue(self.get_key_ready(server_id))

    def post_data_retx(self, server_id, out_data):
        """
        point_data: List[PointDataWithTS]
        """
        key = self.get_key_retx(server_id)
        self._post_data_queue(key, out_data)

    def get_data_retx(self, server_id):
        """
        return all record marked to RETRY and bound to the server_id.
        """
        return self._get_data_queue(self.get_key_retx(server_id))
