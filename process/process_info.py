import psutil
import os
import subprocess
import json
import time
import datetime

class HelperScript(object):

    def __init__(self):
        self.use_script = False
        self.script_path = ""
        self.script_use_shell = False

    def toJSON(self): 
        return json.dumps(self, default= lambda o: o.__dict__, sort_keys=True, indent=4)

class ProcessOptions(object):

    def __init__(self):
        self.process_name = ""
        self.process_cwd = "/"
        self.process_directory = None
        self.process_binary = None
        self.process_pid = -1
        self.process_binary_options = ""
        self.process_example_name = ""
        self.process_start_time = datetime.datetime.now()
        self.process_end_time = "-"
        self.process_running_time = "-"
        self.nice_value = 20
        self.ionice_type_value = (psutil.IOPRIO_CLASS_BE, 3)
        self.cpu_affinity = []
        self.scheduler_type_value = ('', 0)
        self.start_monitoring_str = "here"

        self.pre_execute_script = HelperScript()
        self.post_execute_script = HelperScript()

    def is_valid(self):
        if len(self.process_name) == 0:
            return False

        if self.process_binary == None:
            return False

        return True

    def times_to_string(self):
        self.process_start_time = str(self.process_start_time)
        self.process_end_time = str(self.process_end_time)
        self.process_running_time = str(self.process_running_time)

    def toJSON(self):
        self.times_to_string()
        return json.dumps(self, default= lambda o: o.__dict__, sort_keys=True, indent=4)


class ProcessInfo(object):

    def __init__(self, process_id : int, process_options : ProcessOptions):
        self.process_id = process_id
        self.process_options = process_options

    def is_valid(self):
        return self.process_options.is_valid()

    def toJSON(self):
        self.process_options.times_to_string()
        return json.dumps(self, default= lambda o: o.__dict__, sort_keys=True, indent=4)

