from command_params import *
from models import *

@validate_num_args(2)
@logout_required
def login(core, client, args):
    username, password = args

    user = UserModel.objects(name=username).first()
    if not user:
        return "Invalid username"
    
    if user.password != password:
        return "Invalid password"

    core.user_table[client] = user.id
    return f"Welcome to the realm, {user.name}"

@validate_num_args(2)
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
    return f"Welcome to the realm, {user.name}"


@login_required
def shutdown(core, client, args):
    quit()

select = {
    'login': login,
    'new-user': new_user,
    'shutdown': shutdown
}