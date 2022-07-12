#!/usr/bin/env python

import sys
import time
import threading
from conf import parse_config
from db_man import DBConnector
from time_util import get_time_now, get_sleep_time, get_next_sharp_time, get_time_isoformat
from model_server import ServerPostModel, PointDataWithTS
from diffsumspan import diffsumspan

# XXX
integration_margin = 0

def worker(server, config):
    db_agent = DBConnector(config.AgentDB, config)
    db_que = DBConnector(config.QueDB, config)
    tag = f"Agent:{server.ServerID}: "
    while True:
        config.logger.debug(f"{tag}resumed: {get_time_isoformat()}")
        cur_ts = get_time_now().timestamp()
        svt = db_agent.get_data_raw(server.Points, cur_ts + integration_margin)
        out_data = []
        for pid,svt in svt.items():
            config.logger.debug(f"{tag}{pid}: {len(svt)} data exist.")
            if len(svt) > 0:
                sumspan = getattr(config.Points[pid], "IntegrationTime")
                sumspan *= 60   # minutes
                vsum = diffsumspan(svt, sumspan=sumspan, margin=integration_margin)
                vx = PointDataWithTS(PointID=pid,
                                Values=vsum,
                                TSLastValue=get_time_isoformat(ts=svt[-1][0]))
                config.logger.debug(f"{tag}{pid}: {vx.Values} {vx.TSLastValue}")
                out_data.append(vx.dict())
                # Note: cur_ts - 1: is to leave the latest data.
                db_agent.del_data_raw(server.Points, cur_ts - 1)
        if len(out_data) > 0:
            config.logger.debug(f"{tag}{len(out_data)} data queued.")
            config.logger.debug(f"{tag}{out_data}")
            db_que.post_data_ready(server.ServerID, out_data)
        # sleep
        config.logger.debug(f"{tag}sleep: {get_time_isoformat()}")
        time.sleep(get_sleep_time(server.PostInterval))

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
