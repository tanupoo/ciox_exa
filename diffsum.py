from datetime import datetime, timedelta

def diffsum_timespan_sharp(data, sumspan=300, margin=10):
    """
    data: [ (scire(timestamp), value, isoformat), ... ]
    sumspan: span in seconds to integrate the diff values.
    margin: margin in seconds, which allows the end of the integration.
    return: [ value1, ... ]
        if there is no enough data for the integration, the sum value sets None.
    """
    vsum = []
    ts0 = data[0][0]
    vs = 0
    good = False
    for i in range(1,len(data)):
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

