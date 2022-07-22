import sys
sys.path.insert(0, "..")

import logging
from db_man import DBConnector

import logging
from time_util import get_time_now

from datetime import datetime
import dateutil.parser
import dateutil.tz

tz_info = dateutil.tz.gettz("Asia/Tokyo")

def setup_db():
    logging.basicConfig(level=logging.DEBUG)
    config = type("config",(),{})
    config.logger = logging.getLogger("test")

    db_info = type("db_info",(),{})
    db_info.IPAddr = "127.0.0.1"
    db_info.IPPort = 6379
    db = DBConnector(db_info, config)
    if db.ping() is False:
        return False
    return db

def clear_db(db):
    for i in db.conn.scan_iter(): db.conn.delete(i)

#
# XXX
# try to use pytest_configure, pytest_unconfigure
#

def test_post_data_raw_basic():
    data = [("MONO-215", -1), ("ROT-P216", 30), ("温度", 20), ("稼働中", True) ]
    db = setup_db()
    assert db is not False
    clear_db(db)
    ret = db.post_data_raw(data)
    assert ret == 4

def test_post_data_raw_content():
    data = [("MONO-215", -1)]
    db = setup_db()
    clear_db(db)
    ret = db.post_data_raw(data)
    assert ret == 1
    ret = db.get_data_raw([d[0] for d in data], get_time_now().timestamp())
    # {'MONO-215': [(1658460726.760426, '-1', '2022-07-22T12:32:06+09:00')]}
    for pid,orig_val in data:
        body = ret.get(pid)
        assert body is not None
        print(body)
        for score,val,ts in body:
            assert str(orig_val) == val
            dt1 = datetime.fromtimestamp(score, tz=tz_info).isoformat(timespec="seconds")
            assert dt1 == ts

def test_post_data_raw_None():
    data = [(None, -1)]
    db = setup_db()
    assert db.post_data_raw(data) == False
    #
    # XXX need redis.close()???
    #db.close()

def test_get_data_raw():
    data = [("MONO-215", -1), ("ROT-P216", 30), ("温度", 20), ("稼働中", True) ]
    db = setup_db()
    if db.post_data_raw(data):
        ret = db.get_data_raw([p[0] for p in data],
                               get_time_now().timestamp())
        assert len(ret) == 4
    else:
        assert False

def test_get_data_raw_None():
    db = setup_db()
    ret = db.get_data_raw(None, get_time_now().timestamp())
    assert ret == False

def test_get_data_Nothing():
    db = setup_db()
    ret = db.get_data_raw([], get_time_now().timestamp())
    assert ret == {}

def test_del_data_raw():
    data = [("MONO-215", -1), ("ROT-P216", 30), ("温度", 20), ("稼働中", True) ]
    db = setup_db()
    if db.post_data_raw(data):
        ret = db.del_data_raw([p[0] for p in data],
                            get_time_now().timestamp())
        assert ret == 4
    else:
        False

def test_del_data_raw_False():
    db = setup_db()
    ret = db.del_data_raw("NO-DATA", get_time_now().timestamp())
    assert ret == False


#
# rdy
#
def test_post_data_ready():
    data = [("SERVER1", {"xxx": 1}), ("サーバーX", {"xxx": 2})]
    db = setup_db()
    for p,d in data:
        ret = db.post_data_ready(p, d)
        # return index
        assert ret > 0

def test_get_data_ready_None():
    db = setup_db()
    ret = db.get_data_ready(None)
    assert len(ret) == 0

def test_get_data_ready_Nothing():
    db = setup_db()
    ret = db.get_data_ready("NO-DATA")
    assert len(ret) == 0

def test_get_data_ready():
    data = [("SERVER1", {"xxx": 1}), ("サーバーX", {"xxx": 2})]
    db = setup_db()
    for p,d in data:
        ret = db.get_data_ready(p)
        assert len(ret) == 1

#
# retx
#
def test_post_data_retx():
    data = [("SERVER1", {"xxx": 1}), ("サーバーX", {"xxx": 2})]
    db = setup_db()
    for p,d in data:
        ret = db.post_data_retx(p, d)
        # return index
        assert ret > 0

def test_get_data_retx():
    data = [("SERVER1", {"xxx": 1}), ("サーバーX", {"xxx": 2})]
    db = setup_db()
    for p,d in data:
        ret = db.get_data_retx(p)
        assert len(ret) == 1

