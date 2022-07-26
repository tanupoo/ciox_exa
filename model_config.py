from pydantic import BaseModel, Extra, validator
from typing import List, Optional, Union, Dict, Literal

class PointInfo(BaseModel):
    SiteName: str
    Location: str
    DeviceName: str
    ValueName: str
    Unit: str
    ValueType: Literal["float", "int"] = "float"
    ULimitRotationNumber: Optional[int]
    ProcessType: Optional[Literal["S", "I"]]
    IntegrationSpan: int = 1800

class AuthCredBasic(BaseModel):
    Username: str
    Password: str

class AuthCredCert(BaseModel):
    CertFile: str
    KeyFile: str
    RootChainFile: str

class ServerAuthCertInfo(BaseModel):
    CertRootChainFile: str

class ClientAuthTypeInfo(BaseModel):
    AuthType: Literal["None", "Basic", "Cert"] = "None"
    AuthInfo: Optional[Union[AuthCredBasic,AuthCredCert]]

    @validator("AuthInfo")
    def validate_AuthInfo(cls, v, values):
        auth_type = values["AuthType"]
        if (auth_type== "None" or
            (auth_type == "Basic" and type(v).__name__ == "AuthCredBasic") or
            (auth_type == "Cert" and type(v).__name__ == "AuthCredCert")):
            return v
        else:
            raise ValueError(f"ERROR: invalid AuthInfo: {v} as {auth_type}")

class ServerInfo(BaseModel):
    ServerID: str
    EPR: str
    Version: str
    ServerAuthInfo: Union[None,Dict,ServerAuthCertInfo]
    ClientAuthInfo: Union[None,Dict,ClientAuthTypeInfo]
    PostTimeBase: str = "00:00:00"
    PostInterval: int = 21600
    IntegrationDeferTime: int = 600
    IntegrationMarginTime: int = 30
    Timeout: int = 15
    Compression: bool = False
    Points: List[str]

class PointMapInfo(BaseModel):
    PointID: str
    DeviceCode: str
    Position: int

class TargetInfo(BaseModel):
    TargetID: str
    Points: List[PointMapInfo]
    Protocol: str
    PullInterval: int
    RetryInterval: int
    RetryCount: int
    IPAddr: str
    IPPort: int
    Transport: str
    PDUType: str
    Encode: str
    NetNo: str
    NodeNo: str
    DstProcNo: str
    Timer: int
    Command: str
    SubCommand: str
    DevCode: str
    ReadStart: int
    ReadCount: int

class DBInfo(BaseModel):
    IPAddr: Optional[str] = "localhost"
    IPPort: Optional[int] = 6379

class CommonConfigModel(BaseModel):
    Constants: Optional[Dict[str, str]]
    Points: Dict[str, PointInfo]
    Servers: List[ServerInfo]
    Targets: List[TargetInfo]
    AgentDB: DBInfo = DBInfo()
    QueDB: DBInfo = DBInfo()
    EnableDebug: bool = False
    LogFile: str = "syslog"
    SyslogAddr: str = "localhost"
    SyslogPort: int = 514

    class Config:
        extra = Extra.allow

