from command_helpers import *
from models import *
import random
import world

def help(core, addr, args):
    return """Commands:
    login <username> <password>     - logs into a user account
    new-user <username> <password>  - creates a new user account
    logout                          - logs out of a user account
    quit                            - closes out of the game
    say <msg>                       - sends a message to players in your room
    shout <msg>                     - sends a message to all players
    look / look <target>            - inspects the room, objects in it, or your inventory
    inventory                       - displays items you are carrying
    grab                            - picks up an item and stores it in your inventory
    use <target>                    - interacts with an object in a room"""

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

    print(f"User '{user.name}' logged in from {addr}")

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
        password=password,
        health=15,
        accuracy=8,
        damage=4
    )

    start = Room.objects(start=True).first()
    user.move_to(start)
    core.send_msg_to_room(user, f"{user.name} has entered the room.")

    user.save()

    core.user_table[addr] = user.name
    core.user_table[user.name] = addr
    print(f"New user '{user.name}' logged in from {addr}")

    return f"Hi {user.name}, welcome to Distributed Dungeon!"

@validate_args(split=False)
@login_required
def say(core, addr, args):
    user = core.get_user(addr)

    to_self = f'You said "{args}"'
    to_others = f'{user.name} said "{args}"'

    core.send_msg_to_room(user, to_others)

    return to_self

@validate_args(split=False)
@login_required
def shout(core, addr, args):
    user = core.get_user(addr)

    to_self = f'You shouted "{args}"'
    to_others = f'{user.name} shouted "{args}"'
    
    core.send_msg_to_all(to_others, user)
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

        item = None
        for i in room.items:
            if target == i.name:
                item = i
                break

        if item: return item.description

        feature = None
        for f in room.features:
            if target == f.tag:
                feature = f

        if feature: return feature.description

        return "Couldn't find that in the room."

    if room.features:
        desc += " "
        for feature in room.features: 
            desc += feature.placement + " "

    if room.items:
        desc += "\n\n"
        for item in room.items:
            desc += item.placement + " "
    
    if room.enemies:
        desc += "\n\n"
        for enemy in room.enemies:
            desc += enemy.placement + " "
    
    # not alone
    if len(room.users) > 1:
        other_users = [u.name for u in room.users]
        other_users.remove(user.name)

        desc += f"\n\n{text_array(other_users)} {'is' if is_plural(other_users) else 'are'} also in the room."

    return desc

@validate_args()
@login_required
def inventory(core, addr, args):
    user = core.get_user(addr)

    if user.items:
        items = [f"[{i.name}]" for i in user.items]
        return "You are carrying " + text_array(items) + ". (And your trusty adventurer sword of course!)"

    else:
        return "You aren't carrying anything except for your trusty adventurer sword."

@validate_args(1)
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
        return "Couldn't find that in the room."
    
    room.items.remove(item)
    user.items.append(item)
    room.save()
    user.save()

    to_others = f"{user.name} picked up the [{item.name}]."
    core.send_msg_to_room(user, to_others)

    return f"You picked up the [{item.name}]."

@validate_args(1)
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
        return "Couldn't find that in the room."
    
    action = feature.action

    if action['type'] == 'move':
        if action.get('locked', False):
            item = action['required']
            if user.has(item):
                del action['locked']
                if 'unlock_placement' in action:
                    feature.placement = action['unlock_placement']
                if 'unlock_description' in action:
                    feature.description = action['unlock_description']
                feature.save()

                to_others = f"{user.name} opened the [{feature.tag}]."
                core.send_msg_to_room(user, to_others)

                return action['unlock_msg']
            else:
                return action['locked_msg']

        else:
            dest = Room.objects(pk=action['dest']).first()
            core.send_msg_to_room(user, f"{user.name} has left the room.")
            user.move_to(dest)
            core.send_msg_to_room(user, f"{user.name} has entered the room.")
            return action['move_msg']
        
@validate_args(1)
@login_required
def attack(core, addr, args):
    user = core.get_user(addr)
    room = user.location

    target = args[0]

    enemy = None
    for e in room.enemies:
        if target == e.tag:
            enemy = e
            break

    if not enemy:
        return "Couldn't find that in the room."
    
    player_hit = random.randint(1, 10) < user.accuracy
    player_hit_damage = random.randint(1, user.damage)

    if player_hit:
        enemy.health -= player_hit_damage
        result = f"You hit the [{enemy.tag}] for {player_hit_damage} damage! (It now has {enemy.health} health remaining.)"
        core.send_msg_to_room(user, f"{user.name} attacked [{enemy.tag}].")
        if enemy.health <= 0:
            result += " With that final blow, it collapses to the floor dead."
            enemy.kill(room)
            core.send_msg_to_room(user, f"{user.name} killed [{enemy.tag}].")
    else:
        result = "Your attack missed."

    enemy_hit = random.randint(1, 10) < enemy.accuracy
    enemy_hit_damage = random.randint(1, enemy.damage)

    enemy.save()

    if enemy.dead:
        return result

    if enemy_hit:
        user.health -= enemy_hit_damage
        result += f"\n\nThe [{enemy.tag}] hit you for {enemy_hit_damage} damage! (You now have {user.health} health remaining.)"
        core.send_msg_to_room(user, f"{enemy.tag} attacked [{user.name}].")
        if user.health <= 0:
            result += "\nYou died. All of your items were dropped and you will return to the first room."
            user.kill()
            core.send_msg_to_room(user, f"{enemy.tag} killed [{user.name}].")
    else:
        result += f"\n\nThe [{enemy.tag}]'s attack missed."

    user.save()
    return result

@login_required
def logout(core, addr, args):
    user = core.get_user(addr)
    user.logout()
    name = core.user_table[addr]
    del core.user_table[addr]
    del core.user_table[name]
    return "Successfully logged out."

@login_required
def reset_world(core, addr, args):
    core.send_msg_to_all("Resetting world...")
    Feature.drop_collection()
    Item.drop_collection()
    Enemy.drop_collection()
    Room.drop_collection()
    world.load_rooms()
    user_addrs = [a for a in list(core.user_table.values()) if isinstance(a, tuple)]
    for addr in user_addrs:
        user = core.get_user(addr)
        user.reset()

@login_required
def shutdown(core, addr, args):
    core.send_msg_to_all("Server is shutting down...")
    quit()

def disconnect(core, addr, args):
    core.drop_client(addr)
    