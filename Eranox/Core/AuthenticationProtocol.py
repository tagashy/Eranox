from enum import Enum


class AuthenticationProtocol(Enum):
    PASSWORD = "password"
    SHARED_KEY_PASSWORD = "shared_key"
    SHARED_KEY_BASED_CHALLENGE = "challenge"
    SHARED_KEY_BASED_CHALLENGE_DOUBLE = "slow"


DEFAULT_PROTOCOL = AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE
