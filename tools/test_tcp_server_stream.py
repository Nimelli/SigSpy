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
    dd = 0

    with conn:
        print(f"Connected by {addr}")
        t_start = round(time.time()*1000)
        while True:
            try:
                t_now = round(time.time()*1000) -t_start
                data = "{}, {}, {}, {}, {}, {}, {}, {}\r\n".format(t_now, randint(20, 30), randint(-40, 30), randint(50, 60), 
                                                                    randint(70, 80), randint(100, 120), randint(140, 150), randint(-50, -30))
                data_enc = data.encode("utf-8")
                #print("Sending: {}".format(data_enc))
                conn.sendall(data_enc)   
                dd += 1
                if(dd>=100):
                    dd = 0
                time.sleep(0.001)
            except socket.error or KeyboardInterrupt:
                break