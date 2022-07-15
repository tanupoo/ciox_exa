import sys
sys.path.insert(0, sys.path[0]+"/PySLMPClient") # XXX ugly

from pyslmpclient import SLMPClient
from pyslmpclient.const import DeviceCode
from pyslmpclient.util import Target
from conf import fix_config

class SLMPAgent:

    def __init__(self, target, config):
        self.config = config
        self.target = target
        self.logger = config.logger
        self.IPAddr = target.IPAddr
        self.IPPort = target.IPPort
        self.PullInterval = target.PullInterval
        self.tag = f"Agent:{target.TargetID}: "
        #
        self.logger.info(f"{self.tag}Starting SLMP agent "
                         f"for {target.Transport} {self.IPAddr}:{self.IPPort}"
                         f"{target.PDUType} {target.Encode}")
        self.client = SLMPClient(
                addr=self.IPAddr,
                port=self.IPPort,
                binary=True if target.Encode == "binary" else False,
                ver=3 if target.PDUType == "ST" else 4,
                tcp=False if target.Transport == "UDP" else True)
        self.client.target.network = int(target.NetNo,16)
        self.client.target.node = int(target.NodeNo,16)
        self.client.target.dst_proc = int(target.DstProcNo,16)
        self.client.target.drop = 0
        # fix DevCode
        dev_code = [i for i in DeviceCode if i.name == self.target.DevCode]
        if len(dev_code) == 0:
            msg = f"{self.tag}Invalid DeviceCode, {self.target.DevCode}"
            self.logger.error(msg)
            raise ValueError(msg)
        self.target.DevCode = dev_code[0]

    def pull(self):
        self.client.open()
        result = self.client.read_word_devices(
                self.target.DevCode,
                start_num=self.target.ReadStart,
                count=self.target.ReadCount,
                timeout=self.target.Timer,
                )
        self.client.close()
        return result

def slmp_start_agent(target, config):
    fix_config(target, "PullInterval", 5)
    fix_config(target, "IPAddr", "127.0.0.1")
    fix_config(target, "IPPort", 1025)
    fix_config(target, "Transport", "TCP", ["TCP", "UDP"])
    fix_config(target, "PDUType", "ST", ["ST", "MT"])
    fix_config(target, "Encode", "binary", ["binary", "ascii"])
    fix_config(target, "NetNo", "0x00")
    fix_config(target, "NodeNo", "0xff")
    fix_config(target, "DstProcNo", "0x03ff")
    fix_config(target, "Timer", 4)
    fix_config(target, "DevCode", "D", ["D","W","R"])
    fix_config(target, "ReadStart", 1)
    fix_config(target, "ReadCount", 1)
    return SLMPAgent(target, config)
