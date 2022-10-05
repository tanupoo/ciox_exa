ciox_exa
========

- エッジ側はSLMPのみ対応。
- 他プロトコルに対応するには*agent_man.py*と*agent_slmp.py*を参考にする。

## 単体でのインストール方法

```
git clone --recursive https://github.com/tanupoo/ciox_exa
pip install -r reqs.txt
```

## 単体での起動方法

- PLC/シーケンサを用意する。
    + 用意できない場合はエミュレータなど(後述)を使う。
- HTTPサーバを用意する。
- 必要であればsyslogサーバを用意する。
- config.jsonを書く。
    + 後述の設定とsample-config.jsonを参考にする。
- 端末を5つ起動する。
- それぞれの端末で下記を実行する。

```
docker run --name redis-agent -p 6379:6379 --rm redis:7.0.2-bullseye
docker run --name redis-queue -p 6378:6379 --rm redis:7.0.2-bullseye
python agent_man.py -c config.json -l - -d
python mid_man.py -c config.json -l - -d
python post_man.py -c config.json -l - -d
```

## 超簡易SLMPエミュレータ

```
git clone http://github.com/tanupoo/simple_slmp_server
cd simple_slmp_server
python slmp_server.py
```

デフォルトだと127.0.0.1のUDPポート番号1025で待ち構える。

```
% python slmp_server.py
listening on UDP 127.0.0.1:1025
3E BINARY
```

ListenするIPアドレスを指定するには*-s*オプションを使う。

```
usage: slmp_server.py [-h] [-t] [-4] [-a] [-s SERVER_ADDR] [-p SERVER_PORT]
                      [-F {c1,r10,r100,rand,inc}]

optional arguments:
  -h, --help            show this help message and exit
  -t                    enable tcp mode.
  -4                    enable 4E mode.
  -a                    enable 4E mode.
  -s SERVER_ADDR        specify the server address.
  -p SERVER_PORT        specify the server address.
  -F {c1,r10,r100,rand,inc}
                        enable 4E mode.
```

## 取得するデータの設定

- 積算する場合はIntegrationSpanを秒で設定する。
    + 例. 30秒間隔で積算する。
        * `"IntegrationSpan": 30`
- 上限値がある場合はULimitRotationNumberに設定する。
    + 値はULimitRotationNumber未満でなければならない。

```
    "Points": {
        "P0005215": {
            "SiteName": "朝霞第3工場",
            "Location": "第1ラインエリアC",
            "DeviceName": "プレス機A",
            "ValueName": "使用電力15分積算値",
            "Unit": "kWh",
            "IntegrationSpan": 30,
            "ULimitRotationNumber": 100
        },
        "P0005216": {
            "SiteName": "朝霞第3工場",
            "Location": "第1ラインエリアB",
            "DeviceName": "ロボットアームX",
            "ValueName": "使用電力15分積算値",
            "Unit": "kWh",
            "IntegrationSpan": 30,
            "ULimitRotationNumber": 100
        },
        "P0005217": {
            "SiteName": "朝霞第3工場",
            "Location": "第1ラインエリアB",
            "DeviceName": "ロボットアームX",
            "ValueName": "温度",
            "Unit": "℃"
        }
```

## センサーの設定

- 元データを保持しているセンサーやサーバに関する設定。
- 読み込み間隔をPullIntervalに秒で設定する。
- ReadStartからReadCountだけブロックで読む。
- PointsのPositionの最大値とReadCountが等しいか大きくなければならない。
- 読んだ時刻と共に値をPointIDに割り当てる。

```
    "Targets": [
        {
            "TargetID": "R120CPU-00123",
            "Points": [
                { "PointID": "P0005215", "DeviceCode": "D", "Position": 1 }, 
                { "PointID": "P0005216", "DeviceCode": "D", "Position": 5 },
                { "PointID": "P0005217", "DeviceCode": "D", "Position": 10 }
            ],
            "Protocol": "SLMP",
            "PullInterval": 5,
            "RetryInterval": 1,
            "RetryCount": 2,
            "IPAddr": "127.0.0.1",
            "IPPort": 1025,
            "Transport":  "UDP",
            "PDUType": "ST",
            "Encode": "binary",
            "NetNo": "0x00",
            "NodeNo": "0xff",
            "DstProcNo": "0x3fff",
            "Timer": 4,
            "Command": "0401",
            "SubCommand": "0000",
            "DevCode": "D",
            "ReadStart": 1,
            "ReadCount": 10
        }
    ],
```

## クラウドサーバの設定

- POSTするHTTPサーバに関する設定。
- ポストするPointIDをPointsに設定する。
    + 1つのPointIDは1つのサーバにだけポストすることができる。
    + 第３工場エリアC温度、工作機Z消費電力、など個々の監視対象に対する識別子
        * システム全体で一意になる。
    + PointIDからシーケンサやサーバなどの収集している機器が一意に決まる。
- ポストする間隔をPostIntervalに秒で設定する。
- また、PostIntervalで指定した間隔で中間処理が動作する。
- 積算する間隔を固定すると通信時間や処理時間がかかり定時に収集できていない場合がある。積算に含める時刻のマージンをIntegrationMarginTimeに秒で設定する。
- 定時に積算を始めると最後の値が取れていない可能性がある。積算の開始時刻を少しだけずらす場合にIntegrationDeferTimeにずらす時間を秒で設定する。

```
    "Servers": [
        {
            "ServerID": "TEST-A",
            "EPR": "https://server.example.com/",
            "Version": "0",
            "ServerAuthInfo": {
                "CertRootChainFile": "/var/db/cert/cert.pem"
            },
            "ClientAuthInfo": {
                "AuthType": "Basic",
                "AuthInfo": {
                    "Username": "admin",
                    "Password": "hogehoge"
                }
            },
            "IntegrationDeferTime": 10,
            "IntegrationMarginTime": 2,
            "PostInterval": 60,
            "Timeout": 15,
            "Points": [
                "P0005215"
            ]
        },
        {
            "ServerID": "LOCAL",
            "EPR": "http://127.0.0.1:8000/post",
            "Version": "0",
            "IntegrationDelayTime": 10,
            "IntegrationMarginTime": 2,
            "PostInterval": 60,
            "Timeout": 15,
            "Points": [
                "P0005216",
                "P0005217"
            ]
        }
    ],
```

## ログの送信先の設定

```
    "SyslogAddr": "127.0.0.1",
    "SyslogPort": 8514
```

## DB管理コマンド

```
% ./dbm.py -h
usage: dbm.py [-h] [-n {all,pt,rdy,retx}] [--delete] [-a IP_ADDR] [-p IP_PORT]

redis viewer

optional arguments:
  -h, --help            show this help message and exit
  -n {all,pt,rdy,retx}  specify a category name.
  --delete              delete entries in the specified category
  -a IP_ADDR            specify the ip address of the redis server.
  -p IP_PORT            specify the port number of the redis server.
```
