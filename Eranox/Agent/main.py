import json
from logging import debug, error

from ruamel.yaml import YAML
from EranoxAuth.authenticate import Authenticator
from Eranox.Agent.Actions import init_cmds
from Eranox.Agent.Connections.SSLSocket import SSLController
from Eranox.Core.Command import CommandMessage
from Eranox.Core.Command import CommandReplyMessage, CommandFactory
from Eranox.Core.Message import Message
from Eranox.constants import StatusCode
from Eranox.Core import process_message
from io import StringIO
import logging
yaml = YAML(typ="safe")


def Core(args):
    auth=Authenticator()
    config_file = args.config_file
    data = yaml.load(open(config_file))
    password = data.get("password")
    username = data.get("username")
    server_hash = data.get("server_hash")
    cert_path = data.get("cert_path")
    server_addr = data.get("server_addr", '127.0.0.1')
    port = data.get("port", 8443)
    ssl = SSLController(server_addr, port, cert_path, username, password,auth, server_hash, check_hostname=False)
    ssl.start()
    stream = StringIO()
    logHandler = logging.StreamHandler(stream, )
    logger = logging.getLogger(f"agent")
    logger.addHandler(logHandler)
    logger.setLevel(logging.ERROR)
    parser = init_cmds(logger)
    while True:
        message = ssl.get_data()
        if message is not None:
            process_message(message, parser=parser, controller=ssl,init_cmd=init_cmds)





if __name__ == '__main__':
    from logging import DEBUG, basicConfig

    basicConfig(level=DEBUG)
