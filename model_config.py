from pydantic import BaseModel, Extra
from typing import List, Optional, Union, Dict, Literal

class PointInfo(BaseModel):
    SiteName: str
    Location: str
    DeviceName: str
    ValueName: str
    Unit: str
    ValueType: Literal["float", "int"] = "float"
    ULimitRotationNumber: int = 100
    Integration: bool = True
    IntegrationSpan: int = 1800

class ServerAuthCertInfo(BaseModel):
    CertRootChainFile: Optional[str]

class AuthCredBasic(BaseModel):
    UserName: str
    Password: str

class AuthCredCert(BaseModel):
    CertFile: Optional[str]
    KeyFile: Optional[str]
    RootChainFile: Optional[str]

class ClientAuthTypeInfo(BaseModel):
    AuthType: Optional[str]
    AuthInfo: Union[None,AuthCredBasic,AuthCredCert]

class ServerInfo(BaseModel):
    ServerID: str
    EPR: str
    Version: str
    ServerAuthInfo: Optional[ServerAuthCertInfo]
    ClientAuthInfo: Optional[ClientAuthTypeInfo]
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
    AgentDB: Optional[DBInfo] = DBInfo()
    QueDB: Optional[DBInfo] = DBInfo()

    class Config:
        extra = Extra.allow

class ProgramConfigModel(BaseModel):
    """
    Entry Model
    """
    CommonConfigFile: Optional[str] = "common-config.json"
    EnableDebug: Optional[bool] = False
    LogFile: Optional[str] = "daemon.log"

