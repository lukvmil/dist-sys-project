from command_helpers import *
from models import *
import world

@validate_args(2)
@logout_required
def login(core, addr, args):
    username, password = args

    user = User.objects(name=username).first()
    if not user:
        return "Invalid username"
    
    if user.password != password:
        return "Invalid password"
    
    if user.name in core.user_table:
        return "User is already logged in through another client"

    core.user_table[addr] = user.name
    core.user_table[user.name] = addr

    # rejoining user to room
    room = user.location
    room.users.append(user)
    room.save()

    return f"Hi {user.name}, welcome to Distributed Dungeon!"

@validate_args(2)
@logout_required
def new_user(core, addr, args):
    username, password = args

    if User.objects(name=username).first():
        return "This username is already in use"

    user = User(
        name=username,
        password=password
    )

    start = Room.objects(start=True).first()
    user.enter_room(start)

    user.save()

    core.user_table[addr] = user.name
    core.user_table[user.name] = addr
    return f"Hi {user.name}, welcome to Distributed Dungeon!"

@validate_args(split=False)
@login_required
def say(core, addr, content):
    user = core.get_user(addr)

    to_self = f'You said "{content}"'
    to_others = f'{user.name} said "{content}"'

    core.send_msg_to_room(user, to_others)

    return to_self

@login_required
def look(core, addr, content):
    user = core.get_user(addr)
    room = user.location
    desc = room.description

    # not alone
    if len(room.users) > 1:
        other_users = [u.name for u in room.users]
        other_users.remove(user.name)

        desc += f"\n\n{text_array(other_users)} {'is' if is_plural(other_users) else 'are'} also in the room"

    return desc

@login_required
def logout(core, addr, content):
    user = core.get_user(addr)
    user.logout()
    return "successfully logged out?"

@login_required
def reset_world(core, addr, args):
    core.send_msg_to_all("Resetting world...")
    Room.drop_collection()
    world.load_rooms()


@login_required
def shutdown(core, addr, args):
    core.send_msg_to_all("Server is shutting down...")
    quit()

def disconnect(core, addr, args):
    core.drop_client(addr)
    