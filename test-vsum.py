from datetime import datetime, timedelta
import random
from diffsumspan import diffsumspan

class Value():
    def __init__(self, init_val=0):
        self.val = init_val
        self.num = 1
    def gen_one(self):
        self.val += 1
        return self.val
    def gen_inc(self):
        self.val += self.num
        self.num += 1
        return self.val
    def gen_rand(self):
        self.val += random.random()*10
        return self.val

def make_data(nb_times=10,
              sample_interval=60,
              nb_points=1,
              basetime="2022-07-07T12:00:00+09:00"
              ):
    """
    nb_times: サンプル回数
    sample_interval: サンプル周期
    return:
    {
        <PointID>: [
            # Score, Value, TS
            (1657162800.012281, 1, '2022-07-07T12:00:00+09:00')
            ...
        ], ....
    }
    """
    # make points
    points = []
    for i in range(nb_points):
        points.append(f"P{i+1:06d}")
    dt = datetime.fromisoformat(basetime)
    data = {}
    for pid in points:
        xo = data.setdefault(pid, [])
        val = Value()
        for i in range(nb_times+1):
            # 取得した時刻、少しずらす
            dtx = dt + timedelta(microseconds=random.randint(500,999))
            tstr = dtx.isoformat(timespec="seconds")
            #tstr = dtx.isoformat()
            score = dtx.timestamp()
            #v = val.gen_inc()
            v = val.gen_one()
            xo.append((score, v, tstr))
            # 次の時刻
            dt += timedelta(seconds=span)
    return data

def test(sample_interval, nb_times, sumspan, nb_points,
         basetime="2022-07-07T12:00:00+09:00"):
    print(f"## {sample_interval}秒間隔で{nb_times}個収集する。")
    data = make_data(nb_times=nb_times,
                     sample_interval=sample_interval,
                     nb_points=nb_points,
                     basetime=basetime)
    test(data, sumspan)

def test0(data, sumspan, margin=0):
    """
    {'P0005215': [
            # Score, Value, TS
            (1657162800.012281, 1, '2022-07-07T12:00:00+09:00')
            , ...
            ],
        ...
    """
    for pid,svt in data.items():
        for i,vl in enumerate(svt):
            print(f"{i:02d}: {vl}")

    print(f"## {sumspan//60}分値({sumspan}秒)を算出する。")
    for pid,svt in data.items():
        vsum = diffsumspan(svt, sumspan=sumspan, margin=margin)
        print(vsum)

#
# test
#
testv = [
    # sample_interval, nb_times, sumspan, nb_points
    (10, 11, 60, 1),
    (10, 13, 60, 1),
    (30, 11, 300, 1),
    (60, 11, 300, 1)
    ]
for v in testv:
    test(*v)

test(60, 11, 300, 1, "2022-07-07T12:00:00.999900+09:00")
