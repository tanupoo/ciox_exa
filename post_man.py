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
    tag = f"Post:{server.ServerID}: "
    auth = None
    if not server.ClientAuthInfo or server.ClientAuthInfo["AuthType"] == "None":
        pass
    elif server.ClientAuthInfo["AuthType"] == "Basic":
        cred = server.ClientAuthInfo["AuthInfo"]
        if cred is not None:
            auth = requests.auth.HTTPBasicAuth(cred["Username"], cred["Password"])
        else:
            raise ValueError(f"{tag}No credentials")
    else:
        raise ValueError(f"authtype not implemented yet, {server.ClientAuthInfo.AuthType}")

    # create header
    if server.Compression is True:
        headers = {
            'Content-Type': 'application/json',
            'Content-Encoding': 'gzip'
            }
    else:
        headers = {
            'Content-Type': 'application/json',
            }

    # common process, but getting from the different db.
    def try_post_data(func_get_data):
        while True:
            try:
                data = func_get_data(server.ServerID)
            except db.ConnectionError as e:
                return False
            if len(data) == 0:
                # end of process in this time.
                break
            # preparing the post data.
            xd = ServerPostModel(Data=data).dict()
            # XXX compression is needed ?
            if server.Compression is True:
                body = gzip.compress(json.dumps(xd).encode())
            else:
                body = json.dumps(xd)
            # Send the data.
            success = False
            try:
                resp = requests.post(server.EPR, auth=auth,
                                        timeout=server.Timeout,
                                        headers=headers, data=body)
            except requests.ConnectionError as e:
                config.logger.error(f"{tag}Connection Error, "
                            f"{server.ServerID}, {e}")
            except requests.Timeout as e:
                config.logger.error(f"{tag}connection timeout, "
                            f"{server.ServerID}, {e}")
            except Exception as e:
                config.logger.error(f"{tag}system error, "
                            f"{server.ServerID}, {e}")
            else:
                if resp.status_code == requests.codes.ok:
                    config.logger.debug(f"{tag}submission successful.")
                    success = True
                else:
                    config.logger.error(f"{tag}submission failed with code {resp.status_code}.")
            # post the data for retrying
            if success is not True:
                try:
                    db.post_data_retx(server.ServerID, data)
                except db.ConnectionError as e:
                    pass
                else:
                    config.logger.debug(f"{tag}posted data to retry queue: {data}")
                # stop the process if any error occured.
                return False
            else:
                # interval for the next data.
                time.sleep(1)
        return True

    # main loop
    while True:
        config.logger.debug(f"{tag}resumed: {get_time_isoformat()}")
        db = DBConnector(config.QueDB, config)
        dataset = [db, server, db.get_data_ready]
        if try_post_data(db.get_data_ready) is True:
            # only successful.
            try_post_data(db.get_data_retx)
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
