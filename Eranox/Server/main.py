from ruamel.yaml import YAML

from Eranox.Cli.STDINServer import STDINClient
from Eranox.Server.Manager import Manager
from Eranox.Server.Scheduler import Scheduler

yaml = YAML(typ="safe")


def Core(args):
    config_file = args.config_file
    config = yaml.load(open(config_file))
    if args.bind_addr is not None:
        config["bind_addr"] = args.bind_addr
    manager = Manager(config)  # , timing=10)
    for user in ["test","admin","register"]:
        try:
            manager.authenticator.create_user(user,user)
        except Exception as e:
            print(e)
    test = manager.authenticator.get_user("test")
    admin = manager.authenticator.get_user("admin")
    register = manager.authenticator.get_user("register")
    manager.authenticator.create_permission("test", user=test)
    manager.authenticator.create_permission("admin", user=admin)
    manager.authenticator.create_permission("register", user=register)
    manager.start()
    if args.scheduler:
        try:
            manager.authenticator.create_user("scheduler")
        except Exception as e:
            print(e)
        scheduler = manager.authenticator.get_user("scheduler")
        manager.authenticator.create_permission("scheduler", user=scheduler)
        scheduler = Scheduler(authenticator=manager.authenticator)
        manager.add_client(scheduler)
        scheduler.start()
        scheduler.add_command("pyeval 200*9658", target="all", every_x_seconds=200,
                              callback=lambda msg: print(msg))
    if args.stdin:
        stdin = STDINClient(manager.authenticator)
        manager.add_client(stdin)
        stdin.start()
