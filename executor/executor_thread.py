import time
import logging
import math
import psutil
import threading

from monitor.monitor_thread import *
from monitor.monitor import *
from .executor import Executor

class ExecutorThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ExecutorThread, self).__init__()

        self.target = target
        self.name = name
        self.args = args
        self.kwargs = kwargs

        self.process_queue = self.kwargs["process_queue"]
        self.process_outputs = self.kwargs["process_outputs"]
        self.process_monitor_queue = self.kwargs["process_monitor_queue"]
        self.loop_time = self.kwargs["executor_thread_loop_time"]

        self.running_threads = []
        self.cpu_counts = psutil.cpu_count()
        self.max_shared_process_per_cpu = 3
        self.maximum_number_of_shared_process = math.ceil(psutil.cpu_count() / 4)
        self.running_shared_process_on_cpus = [(i, 0) for i in range(self.cpu_counts - 1, self.cpu_counts - 1 - self.maximum_number_of_shared_process, -1)]
        self.running_process_on_cpus = [(i, 0) for i in range(0, self.cpu_counts - self.maximum_number_of_shared_process)]

    def get_all_running_process(self):
        return [thread_info[0] for thread_info in self.running_threads]

    def get_process_info_by_process_id(self, process_id : int):
        process = [thread_info[0] for thread_info in self.running_threads if thread_info[0].process_id == process_id]
        if len(process) > 0:
            return process[0]
        return None

    def get_process_output_by_id(self, process_id : int): 
        executor = [thread_info[2] for thread_info in self.running_threads if thread_info[0].process_id == process_id]
        if len(executor) > 0:
            return executor[0].get_output()
        return None
    
    def run(self):
        while True:
            # check if we have enough core for running program and if we have process in queue
            if len(self.running_threads) < self.cpu_counts - self.maximum_number_of_shared_process and not self.process_queue.empty():
                new_process = self.process_queue.get()

                if not new_process.is_valid():
                    logging.error("Submitted process does not have valid options, therefore discard process. process: %s", new_process.process_options.process_name)
                    continue

                # assign cpu's if cpu affinity option is empty
                if len(new_process.process_options.cpu_affinity) == 0:
                    first_cpu_index = next((index, cpu) for index, cpu in enumerate(self.running_process_on_cpus) if cpu[1] == 0)
                    first_cpu, index = first_cpu_index[1], first_cpu_index[0]
                    self.running_process_on_cpus[index] = (first_cpu[0], first_cpu[1] + 1)

                    shared_cpu_index, shared_cpu = min(enumerate(self.running_shared_process_on_cpus), key=lambda x: x[1][1])
                    self.running_shared_process_on_cpus[shared_cpu_index] = (shared_cpu[0], shared_cpu[1] + 1)

                    new_process.process_options.cpu_affinity = [first_cpu[0], shared_cpu[0]]

                # comminucate between executor and monitor thread for notify monitor that he can start monitoring
                event = threading.Event()
                executor = Executor(new_process, self.process_outputs, event)
                process_pid = executor.run()
                new_process.process_options.process_pid = process_pid

                # spawn a new thread for writing output
                thread = executor.get_write_output_thread()
                thread.start()
                self.running_threads.append( (new_process, thread, executor) )

                # create monitor request and send to monitor thread
                monitor_obj = MonitorProcess(new_process) 
                monitor_req = MonitorRequest(MonitorRequestType.add, {
                    "monitor_process": monitor_obj,
                    "process_id": new_process.process_id,
                    "monitor_event": event
                })
                
                #we should put large number for queue size
                self.process_monitor_queue.put(monitor_req)

                continue

            dead_threads_index = []
            for index, thread_info in enumerate(self.running_threads):
                if not thread_info[1].is_alive():
                    process_info = thread_info[0]
                    first_cpu = process_info.process_options.cpu_affinity[0]
                    shared_cpu = process_info.process_options.cpu_affinity[1]

                    # free cpus from list
                    first_cpu_index = [(x, y[1]) for x, y in enumerate(self.running_process_on_cpus) if y[0] == first_cpu][0]
                    shared_cpu_index = [(x, y[1]) for x, y in enumerate(self.running_shared_process_on_cpus) if y[0] == shared_cpu][0]

                    self.running_process_on_cpus[first_cpu_index[0]] = (first_cpu, first_cpu_index[1] - 1)
                    self.running_shared_process_on_cpus[shared_cpu_index[0]] = (shared_cpu, shared_cpu_index[1] - 1)

                    monitor_req = MonitorRequest(MonitorRequestType.delete, {
                        "process_id": process_info.process_id
                    })

                    # clean from monitor thread
                    self.process_monitor_queue.put(monitor_req)
                    dead_threads_index.append(index)
            
            # delete dead threads
            self.running_threads = [thread_info for index, thread_info in enumerate(self.running_threads) if index not in dead_threads_index]
            
            time.sleep(self.loop_time)

