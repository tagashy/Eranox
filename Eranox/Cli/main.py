from ruamel.yaml import YAML

from Eranox.Cli.STDINClient import STDINClient

yaml = YAML(typ="safe")
from EranoxAuth.authenticate import Authenticator
from Eranox.Agent.Actions import init_cmds
from Eranox.Core import process_message
from io import StringIO
import logging

def get_param_value(args, config, name, default=None):
    if hasattr(args, name):
        res = getattr(args, name)
        if res is not None:
            return res
    if name in config:
        res = config.get(name)
        if res is not None:
            return res
    if default is None:
        return input(f"{name}>")
    else:
        return default


def Core(args):
    config_file = args.config_file
    data = yaml.load(open(config_file))
    password = get_param_value(args, data, "password")
    username = get_param_value(args, data, "username")
    server_hash = get_param_value(args, data, "server_hash")
    cert_path = get_param_value(args, data, "cert_path")
    server_addr = get_param_value(args, data, "server_addr", '127.0.0.1')
    check_hostname = get_param_value(args, data, "check_hostname", False)
    port = get_param_value(args, data, "port", 8443)
    auth = Authenticator()
    stream = StringIO()
    logHandler = logging.StreamHandler(stream, )
    logger = logging.getLogger(f"agent")
    logger.addHandler(logHandler)
    logger.setLevel(logging.ERROR)
    parser = init_cmds(logger)
    stdin = STDINClient(server_addr, port, cert_path, username, password, auth, server_hash, check_hostname)
    stdin.start()
    while True:
        message = stdin.ssl.get_data()
        if message is not None:
            process_message(message, stdin.ssl, parser=parser, init_cmds=init_cmds)
