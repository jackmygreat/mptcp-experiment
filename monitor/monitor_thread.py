import threading
import logging
import time
from enum import Enum
from .monitor import MonitorProcess

class MonitorRequestType(str, Enum):
    add = "add"
    delete = "delete"


class MonitorRequest(object):
    def __init__(self, request_type, kwargs):
        self.request_type = request_type
        self.kwargs = kwargs

    def get_monitor_obj(self):
        return self.kwargs["monitor_process"]

    def get_monitor_event(self):
        return self.kwargs["monitor_event"]
    
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
                    self.process_list.append( (request.get_process_id(), request.get_monitor_obj(), request.get_monitor_event()) )
                elif request.request_type == MonitorRequestType.delete:
                    request_id = request.get_process_id()
                    self.process_list = [item for item in self.process_list if item[0] != request_id]
                else:
                    # invalid request type
                    logging.error("Got invalid request type in monitor thread")

            dead_process = []
            for process_info in self.process_list:

                # for each process check if we can start monitoring.
                # this because we have compiler stage and we dont want to start monitoing while we inside compiler stage
                if not process_info[2].is_set():
                    continue

                try:
                    process_info[1].monitor()
                except Exception as e:
                    logging.error("Cannot monitor process. error: %s", e)
                    dead_process.append(process_info[0])
            
            self.process_list = [item for item in self.process_list if item[0] not in dead_process]
            time.sleep(self.sleep_time_in_second)
            
