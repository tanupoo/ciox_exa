from pydantic import BaseModel, Extra
from typing import List, Optional, Union, Dict

class PointDataWithTS(BaseModel):
    PointID: str
    Values: List[Union[float, None]]
    TSLastValue: str

    # XXX None: 欠損値 を "" にする処理
    # validation

class HintInfo(BaseModel):
    System: str

class ServerPostModel(BaseModel):
    Version: int = 0
    Data: List[PointDataWithTS]
    Hint: Optional[HintInfo]

if __name__ == "__main__":

    data = {
        "Version": "0",
        "Data": [
            {
                "PointID": "P0005215",
                "TSLastValue": "2022-06-28T00:00:00+09:00",
                "Values":  [
                "0.01", "0.02", "0.03", "0.04", "0.05", "0.06", "0.07", "0.08",
                "0.09", "0.1", "0.11", "0.12", "0.13", "0.14", "0.15", "0.16",
                "0.17", "0.18", "0.19", "0.2", "0.21", "0.22", "0.23", "0.24",
                "0.25", "0.26", "0.27", "0.28", "0.29", "0.3", "0.31", "0.32",
                "0.33", "0.34", "0.35", "0.36", "0.37", "0.38", "0.39", "0.4",
                "0.41", "0.42", "0.43", "0.44", "0.45", "0.46", "0.47", "0.48"
                ],
            }
        ],
        "Hint": {
            "System": "MELSCパターン2"
        },
    }

    print(ServerPostModel.parse_obj(data))

    data = [{'PointID': 'P0005215', 'Values': [None],
             'TSLastValue': '2022-07-12T14:29:55+09:00'},
            {'PointID': 'P0005216', 'Values': [None],
             'TSLastValue': '2022-07-12T14:29:55+09:00'},
            {'PointID': '06_78_90:XA', 'Values': [None],
             'TSLastValue': '2022-07-12T14:29:55+09:00'},
            {'PointID': '06_78_91:XB', 'Values': [None],
             'TSLastValue': '2022-07-12T14:29:55+09:00'}]
    print(ServerPostModel(Data=data))
