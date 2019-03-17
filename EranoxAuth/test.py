from EranoxAuth import Authenticator, DefaultEngine, AuthenticationError

if __name__ == '__main__':
    auth = Authenticator(DefaultEngine('sqlite:///eranox.db'))
    print()
    print()
    try:
        user = auth.authenticate_user("TITI", "123456")
    except AuthenticationError:
        auth.create_user("toto", "123456")
        user = auth.authenticate_user("toto", "123456")

    print(user)