import logging
import threading
import psutil
import time
import subprocess

class MonitorProcess(object):

    def __init__(self, process):
        self.recent_first_core_pid = -1
        self.shared_core_pid = []
        self.process_info = process
        self.options = self.process_info.process_options
        self.process_info = process

    def _set_scheduler(self, thread_id : int, process_scheduler_type_value):
        scheduler_type = process_scheduler_type_value[0]
        prio_value = process_scheduler_type_value[1]
        change_scheduler = subprocess.Popen(["chrt", str(scheduler_type), "-p", str(prio_value), str(thread_id)])
        return_code = change_scheduler.wait()
        if return_code != 0:
            logging.error("Could not change scheduler of process %s. scheduler type: %s, scheduler value: %d", self.options.process_name,
                                                                                                                self.options.scheduler_type_value[0],
                                                                                                                self.options.scheduler_type_value[1])

    def _sort_threads_based_on_cpu_usage(self, thread_list : list):
        thread_pids = [thread_info[0] for thread_info in thread_list]
        thread_pids.sort(key=lambda thread_pid : psutil.Process(thread_pid).cpu_percent(interval=None), reverse=True)
        return thread_pids
    
    def _is_system_consistent(self, threads):
        process_desire_nice_value = self.options.nice_value
        process_io_nice_type_value = self.options.ionice_type_value
        process_cpu_affinity = self.options.cpu_affinity
        process_scheduler_type_value = self.options.scheduler_type_value
        
        for thread in threads:
            try:
                nice_value = psutil.Process(thread[0]).nice()
            except Exception as e:
                logging.error("Tried to get nice value of dead thread. process: %s error: %s", self.options.process_name, e)

            if nice_value != process_desire_nice_value:
                logging.info("System is not consistent(%s). because thread with pid %s has different nice value." 
                            "current value: %d, desire value: %d", self.options.process_name, thread[0], nice_value, process_desire_nice_value)
                return False
            
            ionice_value = psutil.Process(thread[0]).ionice()
            if ionice_value[0] != process_io_nice_type_value[0] or ionice_value[1] != process_io_nice_type_value[1]:
                logging.info("System is not consistent(%s). because thread with pid %s has different ionice value or type."
                                                        "current type: %d, current value: %d, desire type: %d, desire value: %d", self.options.process_name, 
                                                        thread[0], ionice_value[0], ionice_value[1],
                            process_desire_nice_value[0], process_desire_nice_value[1])
                return False
            
            sorted_thread_list = self._sort_threads_based_on_cpu_usage(threads)
            if psutil.Process(sorted_thread_list[0]).cpu_affinity()[0] != process_cpu_affinity[0]:
                logging.info("System is not consistent(%s). because thread with pid %s has different affinity."
                        "first cpu should be for %d but it's for %d. cpu affinity: %d", self.options.process_name, thread[0], self.recent_first_core_pid, sorted_thread_list[0],
                                process_cpu_affinity[0])
                return False

            sorted_thread_list = sorted_thread_list[1:]
            for thread_pid in sorted_thread_list:
                if psutil.Process(thread_pid).cpu_affinity()[0] != process_cpu_affinity[1]:
                    logging.info("System is not consistent(%s). because shared thread with pid %d has diffrent cpu affinity. cpu affinity: %d", self.options.process_name, thread_pid,
                                        process_cpu_affinity[1])
                    return False
        
        logging.debug("System is consistent(%s)", self.options.process_name)
        return True

    def monitor(self):
        process_name = self.options.process_name
        process_cwd = self.options.process_cwd
        process_desire_nice_value = self.options.nice_value
        process_io_nice_type_value = self.options.ionice_type_value
        process_cpu_affinity = self.options.cpu_affinity
        process_scheduler_type_value = self.options.scheduler_type_value
        
        process = None

        # find process based on example name and process directory
        for proc in psutil.process_iter():
            if self.process_info.process_options.process_example_name in proc.name() and \
                self.process_info.process_options.process_directory in proc.cwd():
                    process = proc
                    break

        threads = process.threads()

        # check if system consistent
        if self._is_system_consistent(threads):
            return
    
        # set general settings
        for thread in threads:
            try:
                psutil.Process(thread[0]).nice(process_desire_nice_value)
                psutil.Process(thread[0]).ionice(process_io_nice_type_value[0], process_io_nice_type_value[1])
                self._set_scheduler(thread[0], process_scheduler_type_value)
            except Exception as e:
                logging.warning("Tried to set nice value for dead thread. process: %s error: %s", self.options.process_name, e)
        # set specific settings
        threads = process.threads()
        sorted_thread_list = self._sort_threads_based_on_cpu_usage(threads)

        # set most active cpu to first core
        psutil.Process(sorted_thread_list[0]).cpu_affinity([process_cpu_affinity[0]])
        self.recent_first_core_pid = sorted_thread_list[0]
            
        # set all other thread on another core
        self.shared_core_pid = []
        if len(sorted_thread_list) > 1:
            sorted_thread_list = sorted_thread_list[1:]
            for thread_pid in sorted_thread_list:
                try:
                    psutil.Process(thread_pid).cpu_affinity([process_cpu_affinity[1]])
                    self.shared_core_pid.append(thread_pid)
                except Exception as e:
                    logging.warning("Tried to set cpu affinity for dead thread. process: %s error: %s", self.options.process_name, e)

