from settings import MAX_LINE, T_NAME_SERIAL, T_NAME_TCP

from .serialManager import SerialProc
from .tcpManager import TcpProc

import logging
from queue import Queue


def check_int(s):
    if len(s) <= 0:
        logging.error(s)
        return False
    
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

class Transport():
    def __init__(self) -> None:
        self.data_in_queue = Queue() # host in
        self.data_out_queue = Queue() # host out

        self.t_selection = ""
        self.is_open = False
        self.serProc = SerialProc(self.data_in_queue, self.data_out_queue)
        self.tcpProc = TcpProc(self.data_in_queue, self.data_out_queue)

    def select(self, name):
        logging.debug("transport select")
        if(self.is_open):
            # can't change transport if is open already
            return

        self.t_selection = name
    
    def open(self, port):
        self.close() # just in case
        logging.debug("transport open")

        if(self.t_selection == T_NAME_SERIAL):
            self.is_open = self.serProc.open(port) # open
        elif(self.t_selection == T_NAME_TCP):
            self.is_open = self.tcpProc.open() # default localhaost

    def start(self):
        if(self.is_open):
            logging.debug("transport start")
            if(self.t_selection == T_NAME_SERIAL):
                self.serProc.start()
            elif(self.t_selection == T_NAME_TCP):
                self.tcpProc.start()

    def close(self):
        logging.debug("transport close")
        self.serProc.close()
        self.tcpProc.close()
        self.is_open = False

    def write(self, cmd_b):
        self.data_out_queue.put(cmd_b)        

    def get_data_from_input_buf(self):
        """ read data from input queue, decode and separate (coma separated) the different signals
            Assume data coming line by line and with specific format
            This function needs to change to support other data format """
        new_data_flag = False
        raw_data = []
        signals_data =[]

        for i in range(MAX_LINE):
             signals_data.append([])

        while not self.data_in_queue.empty():
            new_data_flag = True
            line = self.data_in_queue.get()
            raw_data.append(line)

            # expected bytes are in format: b"s1, s2,.., sn \r\n"
            line_split = line.decode("utf-8").splitlines()[0].split(',') # remove \r\n, split by coma
            nb_sig = len(line_split)
            if(nb_sig == 0):
                break
            if(nb_sig > MAX_LINE):
                logging.warning("Too many signals: {}".format(nb_sig))
                break
            
            i = 0
            for sig in line_split: # iterate over the different signals
                if(i >= MAX_LINE):
                    # max signals reached
                    break

                sigv = sig.strip() # remove leading, trailing spaces if any

                if(check_int(sigv)): # signal must be int, for this implementation
                    signals_data[i].append(int(sigv)) 
                else:
                    logging.info("Not a digit: {}".format(line_split))
                    pass

                i += 1

            self.data_in_queue.task_done() # TODO: is it needed or not ?
        
        return (new_data_flag, raw_data, signals_data)