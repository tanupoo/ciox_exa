#!/usr/bin/env python

from argparse import ArgumentParser
import redis

def main(opt):

    def get_kv(rkey):
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

    def get_each(iterator):
        for rkey in iterator:
            get_kv(rkey)

    con = redis.Redis(host=opt.ip_addr, port=opt.ip_port)

    if opt.cmd == "size":
        if opt.key is None:
            print(con.dbsize())
        else:
            print(con.memory_usage(opt.key))
            #print(con.debug_object(opt.key))
    elif opt.cmd == "delete":
        if opt.key is None:
            if "all" in opt.names:
                print("ERROR: 'all' is not acceptable. use the -n option.")
                exit(1)
            for name in opt.names:
                for k in con.scan_iter(f"{name}:*"):
                    n = con.delete(k)
                    print(f"{k} deleted.")
        else:
            n = con.delete(k)
            print(f"{k} deleted.")
    elif opt.cmd == "show":
        if opt.key is None:
            if "all" in opt.names:
                get_each(con.scan_iter())
            else:
                for name in opt.names:
                    get_each(con.scan_iter(f"{name}:*"))
        else:
            get_kv(bytes(opt.key, "utf-8"))
    else:
        raise RuntimeError

#
# main
#
commands = ["show", "delete", "size"]
ap = ArgumentParser(description="redis DB manager.")
ap.add_argument("cmd", metavar="CMD", nargs="?",
                choices=commands,
                default="show",
                help=f"command {commands}")
ap.add_argument("-n", action="store", dest="names",
                default="all",
                nargs="+",
                choices=["all", "pt", "rdy", "retx"],
                help="specify the category name list. e.g. -n rdy retx")
ap.add_argument("-k", action="store", dest="key",
                help="specify a key")
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
