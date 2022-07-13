#!/usr/bin/env python

from conf import parse_config
import threading
from agent_slmp import slmp_start_agent
from db_man import DBConnector
import time
import sys
from time_util import get_sleep_time, get_time_isoformat

def agent_worker(agent):
    db = DBConnector(config.AgentDB, config)
    tag = f"Agent:{agent.target.TargetID}: "
    while True:
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
            for p in agent.target.Points:
                pdata.append(( p.PointID, result[p.Position-1] ))
            db.post_data_raw(pdata)
            agent.logger.debug(f"{tag}posted data: {pdata}")
        agent.logger.debug(f"{tag}sleep: {get_time_isoformat()}")
        time.sleep(get_sleep_time(agent.PullInterval))

def start_wokers(config):
    workers = []
    for x in config.Targets:
        config.logger.debug(f"starting worker for {x.TargetID}")
        if x.Protocol == "SLMP":
            agent = slmp_start_agent(x, config)
            workers.append(threading.Thread(target=agent_worker,
                                            args=(agent,),
                                            daemon=False))
        else:
            raise ValueError("unknown Protocol {x.Protocol}.")
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
