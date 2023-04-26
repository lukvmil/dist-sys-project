from command_params import *
from models import *
import world

@validate_args(2)
@logout_required
def login(core, client, args):
    username, password = args

    user = User.objects(name=username).first()
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

    if User.objects(name=username).first():
        return "This username is already in use"

    user = User(
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
def look(core, client, content):
    user = core.get_user(client)
    return f"You look around and see...\n{user.location.description}"

@login_required
def reset_world(core, client, args):
    core.send_msg_to_all("Resetting world...")
    Room.drop_collection()
    world.load_rooms()


@login_required
def shutdown(core, client, args):
    core.send_msg_to_all("Server is shutting down...")
    quit()