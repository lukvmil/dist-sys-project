
def validate_num_args(count):
    def decorator(func):
        def check_args(core, client, args):
            if len(args) != count:
                return "Invalid number of arguments"
            else:
                return func(core, client, args)    
        return check_args
    return decorator

def login_required(func):
    def check_login(core, client, args):
        if client not in core.user_table:
            return "You must login first!"
        else:
            return func(core, client, args)
    return check_login
        

def logout_required(func):
    def check_login(core, client, args):
        if client in core.user_table:
            return "You are already logged in!"
        else:
            return func(core, client, args)
    return check_login
