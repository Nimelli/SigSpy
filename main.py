import dearpygui.dearpygui as dpg
import logging
logging.basicConfig(level=logging.DEBUG)

from serialManager import SerialProc
from queue import Queue
import time
import numpy as np
    
MAX_LINE = 10

def ts_ms():
    return round(time.time() * 1000)

def check_int(s):
    if len(s) <= 0:
        logging.error(s)
        return False
    
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

class MYAPP():
    def __init__(self, dpg) -> None:
        self.dpg = dpg

        self.data_in_queue = Queue() # host in
        self.data_out_queue = Queue() # host out
        self.serProc = SerialProc(self.data_in_queue, self.data_out_queue)
        self.serProc.start()

        self.t_start_first = 0
        self.plot_data_x = []
        self.plot_data_y = []
        for i in range(MAX_LINE):
            self.plot_data_y.append([])

    def on_close(self):
        logging.info("Exiting")
        self.serProc.close()

    def btn(self, sender, app_data):
        logging.debug(f"sender is: {sender}")
        logging.debug(f"app_data is: {app_data}")
    
        
    def on_btn_open_port(self, sender, app_data):
        com_port = self.dpg.get_value("com_port_txt")
        self.serProc.open(com_port.split(':')[0]) # open
        self.serProc.start()

    def on_btn_close_port(self, sender, app_data):
        self.serProc.close()

    def on_btn_send_cmd(self, sender, app_data):
        print('cmd')
        self.data_out_queue.put(b'test cmd\r\n')

    def on_btn_clear_plot(self, sender, app_data):
        self.plot_data_x = []
        for i in range(MAX_LINE):
            self.dpg.set_value('serial_plot_series_{}'.format(i), [[], []])
            self.plot_data_y[i] = []

        self.dpg.fit_axis_data("x_axis")
        self.dpg.fit_axis_data("y_axis")
    
    def mainloop(self):
        
        # serial get data
        new_data = False
        data_in = []
        for i in range(MAX_LINE):
             data_in.append([])

        while not self.data_in_queue.empty():
            new_data = True
            row = self.data_in_queue.get()

            row_split = row.decode("utf-8").splitlines()[0].split(',') # remove trailing /r/n, remove heading space, split by coma
            
            i = 0
            for s in row_split:
                d = s.lstrip() # remove heading space
                if(check_int(d)):
                    data_in[i].append(int(d)) # signal must be int
                else:
                    logging.info("Not a digit: {}".format(row_split))
                    break
                i += 1

            #self.data_in_queue.task_done()

        # process data
        if(new_data):

            i=0
            for s in data_in:
                self.plot_data_y[i].extend(s)
                i += 1

            if(len(self.plot_data_x) == 0):
                self.t_start_first = ts_ms()

            ts = ts_ms() - self.t_start_first
            self.plot_data_x.append(ts)

            for i in range(MAX_LINE):
                if(len(self.plot_data_y[i]) > 0):
                    self.dpg.set_value('serial_plot_series_{}'.format(i), [self.plot_data_x, self.plot_data_y[i]])

            self.dpg.fit_axis_data("x_axis")
            self.dpg.fit_axis_data("y_axis")


    


# UI
dpg.create_context()
myApp = MYAPP(dpg)
dpg.set_exit_callback(myApp.on_close)



with dpg.window(label="Serial Port", tag="win"):
    all_ports = SerialProc.list_port()
    logging.debug(all_ports)
    dpg.add_combo(all_ports, label="COM Port", tag="com_port_txt")
    #dpg.add_input_text(label="COM Port", tag="com_port_txt")
    dpg.add_button(label="Open Port", callback=myApp.on_btn_open_port, tag="open_port")
    dpg.add_button(label="Close Port", callback=myApp.on_btn_close_port, tag="close_port")

    dpg.add_button(label="Send cmd", callback=myApp.on_btn_send_cmd, tag="send_cmd")
    # create plot

with dpg.window(label="Plot", tag="plotwin"):
    # create plot
    with dpg.plot(label="Line Series", height=400, width=800):
        # optionally create legend
        dpg.add_plot_legend()

        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

        dpg.set_axis_limits_auto("x_axis")
        dpg.set_axis_limits_auto("y_axis")

        # series belong to a y axis
        for i in range(MAX_LINE):
            dpg.add_line_series([], [], parent="y_axis", tag="serial_plot_series_{}".format(i))

    dpg.add_button(label="Clear", callback=myApp.on_btn_clear_plot, tag="clear_plot")

dpg.set_item_pos("plotwin", [200, 0])

# debug usefull
#dpg.show_documentation()
#dpg.show_style_editor()
dpg.show_debug()
#dpg.show_about()
dpg.show_metrics()
#dpg.show_font_manager()
dpg.show_item_registry()



dpg.create_viewport(title='Custom Title', width=1200, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()

# below replaces, start_dearpygui()

# start_time = time.time()
# fpsCounter = 0
while dpg.is_dearpygui_running():
    

    # Use dpg.show_metrics() instead
    # fpsCounter += 1
    # if (time.time() - start_time) > 1 : # print every second
    #     print("FPS: ", fpsCounter / (time.time() - start_time))
    #     fpsCounter = 0
    #     start_time = time.time()

    myApp.mainloop()

    dpg.render_dearpygui_frame()

dpg.destroy_context()