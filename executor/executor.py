import threading
import time
import logging
import subprocess
import os

class Executor(Object):

    def __init__(self, process_info, output_path : str):
        self.process_info = process_info
        self.process = None
        self.output_path = output_path

    def run(self):
        # change directory to give path
        if self.process_info.process_options.process_directory == None:
            logging.info("Process directory does not specified")
        else:
            os.chdir(self.process_info.process_options.process_directory)

        # run and get process
        self.process = subprocess.Popen([self.process_info.process_options.process_binary,
            slef.process_binary_options],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines=True)

    def write_output(self):
        with open(self.output_path + "/" +
                        f"{self.process_info.process_options.process_name}-time", "w+") as f:
                
            while True:
                output = self.process.stdout.readline()
                f.write(output.strip() + "\n")

                return_code = self.process.poll()

                # process finished
                if return_code is not None:

                    # process faced error
                    if return_code != 0:
                        for output in self.process.stdout.readlines():
                            f.write(output.strip() + "\n")
                        logging.error("Process faced error: %s", self.process.stderr.readlines())
                        for output in self.process.stderr.readlines():
                            f.write(output.strip() + "\n")
                    else: # exited normally
                        for output in process.stdout.readlines():
                            f.write(output.strip() + "\n")

                    return return_code




        