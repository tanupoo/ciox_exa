#!/usr/bin/env python

import sys
import time
import threading
from conf import parse_config
from db_man import DBConnector
from time_util import get_time_now, get_sleep_time, get_next_sharp_time, get_time_isoformat
from model_server import ServerPostModel, PointDataWithTS
import requests
import gzip
import json


"""
Requests Auth
https://requests.readthedocs.io/en/latest/user/advanced/#session-objects
"""
def worker(server, config):
    db_que = DBConnector(config.QueDB, config)
    tag = f"Agent:{server.ServerID}: "
    auth = None
    if server.ClientAuthInfo is None or server.ClientAuthInfo.AuthType is None:
        pass
    elif server.ClientAuthInfo.AuthType == "Basic":
        cred = server.ClientAuthInfo.AuthInfo
        if cred is not None:
            auth = requests.auth.HTTPBasicAuth(cred.UserName, cred.Password)
        else:
            raise ValueError(f"{tag}No credentials")
    else:
        raise ValueError(f"authtype not implemented yet, {server.ClientAuthInfo.AuthType}")
    if server.Compression is True:
        headers = {
            'Content-Type': 'application/json',
            'Content-Encoding': 'gzip'
            }
    else:
        headers = {
            'Content-Type': 'application/json',
            }

    #
    while True:
        config.logger.debug(f"{tag}resumed: {get_time_isoformat()}")
        data = db_que.get_data_ready(server.ServerID)
        if len(data) > 0:
            xd = ServerPostModel(Data=data).dict()
            # XXX create data
            if server.Compression is True:
                body = gzip.compress(json.dumps(xd).encode())
            else:
                body = json.dumps(xd)
            # Send the request.
            try:
                result = requests.post(server.EPR, auth=auth,
                                        timeout=server.Timeout,
                                        headers=headers, json=body)
            except requests.ConnectionError:
                config.logger.error(f"{tag}Connection Error, "
                            f"{server.ServerID}, {e}")
                db_que.post_data_retx(server.ServerID, data)
            except requests.Timeout as e:
                config.logger.error(f"{tag}connection timeout, "
                            f"{server.ServerID}, {e}")
                db_que.post_data_retx(server.ServerID, data)
            except Exception as e:
                config.logger.critical(f"{tag}system error, "
                            f"{server.ServerID}, {e}")
            else:
                if result.status_code == requests.codes.ok:
                    config.logger.debug(f"{tag}submission successful.")
                else:
                    config.logger.debug(f"{tag}submission failed with code {result.status_code}.")
                    db_que.post_data_retx(server.ServerID, data)
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

PROG_NAME = "post_man"

if __name__ == "__main__":
    config = parse_config(PROG_NAME, sys.argv[1:])
    config.logger.info(f"Starting {PROG_NAME}")
    start_wokers(config)
