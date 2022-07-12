from datetime import datetime, timedelta
import dateutil.tz

#tz_info = dateutil.tz.gettz("America/Los_Angeles")
tz_info = dateutil.tz.gettz("Asia/Tokyo")

def get_time_isoformat(dt=None, ts=None):
    """
    return isoformat **WITHOUT** microseconds.
    """
    if dt is not None:
        return dt.isoformat(timespec="seconds")
    elif ts is not None:
        return datetime.fromtimestamp(ts, tz=tz_info).isoformat(
                timespec="seconds")
    else:
        return get_time_now().isoformat(timespec="seconds")

def get_time_now(margin=0):
    """
    return datetime
    """
    now = datetime.now(tz=tz_info)
    if margin != 0:
        return now + timedelta(seconds=margin)
    else:
        return now

def get_next_sharp_time(xi, ts0=None):
    """
    xi: interval. e.g. 30 means to calculate seconds to next 30 seconds.
    ts0: base timestamp.
    NOTE: timestamp must be aware-time.
    """
    if ts0 is None:
        ts0 = get_time_now().timestamp()
    return datetime.fromtimestamp((ts0+xi)//xi*xi, tz=tz_info)

def get_sleep_time(xi):
    """
    xi: interval. e.g. 30 means to calculate seconds to next 30 seconds.
    """
    n = get_time_now()
    t = get_next_sharp_time(xi)
    return t.timestamp() - n.timestamp()

if __name__ == "__main__":
    import time
    import dateutil.parser
    x = get_next_sharp_time(3600)   # next 1 hour
    print(x.isoformat())
    a = datetime.fromtimestamp(time.time(), tz=tz_info)
    c = datetime.now(tz_info)
    b = datetime.now()
    print(a.isoformat())
    print(c.isoformat())
    print(b.isoformat())
    #
    dt = dateutil.parser.parse("2022-07-09T22:21:00.083802+09:00")
    print(" ts0:", dt.isoformat())
    print("next:", get_next_sharp_time(3600, dt.timestamp()).isoformat())
