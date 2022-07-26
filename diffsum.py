from time_util import get_sharp_timestamp, get_time_isoformat

def diffsum_timespan_sharp(data, sumspan=300, margin=10, config=None):
    """
    data: [ (scire(timestamp), value, isoformat), ... ]
    sumspan: span in seconds to integrate the diff values.
    margin: margin in seconds, which allows the delay of sampleing timestamp.

    return: { "vsum_list": [ value1, ... ], "rest_offset": rest_data_offset }
        rest_data_offset := None: no data remained.

    XXX need to handle *None* of the sampling value.
        if there is no enough data for the integration, the sum value sets None.

    finds the start record around a sharp time from the sampling timestamps.
    the time is a little progressed time than a sharp time.
Sharp.Time      st0               st1               st2
                 |                 |                 |
Sampl.Time   t.   t0    t1    t2    t3    t4    t5    t6    t7
Value        v.   v0    v1    v2    v3    v4    v5    v6    v7
    """
    if config is not None:
        debug_print = config.logger.debug
    else:
        debug_print = print
    #
    data_size = len(data)
    result = { "vsum_list": [], "rest_offset": 0 }
    if len(data) == 0:
        return result
    for offset,svt in enumerate(data):
        (s,v,t) = svt
        diff = s - get_sharp_timestamp(sumspan, s, prev=True)
        if diff <= margin:
            debug_print(f"* {offset} {get_time_isoformat(ts=s)} {diff}")
            break
        else:
            debug_print(f". {offset} {get_time_isoformat(ts=s)} {diff}")
            pass
    # 
    if 1 + offset == data_size:
        return result
    """
    Now, we can start to integrate the diffs.
    e.g. if the set of data is [t1, t2, t3, t4, t5, t6, t7]
    as st1 is the sharp time, so the start is t3, offset is 2.
    """
    vsum_list = []
    vsum = 0
    v0 = data[offset][1]
    offset_completed = 0
    for offset in range(offset+1,data_size):
        (s,v,t) = data[offset]
        diff = s - get_sharp_timestamp(sumspan, s, prev=True)
        if diff <= margin:
            debug_print(f"Z {offset} {get_time_isoformat(ts=s)} {diff}")
            vsum += (float(v) - float(v0))
            vsum_list.append(vsum)
            vsum = 0
            offset_completed = offset
        else:
            debug_print(f"* {offset} {get_time_isoformat(ts=s)} {diff}")
            vsum += (float(v) - float(v0))
        v0 = v
    result["vsum_list"] = vsum_list
    result["rest_offset"] = offset_completed
    return result

