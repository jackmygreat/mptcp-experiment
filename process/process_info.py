import psutil
import os
import subprocess


class ProcessOptions(Object):

    def __init__(self):
        self.process_name = ""
        self.process_cwd = "/"
        self.process_command = ""
        self.nice_value = 20
        self.ionice_type_value = (psutil.IOPRIO_CLASS_BE, 3)
        self.cpu_affinity = []
        self.scheduler_type_value = ('', 0)
        
class ProcessInfo(Object):

    def __init__(self, process_id : int, process_options : ProcessOptions):
        self.process_id = process_id
        self.process_options = process_options


