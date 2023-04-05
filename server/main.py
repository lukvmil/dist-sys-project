import socket
import json
import sys
import time
import select
from multiprocessing import Process

PREFIX_LEN = 16

def to_str(addr):
    return f'{addr[0]}:{addr[1]}'

class DungeonServer:
    def __init__(self, port):
        self.port = port
        self.master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.open_sockets = [self.master_socket]

    def process_request(self, request):
        print(request)
        return {'success': True}
    
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

    def send(self, conn, payload):
        payload_str = json.dumps(payload)
        payload_bytes = bytes(payload_str, 'utf-8')

        payload_len = len(payload_bytes)

        prefix_str = f'{payload_len:0{PREFIX_LEN}}'
        prefix_bytes = prefix_str.encode('utf-8')

        conn.sendall(prefix_bytes + payload_bytes)

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
        self.open_sockets.remove(client)
        client.close()
        print("Connection closed")

    def run_hashtable(self):
        self.master_socket.listen(1)
        print(f'Listening on port {self.port}')
        
        try:
            while True:
                rlist, wlist, xlist = select.select(self.open_sockets, [], [])

                for n, s in enumerate(rlist):                    
                    # new client
                    if s == self.master_socket:
                        client, address = self.master_socket.accept()
                        addr = to_str(address)

                        self.open_sockets.append(client)

                        print(f'Accepting new connection from', addr)
                    
                    # existing client
                    else:
                        client = s

                        try:
                            success, data_json = self.recv(client)

                            if not success:
                                self.drop_client(client)
                                continue

                            resp = self.process_request(data_json)

                            self.send(client, resp)

                            # print("Processed request from", to_str(client.getpeername()))
                            
                        except ConnectionResetError:
                            self.drop_client(client)


        except KeyboardInterrupt:
            print('Shutting down...')
            return

    def run(self):
        self.bind()
        self.run_hashtable()

if __name__ == "__main__":
    server = HashTableServer(5000)
    server.run()
