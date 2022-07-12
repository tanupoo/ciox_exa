from pydantic import BaseModel, Extra
from typing import List, Optional, Union, Dict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os import environ
from get_logger import get_logger
import json
from model_config import *

__env_vars = {
    "agent_man": {
        "common_config_file": "IOX_EXA_COMMON_CONFIG_FILE",
        "config_file": "IOX_EXA_AM_CONFIG_FILE",
        "enable_debug": "IOX_EXA_AM_ENABLE_DEBUG",
        "log_file": "IOX_EXA_AM_LOG_FILE",
        "log_stdout": "IOX_EXA_AM_LOG_STDOUT",
    },
    "middle_man": {
        "common_config_file": "IOX_EXA_COMMON_CONFIG_FILE",
        "config_file": "IOX_EXA_MM_CONFIG_FILE",
        "enable_debug": "IOX_EXA_MM_ENABLE_DEBUG",
        "log_file": "IOX_EXA_MM_LOG_FILE",
        "log_stdout": "IOX_EXA_MM_LOG_STDOUT",
    },
    "post_man": {
        "common_config_file": "IOX_EXA_COMMON_CONFIG_FILE",
        "config_file": "IOX_EXA_PM_CONFIG_FILE",
        "enable_debug": "IOX_EXA_PM_NABLE_DEBUG",
        "log_file": "IOX_EXA_PM_LOG_FILE",
        "log_stdout": "IOX_EXA_PM_LOG_STDOUT",
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
            description="IOX EnergyX {prog_name}.",
            formatter_class=ArgumentDefaultsHelpFormatter)
    ap.add_argument("config_file", metavar="CONFIG_FILE",
                    help="specify the config file.")
    ap.add_argument("-d", action="store_true", dest="enable_debug",
                default=None,
                help="enable debug mode.")
    ap.add_argument("-l", action="store", dest="log_file",
                help="specify the name of the log file.")
    opt = ap.parse_args(args)
    # set arguments to the env variable to orverwrite the ones.
    for k,v in [("config_file", opt.config_file),
                ("enable_debug", opt.enable_debug),
                ("log_file", opt.log_file)]:
        if v is not None:
            environ[__env_vars[prog_name][k]] = str(v)

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
    if args is not None:
        __parse_args(prog_name, args)
    env_vars = __env_vars[prog_name]
    # load the program config.
    config_file = environ[env_vars["config_file"]]
    try:
        config0 = ProgramConfigModel.parse_obj(json.load(open(config_file)))
    except Exception as e:
        print("ERROR: {} read error. {}".format(config_file, e))
        exit(1)
    # overwrite the config by the cli options/env variable.
    for k,v in [("enable_debug", "EnableDebug"),
                ("log_file", "LogFile")]:
        if environ.get(env_vars[k]) is not None:
            setattr(config0, v, environ.get(env_vars[k]))
    # load the common config.
    try:
        config = CommonConfigModel.parse_obj(json.load(open(
                config0.CommonConfigFile)))
    except Exception as e:
        print("ERROR: {} read error. {}".format(config0.CommonConfigFile, e))
        exit(1)
    # set logger
    config.logger = get_logger(prog_name,
                               log_file=config0.LogFile,
                               debug_mode=config0.EnableDebug)
    return config

if __name__ == "__main__":
    import sys
    conf = json.load(open(sys.argv[1]))
    m = ConfigModel.parse_obj(conf)
    print(m)
