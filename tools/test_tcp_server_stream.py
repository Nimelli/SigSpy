# Streaming Server
import socket
import time
from random import randint

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()

    with conn:
        print(f"Connected by {addr}")
        while True:
            try:
                data = "{}, {}, {}, {}, {}, {}, {}, {}\r\n".format(randint(0, 9), randint(20, 30), randint(-40, 30), randint(50, 60), 
                                                                    randint(70, 80), randint(100, 120), randint(140, 150), randint(-50, -30))
                data_enc = data.encode("utf-8")
                #print("Sending: {}".format(data_enc))
                conn.sendall(data_enc)   
                time.sleep(0.0000001)
            except socket.error or KeyboardInterrupt:
                break