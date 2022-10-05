#!/usr/bin/env python

from conf import parse_config
import threading
from agent_slmp import slmp_start_agent
from db_man import DBConnector
import time
import sys
from time_util import get_sleep_time, get_time_isoformat

def agent_worker(target, config):
    # make an agent.
    if target.Protocol == "SLMP":
        agent = slmp_start_agent(target, config)
    else:
        raise ValueError("unknown Protocol {x.Protocol}.")
    # start the main loop
    db = None
    tag = f"Agent:{agent.target.TargetID}: "
    while True:
        if db is None:
            # since db is set to None when the connection has been rejected.
            # see below.
            db = DBConnector(config.AgentDB, config)
        agent.logger.debug(f"{tag}resumed: {get_time_isoformat()}")
        try:
            result = agent.pull()
        except ConnectionRefusedError as e:
            agent.logger.error(f"{tag}connection refused, "
                         f"{agent.IPAddr}:{agent.IPPort}, {e}")
        except TimeoutError as e:
            agent.logger.error(f"{tag}connection timeout, "
                         f"{agent.IPAddr}:{agent.IPPort}, {e}")
        except Exception as e:
            agent.logger.critical(f"{tag}system error, "
                         f"{agent.IPAddr}:{agent.IPPort}, {e}")
        else:
            pdata = []
            try:
                for p in agent.target.Points:
                    pdata.append(( p.PointID, result[p.Position-1] ))
            except IndexError as e:
                agent.logger.error(f"{tag}"
                                f"result length {len(result)} was too short "
                                f"for Postion {p.Position}. Check ReadCount.")
            try:
                db.post_data_raw(pdata)
            except db.ConnectionError as e:
                db = None
                # through here internal loop and try to connect DB.
            else:
                agent.logger.debug(f"{tag}posted data: {pdata}")
        # sleep
        sleep_time = get_sleep_time(agent.PullInterval)
        agent.logger.debug(f"{tag}sleep: {get_time_isoformat()}, "
                           f"resume in {sleep_time}.")
        time.sleep(sleep_time)

def start_wokers(config):
    workers = []
    for x in config.Targets:
        agent = threading.Thread(target=agent_worker,
                                 args=(x, config,),
                                 daemon=False)
        if agent is not False:
            workers.append(agent)
            config.logger.debug(f"starting worker for {x.TargetID}")
    # start threads.
    for x in workers:
        x.start()

#
# Main
#

PROG_NAME = "agent_man"

if __name__ == "__main__":
    config = parse_config(PROG_NAME, sys.argv[1:])
    config.logger.info(f"Starting {PROG_NAME}")
    start_wokers(config)
