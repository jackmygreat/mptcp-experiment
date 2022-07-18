import time
import logging
import math
import psutil
import threading
import datetime
import json
import math
import subprocess

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

        self.minimum_number_of_consective_live = self.kwargs.get("minimum_number_of_consective_live", 30)
        self.maximum_number_of_factor = self.kwargs.get("maximum_number_of_factor", 5) 

        self.running_threads = []
        self.cpu_counts = psutil.cpu_count()
        self.max_shared_process_per_cpu = 3
        self.maximum_number_of_shared_process = math.ceil(psutil.cpu_count() / 4)
        self.running_shared_process_on_cpus = [(i, 0) for i in range(self.cpu_counts - 1, self.cpu_counts - 1 - self.maximum_number_of_shared_process, -1)]
        self.running_process_on_cpus = [(i, 0) for i in range(0, self.cpu_counts - self.maximum_number_of_shared_process)]

        self.last_event = None
        self.finished_process = []

    def get_all_running_process(self):
        processs = [thread_info[0] for thread_info in self.running_threads]
        for process in processs:
            process.process_options.process_running_time = (datetime.datetime.now() - process.process_options.process_start_time).seconds / 60.0

        return processs

    def get_process_info_by_process_id(self, process_id : int):
        process = [thread_info[0] for thread_info in self.running_threads if thread_info[0].process_id == process_id]
        if len(process) > 0:
            process[0].process_options.process_running_time = (datetime.datetime.now() - process[0].process_options.process_start_time).seconds / 60.0
            return process[0]
        return None

    def get_process_output_by_id(self, process_id : int): 
        executor = [thread_info[2] for thread_info in self.running_threads if thread_info[0].process_id == process_id]
        if len(executor) > 0:
            return executor[0].get_output()
        return None

    def terminate_process_by_id(self, process_id: int):
        threads_info = [thread_info for thread_info in self.running_threads if thread_info[0].process_id == process_id]

        if len(threads_info) > 0:
            executor = threads_info[0][2]
            process_info = threads_info[0][0]

            status = executor.terminate()
            self.finished_process.append(process_info.process_identity)
            return status

        return False

    def _sleep_based_on_factor(self):
        factor = 0

        if self.number_of_consecutive_live_process > self.minimum_number_of_consective_live:
            factor = self.number_of_consecutive_live_process - self.minimum_number_of_consective_live
            if factor > self.maximum_number_of_factor:
                factor = self.maximum_number_of_factor

        time.sleep(math.pow(2, factor) * self.loop_time)

    def _can_run_process(self, process_info):
        if process_info.process_depend_on != "-1" and process_info.process_depend_on not in self.finished_process:
            return False
        return True

    def _check_process_liveness(self, local_live):
        dead_threads_index = []

        if len(self.running_threads) == 0:
            local_live = False

        for index, thread_info in enumerate(self.running_threads):
            local_live = local_live and thread_info[1].is_alive()
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

                process_info.process_options.process_end_time = datetime.datetime.now()
                process_info.process_options.process_running_time = (process_info.process_options.process_end_time - process_info.process_options.process_start_time).seconds / 60.0
                with open(process_info.process_options.process_output_dir + "/" + f"{process_info.process_options.process_name}-info.txt", "w+") as f:
                    f.write(process_info.toJSON())

                self.finished_process.append(process_info.process_identity)

                thread_info[3].set()

        if local_live:
            self.number_of_consecutive_live_process += 1
        else:
            self.number_of_consecutive_live_process = 0

        # delete dead threads
        self.running_threads = [thread_info for index, thread_info in enumerate(self.running_threads) if index not in dead_threads_index]


    def run(self):
        self.number_of_consecutive_live_process = 0
        while True:
            logging.info("i am running")

            local_live = True
            # check if we have enough core for running program and if we have process in queue
            # if last event is None we are good to go, because there is no process in compile stage
            # if last event is set we are also good to go, because previous running process finished his compile stage and moved one to monitor stage
            if self.last_event != None and self.last_event.is_set():
                self.last_event = None

            if len(self.running_threads) < self.cpu_counts - self.maximum_number_of_shared_process and not self.process_queue.empty() and \
                                        (self.last_event == None or self.last_event.is_set() ):
                new_process = self.process_queue.get()

                # we should not sleep here
                if not self._can_run_process(new_process):
                    self.process_queue.put(new_process)
                    self._check_process_liveness(local_live)
                    self._sleep_based_on_factor()
                    continue

                # clear last event
                self.last_event = None

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

                # store last event in order to find out when we should start the new task
                self.last_event = event

                # generate process output dir
                new_process_output = self.process_outputs + "/" + new_process.process_options.process_name
                subprocess.run(f"mkdir -p {new_process_output}", shell=True)
                new_process.process_options.process_output_dir = new_process_output

                executor = Executor(new_process, new_process_output, event)
                process_pid = executor.run()
                new_process.process_options.process_pid = process_pid

                # spawn a new thread for writing output
                thread = executor.get_write_output_thread()
                thread.start()
                self.running_threads.append( (new_process, thread, executor, event) )

                # create monitor request and send to monitor thread
                monitor_obj = MonitorProcess(new_process) 
                monitor_req = MonitorRequest(MonitorRequestType.add, {
                    "monitor_process": monitor_obj,
                    "process_id": new_process.process_id,
                    "monitor_event": event
                })

                #we should put large number for queue size
                self.process_monitor_queue.put(monitor_req)
                self.number_of_consecutive_live_process = 0
                continue

            self._check_process_liveness(local_live)
            self._sleep_based_on_factor()

