from pydantic import BaseModel, Extra
from typing import List, Optional, Union, Dict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os import environ
from get_logger import get_logger
import json
from model_config import *

__env_vars = {
    "agent_man": {
        "ConfigFile": "IOX_EXA_CONFIG_FILE",
        "EnableDebug": "IOX_EXA_AM_ENABLE_DEBUG",
        "LogFile": "IOX_EXA_AM_LOG_FILE",
    },
    "middle_man": {
        "ConfigFile": "IOX_EXA_CONFIG_FILE",
        "EnableDebug": "IOX_EXA_MM_ENABLE_DEBUG",
        "LogFile": "IOX_EXA_MM_LOG_FILE",
    },
    "post_man": {
        "ConfigFile": "IOX_EXA_CONFIG_FILE",
        "EnableDebug": "IOX_EXA_PM_NABLE_DEBUG",
        "LogFile": "IOX_EXA_PM_LOG_FILE",
    },
}

def fix_config(cf0, k0, v0, values=[]):
    """
    cf0: config.
    k0: key in config.
    v0: default value of key if not existed.
    values: list of valid values
    """
    v = cf0.dict().get(k0)
    if v is None:
        cf0.update({k0: v0})
        v = v0
    elif type(v) != type(v0):
        raise ValueError(f"type error as {k0} {type(v0)}: {v}")
    if len(values) > 0 and v not in values:
        raise ValueError(f"invalid value {v}.  must be either {values}")

def __parse_args(prog_name, args):
    """
    take arguments and overwrite ones if specified.
    """
    ap = ArgumentParser(
            description="IOx {prog_name}.",
            formatter_class=ArgumentDefaultsHelpFormatter)
    ap.add_argument("-c", action="store", dest="config_file",
                    help="specify the config file.")
    ap.add_argument("-d", action="store_true", dest="enable_debug",
                default=None,
                help="enable debug mode.")
    ap.add_argument("-l", action="store", dest="log_file",
                help="specify the name of the log file.")
    opt = ap.parse_args(args)
    return opt

def __get_env_bool(key, default):
    c = environ.get(key)
    if c is None:
        return default
    elif c.upper() in [ "TRUE", "1" ]:
        return True
    elif c.upper() in [ "FALSE", "0" ]:
        return False
    else:
        raise ValueError(f"ERROR: {key} must be bool, but {c}")

def parse_config(prog_name, args=None):
    """
    priority order
        1. cli arguments.
        2. environment variable.
        3. config file.
        4. pydantic
    """
    env_vars = __env_vars[prog_name]
    cli_opt  = __parse_args(prog_name, args)
    if cli_opt.config_file is not None:
        config_file = cli_opt.config_file
    else:
        config_file = environ.get(env_vars["ConfigFile"])
    if config_file is None:
        print("ERROR: config file is not specified.")
        exit(1)
    # load the program config.
    try:
        config = CommonConfigModel.parse_obj(json.load(open(config_file)))
    except Exception as e:
        print("ERROR: {} read error. {}".format(config_file, e))
        exit(1)
    # overwrite the params with the order.
    for k,v in [("EnableDebug", cli_opt.enable_debug),
                ("LogFile", cli_opt.log_file)]:
        if v is not None:
            setattr(config, k, v)
        elif environ.get(env_vars[k]) is not None:
            setattr(config, k, environ.get(env_vars[k]))
    # set logger
    config.logger = get_logger(prog_name,
                               log_file=config.LogFile,
                               debug_mode=config.EnableDebug,
                               syslog=(config.SyslogAddr, config.SyslogPort))

    return config

if __name__ == "__main__":
    import sys
    conf = json.load(open(sys.argv[1]))
    m = ConfigModel.parse_obj(conf)
    print(m)
