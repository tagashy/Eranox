from enum import Enum


class AuthenticationProtocol(Enum):
    PASSWORD = "password"
    SHARED_KEY_PASSWORD = "shared_key"
    SHARED_KEY_BASED_CHALLENGE = "challenge"
    SHARED_KEY_BASED_CHALLENGE_DOUBLE = "slow"
    SHARED_KEY_BASED_CHALLENGE_KEEP_ENCRYPTED = "keep_encrypt"


DEFAULT_PROTOCOL = AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_KEEP_ENCRYPTED
