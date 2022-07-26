#!/usr/bin/env python

import sys
import time
import threading
from conf import parse_config
from db_man import DBConnector
from time_util import get_time_now, get_sleep_time, get_time_isoformat
from model_server import ServerPostModel, PointDataWithTS
from diffsum import diffsum_timespan_sharp

def worker(server, config):
    db_agent = DBConnector(config.AgentDB, config)
    db_que = DBConnector(config.QueDB, config)
    tag = f"Mid:{server.ServerID}: "
    while True:
        # since db is set to None when the connection has been rejected.
        # see below.
        if db_agent is None:
            db_agent = DBConnector(config.AgentDB, config)
        if db_que is None:
            db_que = DBConnector(config.QueDB, config)
        #
        config.logger.debug(f"{tag}resumed: {get_time_isoformat()}")
        cur_ts = get_time_now().timestamp()
        # IntegrationDeferTime delays to start this process.
        # So, cur_ts is enough to get the number of sampling data.
        try:
            psvt = db_agent.get_data_raw(server.Points, cur_ts)
        except db_agent.ConnectionError as e:
            db_agent = None
            # through here internal loop and try to connect DB.
        else:
            out_data = []
            del_data = []
            for pid,svt in psvt.items():
                config.logger.debug(f"{tag}{pid}: {len(svt)} data exist.")
                if len(svt) > 0:
                    if config.Points[pid].Integration is True:
                        sumspan = config.Points[pid].IntegrationSpan
                        ret = diffsum_timespan_sharp(
                                svt, sumspan=sumspan,
                                margin=server.IntegrationMarginTime,
                                config=config)
                        vsum_list = ret["vsum_list"]
                        rest_offset = ret["rest_offset"]
                        vx = PointDataWithTS(PointID=pid, Values=vsum_list,
                                            TSLastValue=get_time_isoformat(ts=svt[rest_offset][0]))
                        config.logger.debug(f"{tag}{pid}: {vx.Values} {vx.TSLastValue}")
                        out_data.append(vx.dict())
                        if rest_offset > 0:
                            # Note: score - 1 is to leave the latest data.
                            last_score = svt[rest_offset-1][0] - 1
                            del_data.append((server.Points, last_score))

            # post data to the queue db.
            if len(out_data) > 0:
                config.logger.debug(f"{tag}{len(out_data)} data queued.")
                config.logger.debug(f"{tag}{out_data}")
                try:
                    db_que.post_data_ready(server.ServerID, out_data)
                except db_que.ConnectionError as e:
                    db_que = None
                    # try to connect DB.
                else:
                    # delete data if posting data is successful.
                    try:
                        for p,s in del_data:
                            db_agent.del_data_raw(p,s)
                    except db_agent.ConnectionError as e:
                        db_agent = None
                        # through here and try to connedt to the db next time.
                        pass
        # sleep
        config.logger.debug(f"{tag}sleep: {get_time_isoformat()}")
        time.sleep(get_sleep_time(server.PostInterval,
                                  server.IntegrationMarginTime))

def start_wokers(config):
    workers = []
    for x in config.Servers:
        config.logger.debug(f"starting worker for {x.ServerID}")
        workers.append(threading.Thread(target=worker,
                                        args=(x, config),
                                        daemon=False))
    # start threads.
    for x in workers:
        x.start()

#
# Main
#

PROG_NAME = "middle_man"

if __name__ == "__main__":
    config = parse_config(PROG_NAME, sys.argv[1:])
    config.logger.info(f"Starting {PROG_NAME}")
    start_wokers(config)
