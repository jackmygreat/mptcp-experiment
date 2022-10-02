#!/usr/bin/python3.7

import argparse
import psutil
import requests
import json
from pydantic import BaseModel
import uuid

from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.web import JsonLexer

# TODO: dublicate
class HelperScriptBody(BaseModel):
    use_script = False
    script_path = ""
    script_use_shell = False
    pass_args = ""

# TODO: dublicate
class ProcessReq(BaseModel):
    process_identity = ""
    process_depend_on = "-1"
    process_name: str
    process_directory: str
    process_binary: str
    process_binary_options = ""
    process_example_name: str
    nice_value = 19
    ionice_type = psutil.IOPRIO_CLASS_BE
    ionice_value = 3
    cpu_affinity = []
    scheduler_type = '-o'
    scheduler_value = 0

    pre_script = HelperScriptBody()
    post_script = HelperScriptBody()

#cc_algorithms = ["cubic", "reno", "vegas", "veno", "illinois", "lia", "olia", "wvegas", "balia", "scalable"]
#cc_algorithms = ["cubic", "lia", "olia", "wvegas", "balia"]
cc_algorithms = ["lia", "olia", "balia"]
#cc_algorithms = ["cubic"]
path_managers = ["fullmesh", "ndiffports"]
#path_managers = ["ndiffports"]
schedulers = ["roundrobin", "default"]
distances = [50, 100, 150]
file_sizes = [250, 500, 1000]
#file_sizes = [1000]

dirs = [
        "/root/playground/ns-3-dce-1",
        "/root/playground/ns-3-dce-2",
        "/root/playground/ns-3-dce-3",
        "/root/playground/ns-3-dce-4",
        "/root/playground/ns-3-dce-5",
        "/root/playground/ns-3-dce-6",
]

def first_scenario(process_example_name : str, process_binary_options : str, pcap_name : str):

    current_dir = 0
    last_depend = ["-1" for i in range(0, len(dirs))]

    tasks = []
    oper = 1
    with open("second_scenario.json", "w+") as f:
        f.write("[\n")

        for cc in cc_algorithms:
            for path_m in path_managers:
                for file_size in file_sizes:
                    for sche in schedulers:
                        for distance in distances:
                                if (cc == 'lia' and path_m == 'fullmesh') or ( (cc=='balia' or cc=='olia') and path_m == 'ndiffports'):
                                        continue

                                process_req = ProcessReq(process_name="", process_directory="", process_binary="", process_example_name="")
                                process_req.process_identity = str(uuid.uuid4())

                                process_req.process_depend_on = last_depend[current_dir % 6]
                                last_depend[current_dir % 6] = process_req.process_identity
                    
                                process_req.process_name = f"{cc}_{path_m}_{sche}_{file_size}MB_{distance}m"

                                process_req.process_directory = dirs[current_dir % 6]
                                process_req.process_binary = "./waf"

                                process_req.process_binary_options = f"{process_binary_options} \"{process_example_name} --ccAlgo={cc} --pathM={path_m} --scheAlgo={sche} --fileSize={file_size} --distance={distance}\""
                                process_req.process_example_name = process_example_name
                    
                                process_req.nice_value = -20 
                                process_req.ionice_type = 1
                                process_req.ionice_value = 0

                                process_req.pre_script.use_script = True
                                process_req.pre_script.script_path = dirs[current_dir % 6] + "/" + "prescript.py"
                                process_req.pre_script.script_use_shell = False
                                process_req.pre_script.pass_args = ""

                                process_req.post_script.use_script = True
                                process_req.post_script.script_path = dirs[current_dir % 6] + "/" + "exper_post_process.py"
                                process_req.post_script.pass_args = f"{cc} {pcap_name}"

                                process_req.scheduler_type = '-r'
                                process_req.scheduler_value = 99

                                tasks.append(process_req.json(indent=4))

                                current_dir += oper
                    oper = -1 * oper
                    current_dir += oper

        f.write(",\n".join(tasks))
        f.write("]")
        
def second_scenario():
    return

def third_scenario():
    return
if __name__ == '__main__':

    ptools_cli = argparse.ArgumentParser(prog="PTools")
    ptools_cli.add_argument("--process-example-name", type=str, required=True)
    ptools_cli.add_argument("--process-binary-options", type=str, required=True)
    ptools_cli.add_argument("--pcap-name", type=str, required=True)

    args = ptools_cli.parse_args()
    first_scenario(args.process_example_name, args.process_binary_options, args.pcap_name)
