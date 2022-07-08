import psutil
import os
import subprocess


class ProcessOptions(object):

    def __init__(self):
        self.process_name = ""
        self.process_cwd = "/"
        self.process_directory = None
        self.process_binary = None
        self.process_pid = -1
        self.process_binary_options = ""
        self.process_example_name = ""
        self.nice_value = 20
        self.ionice_type_value = (psutil.IOPRIO_CLASS_BE, 3)
        self.cpu_affinity = []
        self.scheduler_type_value = ('', 0)
        self.start_monitoring_str = "here"

    def is_valid(self):
        if len(self.process_name) == 0:
            return False

        if self.process_binary == None:
            return False

        return True

class ProcessInfo(object):

    def __init__(self, process_id : int, process_options : ProcessOptions):
        self.process_id = process_id
        self.process_options = process_options

    def is_valid(self):
        return self.process_options.is_valid()


