import redis
import json
import dateutil.parser
import dateutil.tz
import time
from time_util import get_time_isoformat, get_time_now

PREFIX_RAW = "pt:"
PREFIX_RETX = "retx:"
PREFIX_READY = "rdy:"

class DBConnector:

    class ConnectionError(Exception):
        pass

    def __init__(self, db_info, config):
        """
        db_info: { "IPAddr": str, "IPPort": int }
        config
        """
        self.logger = config.logger
        self.config = config
        self.conn = redis.Redis(db_info.IPAddr, db_info.IPPort)

    def ping(self):
        return self._wrapper(self.conn.ping, tuple())

    def _wrapper(self, func, args, kwargs={}, msg=None):
        """
        wrapper to check the exceptions.
        return the result, or raise an exception.
        """
        try:
            ret = func(*args, **kwargs)
        except redis.exceptions.ConnectionError as e:
            self.logger.error(e)
            raise self.ConnectionError(f"{e}")
        except Exception as e:
            raise
        else:
            if msg is not None:
                self.logger.debug(msg)
            return ret

    def get_key_raw(self, point_id):
        return f"{PREFIX_RAW}{point_id}"

    def get_key_ready(self, server_id):
        return f"{PREFIX_READY}{server_id}"

    def get_key_retx(self, server_id):
        return f"{PREFIX_RETX}{server_id}"

    def is_valid_point_id(self, point_id):
        """
        check if the point_id is valid.
        point_id: None, "", 0 are NOT allowed.
        """
        if not point_id:
            return False
        else:
            return True

    def is_valid_point_ids(self, points):
        """
        check if the list of point_id is valid.
        return True, or point_id if error.
        """
        if not isinstance(points, list):
            return None
        for pid in points:
            if not self.is_valid_point_id(pid):
                return pid
        else:
            return True

    def post_data_raw(self, point_data, margin=0):
        """
        add data with the current timestamp as its score.
        point_data: [ ( <PointID>: str, <Value>: Union[str, int, float] ), ... ]
        return the number of post count, or False if error.

        the data model in the data of the point is like below:
            DB hashkey:
                see self.get_key_raw()
            DB key:
                **str** "<YYYY-mm-ddTHH:MM:SS+TZ>,<PointID>,<Value>"
            DB score:
                <Timestamp>
        """
        pid = self.is_valid_point_ids([x[0] for x in point_data])
        if pid is not True:
            self.logger.error("data contains invalid point_id, "
                                f"{pid} in {point_data}")
            return False
        dt = get_time_now(margin)
        ts = get_time_isoformat(dt=dt)
        score = dt.timestamp()
        post_count = 0
        for x in point_data:
            point_id = x[0]
            value = x[1]
            hashkey = self.get_key_raw(point_id)
            key = f"{ts},{point_id},{value}"
            self.logger.debug(f"ZADD: {hashkey}, {key}, {score}")
            # always return 1
            self._wrapper(self.conn.zadd, (hashkey, {key: score}))
            post_count += 1
        else:
            return post_count

    def get_data_raw(self, points, cur_ts=None):
        """
        retrieve all data matched with [0, cur_ts] of the score.
        points: [ <PointID>, ... ]
        cur_ts: timestamp
        return:
            {
                <PointID>: [ (score, "val", "ts"), ... ], ...
            }
        Note: the type of ** val ** is str.
        """
        pid = self.is_valid_point_ids(points)
        if pid is not True:
            self.logger.error("data contains invalid point_id, "
                                f"{pid} in {points}")
            return False
        return_val = {}
        for pid in points:
            hashkey = self.get_key_raw(pid)
            # always return a list even if any data don't exist.
            stored_data = self._wrapper(self.conn.zrange,
                                        (hashkey, 0, cur_ts),
                                        dict(byscore=True, withscores=True))
            pv = return_val.setdefault(pid, [])
            for xv in stored_data:
                (ts,pid,val) = [v.decode() for v in xv[0].split(b",")]
                pv.append((xv[1], val, ts))
        return return_val

    def del_data_raw(self, points, cur_ts):
        """
        delete all data matched with [0, cur_ts] of the score.
        points: [ <PointID>, ... ]
        cur_ts: timestamp

        return the number of delete count, or False if error.
        """
        pid = self.is_valid_point_ids(points)
        if pid is not True:
            self.logger.error("data contains invalid point_id, "
                                f"{pid} in {points}")
            return False
        delete_count = 0
        for pid in points:
            hashkey = self.get_key_raw(pid)
            if self._wrapper(self.conn.zremrangebyscore,
                             (hashkey, 0, cur_ts)) is False:
                return False
            delete_count += 1
        return delete_count

    def _post_data_queue(self, key, data):
        """
        key:
        data:
        return index in the list of key
        """
        return self._wrapper(self.conn.rpush, (key, json.dumps(data)))

    def _get_data_queue(self, key):
        """
        key:
        """
        v = self._wrapper(self.conn.rpop, (key,))
        if v is False:
            return False
        elif v is not None:
            return json.loads(v)
        else:
            return []

    def post_data_ready(self, server_id, out_data):
        """
        """
        key = self.get_key_ready(server_id)
        return self._post_data_queue(key, out_data)

    def get_data_ready(self, server_id):
        """
        return all record marked to READY and bound to the server_id.
        """
        return self._get_data_queue(self.get_key_ready(server_id))

    def post_data_retx(self, server_id, out_data):
        """
        """
        key = self.get_key_retx(server_id)
        return self._post_data_queue(key, out_data)

    def get_data_retx(self, server_id):
        """
        return all record marked to RETRY and bound to the server_id.
        """
        return self._get_data_queue(self.get_key_retx(server_id))
