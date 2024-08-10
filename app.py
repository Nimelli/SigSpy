from settings import MAX_LINE, T_NAME_SERIAL, T_NAME_TCP
from transport.transport import Transport

import time
import logging
import numpy as np

PROC_RATE = 1 # per 60 FPS
FPS = 60

def ts_ms():
    return round(time.time() * 1000)

class MYAPP():
    def __init__(self, dpg) -> None:
        self.dpg = dpg

        self.transport = Transport()

        self.mainloop_cnt = 0
        self.data_processing_cnt = 0
        self.data_processing_run = True

        self.t_start_first = 0
        self.plot_data_x = []
        self.plot_data_y = []
        for i in range(MAX_LINE):
            self.plot_data_y.append([])

        self.log_enabled = False
        self.log_val = ""

    def on_close(self):
        logging.info("Exiting")
        self.transport.close()

    def btn(self, sender, app_data):
        logging.debug(f"sender is: {sender}")
        logging.debug(f"app_data is: {app_data}")

    def clear_all(self):
        # clear signals
        self.plot_data_x = []
        for i in range(MAX_LINE):
            self.dpg.set_value('serial_plot_series_{}'.format(i), [[], []])
            self.plot_data_y[i] = []
            self.dpg.configure_item('stat_sig_{}'.format(i), show=False)

        # clear log
        self.log_val = ""
        self.dpg.set_value("serial_log", self.log_val)
        
    def on_btn_open_port(self, sender, app_data):
        self.clear_all()
        com_port = self.dpg.get_value("com_port_txt").split(':')[0]
        self.transport.close()
        self.transport.select(T_NAME_SERIAL)
        self.transport.open((com_port,))
        self.transport.start()

    def on_btn_open_tcp(self, sender, app_data):
        self.clear_all()
        self.transport.close()
        serv = self.dpg.get_value("tcp_server")
        port = self.dpg.get_value("tcp_port")

        self.transport.select(T_NAME_TCP)
        self.transport.open((serv, port))
        self.transport.start()

    def on_btn_close(self, sender, app_data):
        self.transport.close()

    def on_btn_send_cmd(self, sender, app_data):
        cmd = bytearray()
        cmd_txt = self.dpg.get_value("send_cmd_txt")
        cmd.extend(cmd_txt.encode("utf-8"))
        cmd.extend(b"\r\n")
        self.transport.write(cmd)

    def on_btn_clear_plot(self, sender, app_data):
        self.plot_data_x = []
        for i in range(MAX_LINE):
            self.dpg.set_value('serial_plot_series_{}'.format(i), [[], []])
            self.plot_data_y[i] = []
            self.dpg.configure_item('stat_sig_{}'.format(i), show=False)

        self.dpg.fit_axis_data("x_axis")
        self.dpg.fit_axis_data("y_axis")

    def on_log_toggle(self):
        self.log_enabled = not self.log_enabled
        if(self.log_enabled):
            pass
        else:
            # clear
            self.log_val = ""
        self.dpg.set_value("serial_log", self.log_val)

    def on_btn_clear_log(self, sender, app_data):
        self.log_val = ""
        self.dpg.set_value("serial_log", self.log_val)

    def update_UI_input_data(self, raw_data, signals_data):
        """ update UI element with the received data """
        # append to log
        if(self.log_enabled):
            for line in raw_data:
                self.log_val = self.log_val + line.decode("utf-8")
            self.dpg.set_value("serial_log", self.log_val)

        # add new data in plot data
        for i, sig in enumerate(signals_data):
            self.plot_data_y[i].extend(sig)
            

        if(len(self.plot_data_x) == 0):
            self.t_start_first = ts_ms()

        ts = ts_ms() - self.t_start_first
        self.plot_data_x.append(ts)

        # update UI
        for i in range(MAX_LINE):
            if(len(self.plot_data_y[i]) > 0):
                self.dpg.set_value('serial_plot_series_{}'.format(i), [self.plot_data_x, self.plot_data_y[i]])

        self.dpg.fit_axis_data("x_axis")
        self.dpg.fit_axis_data("y_axis")

    def data_processing(self):
        logging.debug("data processing")

        for i, sig in enumerate(self.plot_data_y):
            if len(sig) > 0:
                npsig = np.array(sig)

                s_min = np.min(npsig)
                s_max = np.max(npsig)
                s_avg = np.mean(npsig)
                s_std = np.std(npsig)
                #logging.debug("{}, {}, {}, {}".format(s_min, s_max, s_avg, s_std))

                # update UI
                self.dpg.configure_item('stat_sig_{}'.format(i), show=True)
                self.dpg.set_value('stat_sig_min_{}'.format(i), "Min: {:.2f}".format(s_min))
                self.dpg.set_value('stat_sig_max_{}'.format(i), "Max: {:.2f}".format(s_max))
                self.dpg.set_value('stat_sig_avg_{}'.format(i), "Avg: {:.2f}".format(s_avg))
                self.dpg.set_value('stat_sig_std_{}'.format(i), "Std: {:.2f}".format(s_std))

    def loop_cnt_update(self):
        """ maintain loop counter and task rate """
        #logging.debug("{}, {}".format(self.mainloop_cnt, self.data_processing_cnt))
        self.mainloop_cnt +=1
        self.data_processing_cnt +=1
        
        if(self.data_processing_cnt >= int(FPS/PROC_RATE)): # run a second time after 30 fps
            self.data_processing_run = True
            self.data_processing_cnt = 0

        
        if(self.mainloop_cnt >= FPS):
            self.mainloop_cnt = 0
            self.data_processing_cnt = 0
            # reset loop run flags
            self.data_processing_run = True
    
    def mainloop(self):
        """ dpk runs at 60FPS, this loop is called as fast """
        (new_data_flag, raw_data, signals_data) = self.transport.get_data_from_input_buf()  
        if(new_data_flag):
            self.update_UI_input_data(raw_data, signals_data)

        if(new_data_flag):
            if(self.data_processing_run): # run once every 30 FPS
                self.data_processing_run = False
                self.data_processing()

                # some debug info
                self.transport.print_debug_info()
        
        self.loop_cnt_update()