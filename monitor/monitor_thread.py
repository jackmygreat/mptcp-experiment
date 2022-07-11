import threading
import logging
import time
from enum import Enum
from .monitor import MonitorProcess
import traceback
import math

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
        self.minimum_number_of_consecutive_consistency = self.kwargs.get("minimum_number_of_consecutive_consistency", 20)
        self.maximum_sleep_factor = self.kwargs.get("maximum_sleep_factor", 6)
        self.process_list = []

    def _sleep_based_on_consistency(self):
        factor = 0

        if self.number_consecutive_consistency > self.minimum_number_of_consecutive_consistency:
            factor = self.number_consecutive_consistency - self.minimum_number_of_consecutive_consistency
            if factor > self.maximum_sleep_factor:
                factor = self.maximum_sleep_factor

        time.sleep(math.pow(2, factor) * self.sleep_time_in_second)

    def run(self):
        # loop for ever

        self.number_consecutive_consistency = 0
        while True:
            local_consistency = True
            
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
                    is_consistent = process_info[1].monitor()
                    if is_consistent != True:
                        is_consistent = False
                    local_consistency = local_consistency and is_consistent
                except Exception as e:
                    print(traceback.format_exc())
                    logging.error("Cannot monitor process id %d. error: %s", process_info[0], e)
                    dead_process.append(process_info[0])

            if local_consistency:
                self.number_consecutive_consistency += 1
            else:
                self.number_consecutive_consistency = 0

            # delete dead process from monitor list
            self.process_list = [item for item in self.process_list if item[0] not in dead_process]
            self._sleep_based_on_consistency()
