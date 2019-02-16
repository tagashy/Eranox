from yosai.core import Yosai, UsernamePasswordToken

from Eranox.Server.Authentication.Authenticator import Authenticator


class YosaiAuthenticator(Authenticator):
    def __init__(self, yosai_config_path: str = '/../../../whatever_filename_you_want.yaml'):
        self.yosai = Yosai(file_path=yosai_config_path)

    def authenticate_user(self, user, password):
        with Yosai.context(self.yosai):
            subject = Yosai.get_current_subject()

            authc_token = UsernamePasswordToken(username=user, credentials=password)

            try:
                subject.login(authc_token)
            except UnknownAccountException:
            # insert here
            except IncorrectCredentialsException:
            # insert here
            except LockedAccountException:
            # insert here
            except ExcessiveAttemptsException:
            # insert here
            except AuthenticationException:
        # insert here
