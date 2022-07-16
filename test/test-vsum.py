import sys
sys.path.insert(0, "..")

from datetime import datetime, timedelta
import random
from diffsum import diffsum_timespan_sharp

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

def make_data(nb_times, sample_span, basetime, nb_points):
    """
    nb_times: サンプル回数
    sample_span: サンプル周期
    basetime: データの開始時間
    nb_points: ポイント数
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
        for i in range(nb_times):
            # 取得した時刻、少しずらす
            dtx = dt + timedelta(microseconds=random.randint(500,999))
            tstr = dtx.isoformat(timespec="seconds")
            #tstr = dtx.isoformat()
            score = dtx.timestamp()
            #v = val.gen_inc()
            v = val.gen_one()
            xo.append((score, v, tstr))
            # 次の時刻
            dt += timedelta(seconds=sample_span)
    return data

def main(data, sumspan, margin, expected):
    """
    data: see the return value of make_data()
    """
    for pid,svt in data.items():
        for i,vl in enumerate(svt):
            print(f"{i:02d}: {vl}")

    print()
    print(f"- Integ span = {sumspan//60} ({sumspan} sec), margin={margin} sec")
    for pid,svt_list in data.items():
        vsum = diffsum_timespan_sharp(svt_list, sumspan, margin)
        print(pid, vsum)
        print()
        assert vsum == expected
        #if vsum != expected:
        #    raise ValueError(f"ERROR: {vsum} != {expected}")

def make_data_and_test(testv, expected):
    sample_span, nb_times, sumspan, margin, nb_points, basetime = testv
    print(f"- Sampl. span = {sample_span} sec, #of data = {nb_times}")
    data = make_data(nb_times, sample_span, basetime, nb_points)
    main(data, sumspan, margin, expected)

def test_even():
    testv = [
# sample_span, nb_times, sumspan, margin, nb_points
( (10,  1, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  2, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  6, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  7, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 6} ),
( (10,  8, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 6} ),
( (10, 12, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 6} ),
( (10, 13, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [6.0, 6.0], 'rest_offset': 12} ),
( (10, 14, 60, 1, 1, "2022-07-07T12:30:00.123499+09:00"), {'vsum_list': [6.0, 6.0], 'rest_offset': 12} ),
        ]
    for i in range(0,8): make_data_and_test(*testv[i])

def test_plus2sec():
    testv = [
# sample_span, nb_times, sumspan, margin, nb_points
# "2022-07-07T12:30:02.123499+09:00" needs 3 sec as margin.
( (10,  1, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  2, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  6, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  7, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 6} ),
( (10,  8, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 6} ),
( (10, 12, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 6} ),
( (10, 13, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [6.0, 6.0], 'rest_offset': 12} ),
( (10, 14, 60, 3, 1, "2022-07-07T12:30:02.123499+09:00"), {'vsum_list': [6.0, 6.0], 'rest_offset': 12} ),
        ]
    for i in range(0,8): make_data_and_test(*testv[i])

def test_minus8sec():
    testv = [
# sample_span, nb_times, sumspan, margin, nb_points
# "2022-07-07T12:29:52.123499+09:00"
( (10,  1, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  2, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  3, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  7, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [], 'rest_offset': 0} ),
( (10,  8, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 7} ),
( (10,  9, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 7} ),
( (10, 13, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [6.0], 'rest_offset': 7} ),
( (10, 14, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [6.0, 6.0], 'rest_offset': 13} ),
( (10, 15, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [6.0, 6.0], 'rest_offset': 13} ),
( (10, 16, 60, 3, 1, "2022-07-07T12:29:52.123499+09:00"), {'vsum_list': [6.0, 6.0], 'rest_offset': 13} ),
        ]
    for i in range(0,8): make_data_and_test(*testv[i])

if __name__ == "__main__":
    test_even()
    test_plus2sec()
    test_minus8sec()
