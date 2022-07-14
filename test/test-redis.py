
import redis
con = redis.Redis(host="localhost", port=6379)

for rkey in con.scan_iter():
    ktype = con.type(rkey)
    if ktype == b'zset':
        for rv in con.zscan_iter(rkey):
            (v, s) = rv
            print(rkey.decode(), s, v.decode().split(","))
    elif ktype == b'list':
        for v in con.lrange(rkey, 0, -1):
              print(v)
    else:
        print(rkey.decode())

