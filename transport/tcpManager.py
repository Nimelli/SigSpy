import logging
import threading
import time
import socket


class TcpProc():
    def __init__(self, data_in_queue, data_out_queue) -> None:
        self.conn = None
        self.readline_buf = bytearray()
        self.data_in_queue = data_in_queue
        self.data_out_queue = data_out_queue

        self.thread_stop = threading.Event()
        self.threads = []
        self.running = False
        

    def open(self, host="127.0.0.1", port=65432):
        if(self.running):
            # TBC: or close first then open
            return False

        opened = False

        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.settimeout(2)
            self.conn.connect((host, port))
            opened = True
        except :
            logging.error("Can not open socket")

        return opened
    
    def start(self):
        if(self.conn and not self.running):
            self.thread_stop.clear()
            thread_reader = threading.Thread(target=self.reader)
            thread_cmder = threading.Thread(target=self.commander)
            self.threads.append(thread_reader)
            self.threads.append(thread_cmder)
            thread_reader.start()
            thread_cmder.start()
            self.running = True

    def reader(self):
        """ to run in thread - listen serial and add to in queue """
        logging.debug("tcp reader start")
        while not self.thread_stop.is_set():
            line = self.readline()
            self.data_in_queue.put(line)

    def commander(self):
        """ to run in thread - check out queue and send to serial """
        logging.debug("serial commander start")
        while not self.thread_stop.is_set():
            buff = bytearray()
            while not self.data_out_queue.empty():
                buff.extend(self.data_out_queue.get())
                self.conn.sendall(buff)

            time.sleep(0.05) # no need to poll too fast 


    def readline(self):
        """ optimized readline"""
        i = self.readline_buf.find(b"\n")
        if i >= 0:
            r = self.readline_buf[:i+1]
            self.readline_buf = self.readline_buf[i+1:]
            return r
        while True:
            data = self.conn.recv(1024)
            i = data.find(b"\n")
            if i >= 0:
                r = self.readline_buf + data[:i+1]
                self.readline_buf[0:] = data[i+1:]
                return r
            else:
                self.readline_buf.extend(data)
    
    def close(self):
        if(self.conn):
            logging.debug("Close tcp")
            self.thread_stop.set() # stop thread
            for t in self.threads:
                t.join()
            self.conn.close()
            self.conn = None
            self.running = False