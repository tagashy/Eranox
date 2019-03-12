from enum import Enum


class AuthenticationProtocol(Enum):
    PASSWORD = "password" # Fastest no server validation, vulnerable to MIT and replay attack if tls is broken
    SHARED_KEY_PASSWORD = "shared_key" # vulnerable to MIT and replay attack if tls is broken but server validation is done through a shared key
    SHARED_KEY_BASED_CHALLENGE = "challenge" # vulnerable to MIT after authentication but credentials won't be in danger
    SHARED_KEY_BASED_CHALLENGE_DOUBLE = "double" # same as above but slower as the password is encrypted
    SHARED_KEY_BASED_CHALLENGE_KEEP_ENCRYPTED = "keep_encrypt" # challenge based authentication with negociation of shared key for encrypting the traffic after authentication A.K.A you need to break TLS + AES encrypted communication based on preshared key GLHF


DEFAULT_PROTOCOL = AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_KEEP_ENCRYPTED
