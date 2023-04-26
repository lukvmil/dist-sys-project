import functools

# passes args as a split list of words or single string, and enforce number of arguments
def validate_args(count=False, split=True):
    def decorator(func):
        @functools.wraps(func)
        def check_args(core, client, content):
            args = content.split() if split else content
            if (count != False) and (len(args) != count):
                return "Invalid number of arguments"
            else:
                return func(core, client, args)    
        return check_args
    return decorator

# command only allowed by logged in users 
def login_required(func):
    @functools.wraps(func)
    def check_login(core, client, args):
        if client not in core.user_table:
            return "You must login first!"
        else:
            return func(core, client, args)
    return check_login
        
# command only allowed by logged out users 
def logout_required(func):
    @functools.wraps(func)
    def check_login(core, client, args):
        if client in core.user_table:
            return "You are already logged in!"
        else:
            return func(core, client, args)
    return check_login

# converts an array of strings to a gramatically correct english list
def text_array(arr):
    string = ""
    if len(arr) == 1:
        string = arr[0]
    
    elif len(arr) == 2:
        string = f"{arr[0]} and {arr[1]}"
    
    elif len(arr) > 2:
        for w in arr[:-1]:
            string += f"{w}, "

        string += f"and {arr[-1]}"

    return string

def is_plural(arr): return len(arr) == 1