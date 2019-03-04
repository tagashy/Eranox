from enum import Enum


class StatusCode(Enum):
    COMMAND = 100
    COMMAND_REPLY = 200
    AUTHENTICATION_ERROR = 90
    AUTHENTICATION_SUCCESS = 1
    AUTHENTICATION_CHALLENGE_STEP_2 = 2


STATUS_CODE = "status_code"
MESSAGE = "message"
ERRORS = "errors"
VERSION = "0.0.1"
SECURE_STORAGE_MASTERTABLE_PATH = ".mastertable.yml"
SERVER_ACTION = "server"
CLI_ACTION = "cli"
AGENT_ACTION = "agent"
LOGIN = "LOGIN"
