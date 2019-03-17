import logging
import socket
from io import StringIO
from logging import error
from typing import Union

from ruamel.yaml import YAML

from Eranox.Agent.Actions import init_cmds
from Eranox.Agent.Connections.SSLSocket import SSLController
from Eranox.Core import process_message
from Eranox.Core.Command import CommandFactory, CommandReplyMessage
from EranoxAuth.authenticate import Authenticator

yaml = YAML(typ="safe")
import base64


def Core(args):
    def get_parameter(name, type, default=None):
        def get_from_config(permit_none_value: bool = False) -> Union[type, None]:
            if name in config:
                pval = config.get(name)
                if isinstance(pval, type):
                    return pval
                elif pval is not None or permit_none_value:
                    try:
                        return type(pval)
                    except Exception as e:
                        error(e)

        def get_from_args(permit_none_value: bool = False):
            if hasattr(args, name):
                pval = getattr(args, name)
                if isinstance(pval, type):
                    return pval
                elif pval is not None or permit_none_value:
                    try:
                        return type(pval)
                    except Exception as e:
                        error(e)

        def get_from_stdin():
            while True:
                try:
                    return type(input(f"{name}>"))
                except Exception as e:
                    error(e)

        pval = get_from_config()
        if pval is None: pval = get_from_args()
        if pval is None:
            if default is not None:
                return default
            else:
                return get_from_stdin()
        else:
            return pval

    auth = Authenticator()
    config_file = args.config_file
    config = yaml.load(open(config_file))
    server_addr = get_parameter("server_addr", str)
    port = get_parameter("port", int)
    cert_path = get_parameter("cert_path", str)
    username = get_parameter("username", str, "register")
    password = get_parameter("password", str, "register")
    server_hash = get_parameter("server_hash", str, False)
    ssl = SSLController(server_addr, port, cert_path, username, password, auth, server_hash, check_hostname=False)
    ssl.start()
    if args.install:
        if get_parameter("manual_credentials", bool, False):
            r_user = get_parameter("register_user", str)
            r_pwd = get_parameter("register_password", str)
        else:
            import os
            r_user = get_parameter("register_user", str, socket.gethostname())
            r_pwd = get_parameter("register_password", str, base64.b64encode(os.urandom(64)).decode())
        ssl.write(CommandFactory.create_command(f"REGISTER -u '{r_user}' -p '{r_pwd}'", register_phase_2,
                                                    kwargs={"ssl": ssl, "password": r_pwd, "username": r_user,
                                                            "server_addr": server_addr, "port": port,
                                                            "cert_path": cert_path,
                                                            "config_file": config_file}))

    stream = StringIO()
    logHandler = logging.StreamHandler(stream, )
    logger = logging.getLogger(f"agent")
    logger.addHandler(logHandler)
    logger.setLevel(logging.ERROR)
    parser = init_cmds(logger)
    try:
        while ssl.is_alive():
            message = ssl.get_data()
            if message is not None:
                process_message(message, parser=parser, controller=ssl, init_cmd=init_cmds)
    except TypeError as e: # thread error ...
        error(e)


def register_phase_2(username: str, password: str, server_addr: str, port: int, cert_path: str, config_file: str, ssl,
                     msg: CommandReplyMessage):
    if msg.errors:
        ssl.stop()
        raise Exception(msg.errors)
    if isinstance(msg.result, bytes):
        file = open(config_file, "w")
        yaml.dump({
            "username": username,
            "password": password,
            "server_addr": server_addr,
            "port": port,
            "cert_path": cert_path,
            "server_hash": msg.result.decode()
        }, file)
        file.close()
    ssl.stop()
