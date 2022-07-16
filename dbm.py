#!/usr/bin/env python

from argparse import ArgumentParser
import redis

def main(opt):
    con = redis.Redis(host=opt.ip_addr, port=opt.ip_port)

    if opt.name == "all":
        it = con.scan_iter()
    else:
        it = con.scan_iter(f"{opt.name}:*")

    if opt.delete_name:
        if opt.name == "all":
            print("ERROR: 'all' is not acceptable. use the -n option.")
            exit(0)
        for k in con.scan_iter(f"{opt.name}:*"):
            con.delete(k)
    else:
        for rkey in it:
            ktype = con.type(rkey)
            if ktype == b'zset':
                for rv in con.zscan_iter(rkey):
                    (v, s) = rv
                    print(rkey.decode(), s, v.decode().split(","))
            elif ktype == b'list':
                for v in con.lrange(rkey, 0, -1):
                    print(rkey.decode(), v)
            else:
                print(con.type(rkey), rkey.decode())

#
# main
#
ap = ArgumentParser(description="redis viewer")
ap.add_argument("-n", action="store", dest="name",
                default="all",
                choices=["all", "pt", "rdy", "retx"],
                help="specify a category name.")
ap.add_argument("--delete", action="store_true", dest="delete_name",
                help="delete entries in the specified category")
ap.add_argument("-a", action="store", dest="ip_addr",
                default="127.0.0.1",
                help="specify the ip address of the redis server.")
ap.add_argument("-p", action="store", dest="ip_port",
                type=int, default=6379,
                help="specify the port number of the redis server.")

opt = ap.parse_args()

try:
    main(opt)
except Exception as e:
    print(e)
    exit(1)
