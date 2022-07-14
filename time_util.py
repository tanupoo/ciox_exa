from datetime import datetime, timedelta
import dateutil.tz

#tz_info = dateutil.tz.gettz("America/Los_Angeles")
tz_info = dateutil.tz.gettz("Asia/Tokyo")

def get_time_isoformat(dt=None, ts=None):
    """
    either dt or ts is required.
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

def get_sharp_timestamp(xi, ts0=None, prev=True):
    """
    xi: integration span.
    ts0: base timestamp.
    prev:
        False: return timestamp of the next shart time.
        True: return timestamp of the previous shart time.
    e.g. (xi, prev) = (30, False), returns the latest of 30 seconds.
    """
    if ts0 is None:
        ts0 = get_time_now().timestamp()
    if prev is True:
        return ts0//xi*xi
    else:
        return (ts0+xi)//xi*xi

def get_prev_sharp_time(xi, ts0=None):
    """
    xi: interval. e.g. 30 means to calculate seconds to previous 30 seconds.
    ts0: base timestamp.
    NOTE: timestamp must be aware-time.
    """
    return datetime.fromtimestamp(get_sharp_timestamp(xi, ts0, prev=True),
                                  tz=tz_info)

def get_next_sharp_time(xi, ts0=None):
    """
    xi: interval. e.g. 30 means to calculate seconds to next 30 seconds.
    ts0: base timestamp.
    NOTE: timestamp must be aware-time.
    """
    return datetime.fromtimestamp(get_sharp_timestamp(xi, ts0, prev=False),
                                  tz=tz_info)

def get_sleep_time(xi, margin=0):
    """
    xi: interval. e.g. 30 means to calculate seconds to next 30 seconds.
    """
    n = get_time_now()
    t = get_next_sharp_time(xi)
    return t.timestamp() - n.timestamp() + margin

if __name__ == "__main__":
    import time
    import dateutil.parser
    print("current:", get_time_isoformat())
    print("   prev:", get_prev_sharp_time(3600).isoformat())
    print("   next:", get_next_sharp_time(3600).isoformat())
    testv = [
            # span, isots
            (60, "2022-07-07 12:31:02.000826"),
            ]
    for t in testv:
        span = t[0]
        dt = dateutil.parser.parse(t[1])
        print(testv, "==>",
              datetime.fromtimestamp(get_sharp_timestamp(span, dt.timestamp(),
                                                         prev=True)))
