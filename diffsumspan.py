from datetime import datetime, timedelta

def diffsumspan(data, sumspan=300, margin=10, offset=0):
    """
    data: [ (scire(timestamp), value, isoformat), ... ]
    sumspan: span in seconds to integrate the diff values.
    margin: margin in seconds, which allows the end of the integration.
        sumspan丁度にタイムスタンプが収まらないので余裕をもたせる。
    offset: the offset of the list in data to start the integration.
    return: [ value1, ... ]
        if there is no enough data for the integration, the sum value sets None.
    """
    vsum = []
    ts0 = data[offset][0]
    vs = 0
    good = False
    for i in range(offset+1,len(data)):
        di = data[i]
        print("delta:", data[i][0] - ts0)
        if data[i][0] - ts0 < sumspan + margin:
            print("S", data[i][2], datetime.fromtimestamp(data[i][0]))
            vs += (float(data[i][1]) - float(data[i-1][1]))
            good = False
        else:
            print("Z", data[i][2], datetime.fromtimestamp(data[i][0]))
            vsum.append(vs)
            ts0 = data[i-1][0]
            vs = (float(data[i][1]) - float(data[i-1][1]))
            good = True
    if not good:
        vsum.append(None)
    return vsum

