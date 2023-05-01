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
    user.move_to(start)

    user.save()

    core.user_table[addr] = user.name
    core.user_table[user.name] = addr
    return f"Hi {user.name}, welcome to Distributed Dungeon!"

@validate_args(split=False)
@login_required
def say(core, addr, args):
    user = core.get_user(addr)

    to_self = f'You said "{args}"'
    to_others = f'{user.name} said "{args}"'

    core.send_msg_to_room(user, to_others)

    return to_self

@validate_args()
@login_required
def look(core, addr, args):
    user = core.get_user(addr)
    room = user.location
    desc = room.description

    if args:
        target = args[0]

        item = None
        for i in user.items:
            if target == i.name:
                item = i
                break

        if item: return item.description

        feature = None
        for f in room.features:
            if target == f.tag:
                feature = f

        if feature: return feature.description

        return "Couldn't find that in the room"

    if room.features:
        desc += " "
        for feature in room.features: 
            desc += feature.description + " "

    if room.items:
        desc += "\n\n"
        for item in room.items:
            desc += item.placement + " "
    
    # not alone
    if len(room.users) > 1:
        other_users = [u.name for u in room.users]
        other_users.remove(user.name)

        desc += f"\n\n{text_array(other_users)} {'is' if is_plural(other_users) else 'are'} also in the room"

    return desc

@validate_args()
@login_required
def inventory(core, addr, args):
    user = core.get_user(addr)

    if user.items:
        items = [f"[{i.name}]" for i in user.items]
        return "You are carrying " + text_array(items)

    else:
        return "You aren't carrying anything."

@validate_args()
@login_required
def grab(core, addr, args):
    user = core.get_user(addr)
    room = user.location

    target = args[0]

    item = None
    for i in room.items:
        if target == i.name:
            item = i
            break
    
    if not item:
        return "Couldn't find that in the room"
    
    room.items.remove(item)
    user.items.append(item)
    room.save()
    user.save()

    return f"You picked up the [{item.name}]"

@validate_args()
@login_required
def use(core, addr, args):
    user = core.get_user(addr)
    room = user.location

    target = args[0]

    feature = None
    for f in room.features:
        if target == f.tag:
            feature = f
            break

    if not feature:
        return "Couldn't find that in the room"
    
    action = feature.action

    if action['type'] == 'move':
        dest = Room.objects(pk=action['dest']).first()
        user.move_to(dest)
        return action['msg']
    

@login_required
def logout(core, addr, args):
    user = core.get_user(addr)
    user.logout()
    return "successfully logged out?"

@login_required
def reset_world(core, addr, args):
    core.send_msg_to_all("Resetting world...")
    Feature.drop_collection()
    Room.drop_collection()
    world.load_rooms()
    for user in User.objects():
        user.reset()

@login_required
def shutdown(core, addr, args):
    core.send_msg_to_all("Server is shutting down...")
    quit()

def disconnect(core, addr, args):
    core.drop_client(addr)
    