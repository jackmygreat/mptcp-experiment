import threading
import logging
import time
from enum import Enum
from . import MonitorProcess

class MonitorRequestType(str, Enum):
    add = "add"
    delete = "delete"


class MonitorRequest(Object)
    def __init__(self, request_type, kwargs):
        self.request_type = request_type
        self.kwargs = kwargs

    def get_monitor_obj(self):
        return self.kwargs["monitor_process"]
    
    def get_process_id(self):
        return self.kwargs["process_id"]


class MonitorThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
		super(MonitorThread, self).__init__(group=group, target=target, name=name)

		self.args = args
		self.kwargs = kwargs
        self.queue = self.kwargs["queue"]
        self.sleep_time_in_second = self.kwargs["sleep_time_in_second"]
        self.process_list = []

    def run(self):
        # loop for ever
        while True:

            # get all requests in queue
            if not self.queue.empty():
                request = self.queue.get()

                if request.request_type == MonitorRequestType.add:
                    self.process_list.append( (request.get_process_id(), request.get_monitor_obj()) )
                elif request.request_type == MonitorRequestType.delete:
                    request_id = request.get_process_id()
                    self.process_list = [item for item in self.process_list if item[0] != request_id]
                else:
                    # invalid request type
                    logging.error("Got invalid request type in monitor thread")

            for process_info in self.process_list:
                process_info[0].monitor()

            time.sleep(self.sleep_time_in_second)
            


                


        
