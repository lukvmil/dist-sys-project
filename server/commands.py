from command_params import *
from models import *

@validate_args(2)
@logout_required
def login(core, client, args):
    username, password = args

    user = UserModel.objects(name=username).first()
    if not user:
        return "Invalid username"
    
    if user.password != password:
        return "Invalid password"
    
    if user.id in core.user_table.values():
        return "User is already logged in through another client"

    core.user_table[client] = user.id
    return f"Hi {user.name}, welcome to Distributed Dungeon!"

@validate_args(2)
@logout_required
def new_user(core, client, args):
    username, password = args

    if UserModel.objects(name=username).first():
        return "This username is already in use"

    user = UserModel(
        name=username,
        password=password
    )
    user.save()

    core.user_table[client] = user.id
    return f"Hi {user.name}, welcome to Distributed Dungeon!"

@validate_args(split=False)
@login_required
def say(core, client, content):
    user = core.get_user(client)

    to_self = f'You said "{content}"'
    to_others = f'{user.name} said "{content}"'

    core.send_msg_to_all(to_others, exclude=client)

    return to_self

@login_required
def shutdown(core, client, args):
    core.send_msg_to_all("Server is shutting down...")
    quit()

select = {
    'login': login,
    'new-user': new_user,
    'say': say,
    'shutdown': shutdown
}