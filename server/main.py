import socket
import json
import select
import sys
import time
from inspect import getmembers, isfunction
from mongoengine import connect

from models import User
import commands

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
        self.open_sockets = [self.master_socket]
        self.sock_table = {}
        self.user_table = {}
        self.recv_table = {}
        self.db = connect(MONGO_DATABASE)

    # forwards client requests to be handled by the proper command
    def process_request(self, client, request):
        # changes new-user -> new_user
        method = request['method'].replace('-', '_')
        args = request['content']
        
        if method == 'init_send':
            host, send_port = client.getpeername()
            recv_port = int(args)

            recv_addr = (host, recv_port)
            if recv_addr in self.sock_table:
                self.recv_table[client] = self.sock_table[recv_addr]
            else:
                self.recv_table[client] = recv_addr

            return
            

        elif method == 'init_recv':
            addr = client.getpeername()

            if addr in self.recv_table.values():
                index = list(self.recv_table.values()).index(addr)
                key = list(self.recv_table.keys())[index]
                self.recv_table[key] = client

            return

        if method in select_command:
            cmd = select_command[method]

            response = cmd(self, client, args)        
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
        # print('Waiting for data...')
        prefix = conn.recv(PREFIX_LEN)

        if not prefix:
            return False, None

        prefix_str = prefix.decode('utf-8')
        request_len = int(prefix_str)

        # print(f'Awaiting a {request_len} byte request')

        buffer = bytearray()

        while len(buffer) < request_len:
            remaining_bytes = request_len - len(buffer)
            buffer += conn.recv(remaining_bytes)
            # print(f'Buffer contains {len(buffer)} bytes')

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

    def send_to(self, client, payload):
        conn = self.recv_table[client]
        self.send(conn, payload)

    def send_msg(self, conn, msg):
        self.send_to(conn, {'message': msg})

    def send_msg_to_all(self, msg, exclude=None):
        for client in self.user_table.keys():
            if client != exclude:
                self.send_msg(client, msg)

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

    def drop_client(self, client):
        if client in self.open_sockets: self.open_sockets.remove(client)
        if client in self.user_table:
            del self.user_table[client]
        if client in self.recv_table:
            recv_client = self.recv_table[client]
            self.drop_client(recv_client)
            del self.recv_table[client]
        client.close()
        # print("Connection closed")

    # returns user model from a client
    def get_user(self, client):
        user_id = self.user_table[client]
        return User.objects(pk=user_id).first()
    
    def client_to_str(self, client):
        addr = client.getpeername()
        return f'{addr[0]}:{addr[1]}'

    def run(self):
        self.bind()
        self.master_socket.listen(1)
        print(f'Listening on port {self.port}')
        
        try:
            while True:
                rlist, wlist, xlist = select.select(self.open_sockets, [], [])

                for n, s in enumerate(rlist):                    
                    # new client
                    if s == self.master_socket:
                        client, address = self.master_socket.accept()
                        addr = self.client_to_str(client)

                        self.open_sockets.append(client)
                        self.sock_table[address] = client

                        self.send(client, {
                            "message": "Welcome to Distributed Dungeon! Login with 'login <username> <password>' or 'new-user <username> <password>'"
                        })

                        print(f'Accepting new connection from', addr)
                    
                    # existing client
                    else:
                        client = s

                        try:
                            success, data_json = self.recv(client)

                            if not success:
                                self.drop_client(client)
                                continue

                            resp = self.process_request(client, data_json)

                            if resp:
                                self.send_to(client, resp)

                                # print("Processed request from", self.client_to_str(client))
                            
                        except ConnectionResetError:
                            self.drop_client(client)


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
