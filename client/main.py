import socket
import time
import json
import threading
import sys

PREFIX_LEN = 16
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5000

CSI = b"\x1b["
CLEAR_LINE = CSI + b"2K"
CURSOR_UP_ONE = CSI + b"1A"
PROMPT_INTRO = ">"

def emit(*args):
    sys.stdout.buffer.write(b''.join(args))

class DungeonClient:
    def __init__(self, host, port, quiet=False):
        self.host = host
        self.port = port
        self.quiet = quiet
        self.socket_init()
        self.connect()
        sockname = self.send_socket.getsockname()
        self.client_str = f'{sockname[0]}:{sockname[1]}'
        self.recv_port = self.recv_socket.getsockname()[1]

        self._send({
            'method': 'init_recv',
            'content': ''
        }, socket=self.recv_socket)
        
        self._send({
            'method': 'init_send',
            'content': self.recv_port
        })

    def socket_init(self):
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.settimeout(5)

    def reconnect(self):
        self.close()
        self.socket_init()
        self.connect()

    def connect(self):
        while True:
            try:
                self.send_socket.connect((self.host, self.port))
                self.recv_socket.connect((self.host, self.port))
                break
            except (ConnectionRefusedError, ConnectionAbortedError):
                print("Failed to connect to server")
                time.sleep(1)

    def close(self):
        self.send_socket.close()
        self.recv_socket.close()

    def _recv(self, socket=None):
        if not socket: socket = self.recv_socket
        # print("recv as", socket.getsockname())
        prefix = socket.recv(PREFIX_LEN)

        prefix_str = prefix.decode('utf-8')
        if not prefix_str:
            # print("Connection interrupted")
            return False

        response_len = int(prefix_str)

        buffer = bytearray()

        while len(buffer) < response_len:
            remaining_bytes = response_len - len(buffer)
            buffer += socket.recv(remaining_bytes)

        data_str = buffer.decode('utf-8')
        data_json = json.loads(data_str)

        return data_json

    def _send(self, payload, socket=None):
        if not socket: socket = self.send_socket
        # print("send as", socket.getsockname())
        payload_str = json.dumps(payload)
        payload_bytes = payload_str.encode('utf-8')

        payload_len = len(payload_bytes)

        prefix_str = f'{payload_len:0{PREFIX_LEN}}'
        prefix_bytes = prefix_str.encode('utf-8')

        while True:
            try:
                socket.sendall(prefix_bytes + payload_bytes)
                break
            except BrokenPipeError:
                print("Connection to socket closed")
                self.reconnect()

        #     resp = None
        #     try:
        #         resp = self._recv()
        #     except (socket.timeout, ConnectionResetError):
        #         print("Connection to socket closed")
        #         self.reconnect()

        #     if resp:
        #         break
        #     else:
        #         self.reconnect()

        # return resp
    
    def receive_data(self):
        latencies = []
        
        while True:
            try:
                data = self._recv()
            except (ConnectionResetError):
                print("Connection to socket closed")
                quit()
            if not data:
                # print("Connection closed, pressed enter to continue")
                if latencies:
                    # print(latencies)
                    print("avg latency", sum(latencies) / len(latencies))
                quit()

            if not self.quiet: emit(CLEAR_LINE, CURSOR_UP_ONE)

            if 'timestamp' in data:
                before = int(data['timestamp'])
                after = time.time_ns()
                elapsed = after - before
                latencies.append(elapsed / 1_000_000_000)
                # print(elapsed)
                # print(before, after, elapsed, elapsed / 1_000_000_000)

            if not self.quiet:
                print("\n" + data['message'])
                
                print("\n" + PROMPT_INTRO + " ", end="")

    def send_data(self, recv_thread):
        while True:
            if not recv_thread.is_alive():
                quit()

            msg = input()
            words = msg.split()

            if not words: continue

            method = words[0]
            args = words[1:]
            content = msg[len(method) + 1:]

            if method == 'quit': quit()

            payload = {
                'method': method,
                'content': content,
            }

            # if (method == 'login') or (method == 'new-user'):
            #     payload['content'] += " " + str(self.recv_port)

            if not self.quiet:
                print("\n" + PROMPT_INTRO + " " + msg)
                emit(CURSOR_UP_ONE)

            self._send(payload)
    

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Using default port", DEFAULT_PORT)
        print("Using default host", DEFAULT_HOST)
        port = DEFAULT_PORT
        host = DEFAULT_HOST

    elif len(sys.argv) == 2:
        print("Using default port", DEFAULT_PORT)
        port = DEFAULT_PORT
        host = sys.argv[1]

    elif len(sys.argv) == 3:
        host = sys.argv[1]
        port_str = sys.argv[2]
        if port_str.isdigit():
            port = int(port_str)
        else:
            print("Invalid port number")
            quit()

    else:
        print("Usage: main.py [host] [port], leave args empty to use default")

    client = DungeonClient(host, port)

    recv_thread = threading.Thread(target=client.receive_data)
    recv_thread.setDaemon(True)
    recv_thread.start()
    client.send_data(recv_thread)
