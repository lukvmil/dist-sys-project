import socket
import json
import select
import sys
import time
from inspect import getmembers, isfunction
from mongoengine import connect

from models import *
import commands
import world

# generating command -> function lookup table
select_command = {
    name: func
    for name, func in getmembers(commands, isfunction)
    if func.__module__ == commands.__name__
}

PREFIX_LEN = 16
DEFAULT_PORT = 5000
MONGO_DATABASE = "dungeon"

class DungeonServer:
    def __init__(self, port):
        self.port = port
        self.master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_table = {}
        self.recv_table = {}
        self.user_table = {}
        self.db = connect(MONGO_DATABASE)

    # forwards client requests to be handled by the proper command
    def process_request(self, addr, request):
        # changes new-user -> new_user
        method = request['method'].replace('-', '_')
        args = request['content']
        
        # special method for initializing client send thread
        if method == 'init_send':
            host, send_port = addr
            recv_port = int(args)

            recv_addr = (host, recv_port)
            # creates send -> recv binding in user_table
            self.recv_table[addr] = recv_addr
            return
            
        # special method for initializing client receive thread
        elif method == 'init_recv':
            return
        
        # selects command to call from commands module
        if method in select_command:
            cmd = select_command[method]
            response = cmd(self, addr, args)        
        else:
            response = "Invalid command"
        
        if response:
            resp = {'message': response}
        else:
            resp = None

        if 'timestamp' in request:
            # print(request['timestamp'])
            resp['timestamp'] = request['timestamp']

        return resp
    
    # handles receiving data from clients
    def recv(self, conn):
        prefix = conn.recv(PREFIX_LEN)

        if not prefix:
            return False, None

        prefix_str = prefix.decode('utf-8')
        request_len = int(prefix_str)

        buffer = bytearray()

        while len(buffer) < request_len:
            remaining_bytes = request_len - len(buffer)
            buffer += conn.recv(remaining_bytes)

        data_str = buffer.decode('utf-8')
        data_json = json.loads(data_str)

        return True, data_json

    # handles sending data to clients
    def send(self, conn, payload):
        payload_str = json.dumps(payload)
        payload_bytes = bytes(payload_str, 'utf-8')

        payload_len = len(payload_bytes)

        prefix_str = f'{payload_len:0{PREFIX_LEN}}'
        prefix_bytes = prefix_str.encode('utf-8')

        conn.sendall(prefix_bytes + payload_bytes)

    # forwards a message to a user's receive thread
    def send_to(self, addr, payload):
        recv_addr = self.recv_table[addr]
        conn = self.sock_table[recv_addr]
        self.send(conn, payload)

    def send_msg(self, addr, msg):
        self.send_to(addr, {'message': msg})

    def send_msg_to_room(self, user, msg):
        for other in user.location.users:
            if other == user: continue
            addr = self.user_table[other.name]
            self.send_msg(addr, msg)            

    def send_msg_to_all(self, msg, exclude=None):
        user_addrs = [a for a in list(self.user_table.values()) if isinstance(a, tuple)]
        for addr in user_addrs:
            if addr != exclude:
                self.send_msg(addr, msg)

    # binds server to port
    def bind(self):
        try:
            self.master_socket.bind(('', self.port))
        except OSError:
            print("Port is already in use!")
            quit()

        address = self.master_socket.getsockname()
        self.host, self.port = address
        print(f"Bound to {self.host}:{self.port}")

    def drop_client(self, addr):
        if addr in self.sock_table:
            client = self.sock_table[addr]
            del self.sock_table[addr]
            del self.sock_table[client]
            client.close()
            # print("Connection closed with", addr)

        if addr in self.user_table:
            user = self.get_user(addr)
            # removes users from game world
            room = user.location
            self.send_msg_to_room(user, f"{user.name} has left the room.")
            room.users.remove(user)
            room.save()

            print(f"User '{user.name}' logged out from {addr}")

            del self.user_table[addr]
            del self.user_table[user.name]

        if addr in self.recv_table:
            recv_addr = self.recv_table[addr]
            self.drop_client(recv_addr)
            del self.recv_table[addr]

    # returns user model from a client
    def get_user(self, addr):
        user_id = self.user_table[addr]
        if user_id:
            return User.objects(pk=user_id).first()
        else:
            return None
    
    def get_users(self):
        users = []
        for entry in self.user_table.values():
            user = entry.get('user')
            if user: users.append(user)
    
    def run(self):
        if 'dungeon' not in self.db.list_database_names():
            print('Loading default world')
            world.load_rooms()

        # makes sure rooms are empty on startup
        for room in Room.objects():
            room.users = []
            room.save()

        self.bind()
        self.master_socket.listen(1)
        print(f'Listening on port {self.port}')
        
        try:
            while True:
                open_sockets = [s for s in list(self.sock_table.values()) if not isinstance(s, tuple)] + [self.master_socket]
                rlist, wlist, xlist = select.select(open_sockets, [], [])

                for n, s in enumerate(rlist):                    
                    # new client
                    if s == self.master_socket:
                        client, addr = self.master_socket.accept()

                        self.sock_table[addr] = client
                        self.sock_table[client] = addr

                        self.send(client, {
                            "message": "Welcome to Distributed Dungeon! Login with 'login <username> <password>' or 'new-user <username> <password>'"
                        })

                        # print(f'Accepting new connection from', addr)
                    
                    # existing client
                    else:
                        client = s
                        addr = self.sock_table[client]

                        try:
                            success, data_json = self.recv(client)

                            if not success:
                                self.drop_client(addr)
                                continue

                            resp = self.process_request(addr, data_json)

                            if resp:
                                self.send_to(addr, resp)

                            
                        except ConnectionResetError:
                            self.drop_client(addr)


        except KeyboardInterrupt:
            print('Shutting down...')
            return

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Using default port", DEFAULT_PORT)
        port = DEFAULT_PORT
        
    
    elif len(sys.argv) == 2:
        port_str = sys.argv[1]
        if port_str.isdigit():
            port = int(port_str)
        else:
            print("Invalid port number")
            quit()
    
    else:
        print("Usage: main.py [port], leave arg empty to use default")

    server = DungeonServer(port)
    server.run()
