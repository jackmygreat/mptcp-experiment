import threading
import time
import logging
import subprocess
import os
import psutil
import copy

class Executor(object):

    def __init__(self, process_info, output_path : str, monitor_event : threading.Event):
        self.process_info = process_info
        self.process = None
        self.output_path = output_path
        self.sent_signal_to_monitor_thread = False
        self.monitor_event = monitor_event
        self.output = []

    def _pre_execute_script(self):
        helper_script = self.process_info.process_options.pre_execute_script
        
        process_info = copy.deepcopy(self.process_info)
        pre_execute_script_process = subprocess.Popen([helper_script.script_path, str(process_info.toJSON())],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                universal_newlines = True,
                shell = helper_script.script_use_shell)

        return_code = pre_execute_script_process.wait()
        if return_code != 0:
            logging.error("Pre execute script faild. process: %s, error: %s", self.process_info.process_options.process_name, 
                                     pre_execute_script_process.stderr.readlines())

    def _post_execute_script(self):
        helper_script = self.process_info.process_options.post_execute_script

        post_execute_script_process = subprocess.Popen([helper_script.script_path, str(self.process_info.toJSON())],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                universal_newlines = True,
                shell = helper_script.script_use_shell)

        return_code = post_execute_script_process.wait()
        if return_code != 0:
            logging.error("Post execute script faild. process: %s, error: %s", self.process_info.process_options.process_name, 
                                     post_execute_script_process.stderr.readlines())

    def run(self):
        # change directory to give path
        if self.process_info.process_options.process_directory == None:
            logging.info("Process directory is None. process: %s", self.process_info.process_options.process_name)
        else:
            os.chdir(self.process_info.process_options.process_directory)

        # If we have pre execute script. here is the right place to execute it.
        if self.process_info.process_options.pre_execute_script.use_script:
            self._pre_execute_script()

        # run and get process
        self.process = subprocess.Popen([self.process_info.process_options.process_binary] + 
                self.process_info.process_options.process_binary_options.split(" "),
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines=True)

        return self.process.pid

    def terminate(self):
        parent_pid = self.process.pid

        try:
            parent_process = psutil.Process(parent_pid)

            for child in parent_process.children():
                try:
                    child.kill()
                except Exception as e:
                    logging.error("Failed to terminate process %s child. error: %s", self.process_info.process_options.process_name, e)

            parent_process.kill()
        except Exception as error:
            logging.error("Failed to terminate process %s. error: %s", self.process_info.process_options.process_name, e)
            return False

        return True

    def get_output(self):
        return self.output

    def _write_output(self):
        with open(self.output_path + "/" +
                        f"{self.process_info.process_options.process_name}-output.txt", "w+") as f:

            while True:
                output = self.process.stdout.readline()
                f.write(output.strip() + "\n")
                f.flush()
                self.output.append(output.strip())

                # check if we sent signal beforce and check if we saw string for start monitoring
                if not self.sent_signal_to_monitor_thread and self.process_info.process_options.start_monitoring_str in output.strip():
                    self.monitor_event.set()

                return_code = self.process.poll()

                # process finished
                if return_code is not None:

                    # process faced error
                    if return_code != 0:
                        for output in self.process.stdout.readlines():
                            f.write(output.strip() + "\n")
                        logging.error("Process %s faced error: %s", self.process_info.process_options.process_name, self.process.stderr.readlines())
                        for output in self.process.stderr.readlines():
                            f.write(output.strip() + "\n")
                    else: # exited normally
                        for output in self.process.stdout.readlines():
                            f.write(output.strip() + "\n")

                    # if we have post execute script. here is the right place to execute it.
                    if self.process_info.process_options.post_execute_script.use_script:
                        self._post_execute_script()

                    return return_code

    def get_write_output_thread(self):
        return threading.Thread(name=f"{self.process_info.process_options.process_name}-output-thread", target=self._write_output, args=())

