import psutil
import os
import subprocess
import json
import time
import datetime
import uuid

class HelperScript(object):

    def __init__(self):
        self.use_script = False
        self.script_path = ""
        self.script_use_shell = False
        self.pass_args = ""

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
        self.captured_kv_str = "capture"

        self.process_output_dir = ""

        self.pre_execute_script = HelperScript()
        self.post_execute_script = HelperScript()

    def is_valid(self):
        if len(self.process_name) == 0:
            return False

        if self.process_binary == None:
            return False

        return True

    def set_time_tuple(self, time_tuple):
        self.process_start_time = time_tuple[0]
        self.process_end_time = time_tuple[1]
        self.process_running_time = time_tuple[2]

    def get_time_tuple(self):
        return (self.process_start_time, self.process_end_time, self.process_running_time)
    
    def times_to_string(self):
        self.process_start_time = str(self.process_start_time)
        self.process_end_time = str(self.process_end_time)
        self.process_running_time = str(self.process_running_time)

    def toJSON(self):
        time_tuple = self.get_time_tuple()
        self.times_to_string()
        json_result = json.dumps(self, default= lambda o: o.__dict__, sort_keys=True, indent=4)
        self.set_time_tuple(time_tuple)
        return json_result


class ProcessInfo(object):

    def __init__(self, process_id : int, process_options : ProcessOptions):
        self.process_id = process_id
        self.process_options = process_options
        self.process_identity = uuid.uuid4()
        self.process_depend_on = "-1"

    def is_valid(self):
        return self.process_options.is_valid()

    def toJSON(self):
        time_tuple = self.process_options.get_time_tuple()
        self.process_options.times_to_string()
        self.process_identity = str(self.process_identity)
        json_result = json.dumps(self, default= lambda o: o.__dict__, sort_keys=True, indent=4)
        self.process_options.set_time_tuple(time_tuple)
        return json_result


