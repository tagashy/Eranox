class Authenticator(object):
    def authenticate_user(self, user, password):
        raise NotImplementedError()

    def log_out_user(self, user):
        raise NotImplementedError()
