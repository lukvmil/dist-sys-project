import threading
from main import DungeonClient
import time
import uuid
import random
import sys

num_clients = int(sys.argv[1])
clients = [DungeonClient("localhost", 5000, quiet=True) for x in range(num_clients)]

recv_threads = [threading.Thread(target=client.receive_data) for client in clients]
for rt in recv_threads:
    rt.setDaemon(True)
    rt.start()

count = 0
for client in clients:
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())

    client._send({
        "method": "new-user",
        "content": f"{username} {password}"
    })

    count += 1
    print("created user", count)

# input()

before = time.time_ns()
for i in range(50):
    
    # print(ts)
    for client in clients:
        ts = time.time_ns()
        client._send({
            "method": "look",
            "content": "",
            "timestamp": str(ts)
        })

        time.sleep(random.uniform(0, 1) / num_clients)

elapsed = time.time_ns() - before

print("elapsed", elapsed / 1_000_000_000)

for client in clients:
    client._send({
        "method": "disconnect",
        "content": ""
    })

for rt in recv_threads:
    rt.join()

elapsed = time.time_ns() - before

# print("elapsed", elapsed / 1_000_000_000)