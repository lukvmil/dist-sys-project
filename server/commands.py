from command_params import *


@validate_num_args(2)
@login_prohibited
def login(core, client, args):
    print(args)

    username, password = args
    core.user_table[client] = password
    return f"Welcome to the realm, {username}"

def shutdown(core, client, args):
    quit()