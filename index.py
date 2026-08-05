import socket
import time

HOST = "127.0.0.1"
PORT = 8000

# server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # binding the server to ip host and port PORT
    s.bind((HOST, PORT))
    s.listen()

    # keep the server contineously running
    while True:
        conn, addrs = s.accept()
        time.sleep(5)
        # when request appears
        with conn:
            print(f"client connected from address {addrs}")
            response = f"Hello, {addrs}"
            conn.sendall(response.encode('utf-8'))