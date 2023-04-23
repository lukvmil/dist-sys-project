import socket
import time
import json
import threading
import sys

PREFIX_LEN = 16

CSI = b"\x1b["
CLEAR_LINE = CSI + b"2K"
CURSOR_UP_ONE = CSI + b"1A"
PROMPT_INTRO = ">"

def emit(*args):
    sys.stdout.buffer.write(b''.join(args))

class DungeonClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.retry_table = {}
        self.socket_init()
        self.connect()

    def socket_init(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.settimeout(5)

    def reconnect(self):
        self.close()
        self.socket_init()
        self.connect()

    def connect(self):
        while True:
            try:
                self.socket.connect((self.host, self.port))
                break
            except (ConnectionRefusedError, ConnectionAbortedError):
                print("Failed to connect to server")
                time.sleep(1)

    def close(self):
        self.socket.close()

    def _recv(self):
        prefix = self.socket.recv(PREFIX_LEN)

        prefix_str = prefix.decode('utf-8')
        if not prefix_str:
            print("Connection interrupted")
            return False

        response_len = int(prefix_str)

        buffer = bytearray()

        while len(buffer) < response_len:
            remaining_bytes = response_len - len(buffer)
            buffer += self.socket.recv(remaining_bytes)

        data_str = buffer.decode('utf-8')
        data_json = json.loads(data_str)

        return data_json

    def _send(self, payload):
        payload_str = json.dumps(payload)
        payload_bytes = payload_str.encode('utf-8')

        payload_len = len(payload_bytes)

        prefix_str = f'{payload_len:0{PREFIX_LEN}}'
        prefix_bytes = prefix_str.encode('utf-8')

        while True:
            try:
                self.socket.sendall(prefix_bytes + payload_bytes)
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
        while True:
            data = self._recv()
            if not data:
                quit()
            emit(CLEAR_LINE, CURSOR_UP_ONE)
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

            if method == 'quit': quit()

            payload = {
                'method': method,
                'args': args
            }

            print("\n" + PROMPT_INTRO + " " + msg)
            emit(CURSOR_UP_ONE)

            self._send(payload)
    

if __name__ == "__main__":
    client = DungeonClient("localhost", 5000)

    recv_thread = threading.Thread(target=client.receive_data)
    recv_thread.setDaemon(True)
    recv_thread.start()
    client.send_data(recv_thread)
