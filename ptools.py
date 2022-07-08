#!/usr/bin/python3

import logging
import threading
import psutil
import time
import subprocess

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)

class MonitorThread(threading.Thread):

	def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
		super(MonitorThread, self).__init__(group=group, target=target, name=name)

		self.args = args
		self.kwargs = kwargs
		self.recent_first_core_pid = -1

	def _set_scheduler(self, thread_id : int, process_scheduler_type_value):
		scheduler_type = process_scheduler_type_value[0]
		prio_value = process_scheduler_type_value[1]
		change_scheduler = subprocess.Popen(["chrt", str(scheduler_type), "-p", str(prio_value), str(thread_id)])
		return_code = change_scheduler.wait()
		if return_code != 0:
			logging.error("Could not change scheduler.")

	def _sort_threads_based_on_cpu_usage(self, thread_list : list):
		thread_pids = [thread_info[0] for thread_info in thread_list]
		thread_pids.sort(key=lambda thread_pid : psutil.Process(thread_pid).cpu_percent(interval=None), reverse=True)
		return thread_pids
	
	def _is_system_consistent(self, threads):
		process_desire_nice_value = self.kwargs["nice_value"]
		process_io_nice_type_value = self.kwargs["ionice_type_value"]
		process_cpu_affinity = self.kwargs["affinity_values"]
		process_scheduler_type_value = self.kwargs["scheduler_type_value"]
		
		for thread in threads:
			nice_value = psutil.Process(thread[0]).nice()
			if nice_value != process_desire_nice_value:
				logging.info("System is not consistent. because thread with pid %s has different nice value." 
							"current value: %d, desire value: %d", thread[0], nice_value, process_desire_nice_value)
				return False
			
			ionice_value = psutil.Process(thread[0]).ionice()
			if ionice_value[0] != process_io_nice_type_value[0] or ionice_value[1] != process_io_nice_type_value[1]:
				logging.info("System is not consistent. because thread with pid %s has different ionice value or type."
                                                        "current type: %d, current value: %d, desire type: %d, desire value: %d", thread[0], ionice_value[0], ionice_value[1],
							process_desire_nice_value[0], process_desire_nice_value[1])
				return False
			
			sorted_thread_list = self._sort_threads_based_on_cpu_usage(threads)
			if sorted_thread_list[0] != self.recent_first_core_pid:
				logging.info("System is not consistent. because thread with pid %s has different affinity."
						"first cpu should be for %d but it's for %d", thread[0], self.recent_first_core_pid, sorted_thread_list[0])
				return False
		
		logging.debug("System is consistent")
		return True

	def run(self):
		process_name = self.kwargs["process_name"]
		process_cwd = self.kwargs["process_cwd"]
		process_desire_nice_value = self.kwargs["nice_value"]
		process_io_nice_type_value = self.kwargs["ionice_type_value"]
		process_cpu_affinity = self.kwargs["affinity_values"]
		process_scheduler_type_value = self.kwargs["scheduler_type_value"]
		
		while True:
			for process in psutil.process_iter():
				# found our process!
				if process_name in process.name() and process_cwd in process.cwd():
					logging.debug("Found process with name: %s and with current working directory: %s", process.name(), process.cwd())
					threads = process.threads()
					
					# check if system consistent
					if self._is_system_consistent(threads):
						break
	
					# set general settings
					for thread in threads:
						psutil.Process(thread[0]).nice(process_desire_nice_value)
						psutil.Process(thread[0]).ionice(process_io_nice_type_value[0], process_io_nice_type_value[1])
						self._set_scheduler(thread[0], process_scheduler_type_value)
					
					# set specific settings
					threads = process.threads()
					sorted_thread_list = self._sort_threads_based_on_cpu_usage(threads)

					# set most active cpu to first core
					psutil.Process(sorted_thread_list[0]).cpu_affinity([process_cpu_affinity[0]])
					self.recent_first_core_pid = sorted_thread_list[0]
						
					# set all other thread on another core
					if len(sorted_thread_list) > 1:
						sorted_thread_list = sorted_thread_list[1:]
						for thread_pid in sorted_thread_list:
							psutil.Process(thread_pid).cpu_affinity([process_cpu_affinity[1]])	
			time.sleep(1000)


def monitor_process(name: str):
	while True:
		for proc in psutil.process_iter():
			# print(proc.pid)
			if name in proc.name():
				print(str(proc.pid) + " " + proc.name())
				print(proc.threads())
		time.sleep(10)


if __name__=="__main__":
	print(psutil.pid_exists(1411))
	print(psutil.Process(55382).children())
	x = MonitorThread(args=(), kwargs={
		'process_name': 'mmwave',
		'process_cwd': 'dce',
		'nice_value': -20,
		'ionice_type_value': (psutil.IOPRIO_CLASS_RT, 0),
		'affinity_values': (0, 1),
		'scheduler_type_value': ('--rr', 99)
	})
	x.start()
	x.join()
