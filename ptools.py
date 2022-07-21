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

def colorful_json(json_str: str):
    return highlight(
        json_str,
        lexer=JsonLexer(),
        formatter=Terminal256Formatter(),
    )

def add_process_handler(args):
    process_req = ProcessReq(process_name="", process_directory="", process_binary="", process_example_name="")
    process_req.process_identity = str(args.process_identity)
    process_req.process_depend_on = args.process_depend_on
    process_req.process_name = args.process_name
    process_req.process_directory = args.process_directory
    process_req.process_binary = args.process_binary
    process_req.process_binary_options = args.process_binary_options
    process_req.process_example_name = args.process_sub_program
    process_req.nice_value = args.nice_value
    process_req.ionice_type = args.ionice_type
    process_req.ionice_value = args.ionice_value

    if args.prescript_path != "":
        process_req.pre_script.use_script = True
        process_req.pre_script.script_path = args.prescript_path
        process_req.pre_script.script_use_shell = args.prescript_shell
        process_req.pre_script.pass_args = args.prescript_args

    if args.postscript_path != "":
        process_req.post_script.use_script = True
        process_req.post_script.script_path = args.postscript_path
        process_req.post_script.script_use_shell = args.postscript_shell
        process_req.post_script.pass_args = args.postscript_args

    cpus = [cpu for cpu in args.cpus.split(",")]
    if len(cpus) > 0 and cpus[0] != '':
        process_req.cpu_affinity = [int(cpu) for cpu in cpus]
    else:
        process_req.cpu_affinity = []
    process_req.scheduler_type = '-' + args.scheduler_type
    process_req.scheduler_value = args.scheduler_value

    if args.v:
        raw_json = process_req.json(indent=4)
        print("<" * 40)
        print(colorful_json(raw_json))

    response = requests.post("http://127.0.0.1:8080/process-queue/add", json=json.loads(process_req.json()), headers={"Content-Type": "application/json"})
    if args.v:
        print(">" * 40)
    print(colorful_json( json.dumps(response.json(), indent=4)) )

def stop_process_handler(args):
    process_id = args.process_id
    response = requests.delete(f"http://127.0.0.1:8080/process/{process_id}")
    print(colorful_json( json.dumps(response.json(), indent=4)) )
    
def list_process_handler(args):
    running = args.running
    pending = args.pending
    finished = args.finished

    response = None
    if not running and pending:
        response = requests.get("http://127.0.0.1:8080/process-queue")
    elif not running and finished:
        response = requests.get("http://127.0.0.1:8080/finished-process")
    else:
        response = requests.get("http://127.0.0.1:8080/process")

    print(colorful_json( json.dumps(response.json(), indent=4)) )
    
def output_process_handler(args):
    process_id = args.process_id
    response = requests.get(f"http://127.0.0.1:8080/output/{process_id}")
    for output_line in response.json():
        print(output_line)

def info_process_handler(args):
    process_id = args.process_id
    response = requests.get(f"http://127.0.0.1:8080/process/{process_id}")
    print(colorful_json( json.dumps(response.json(), indent=4)) )
 
def defualt_process_handler(args):
    if args.t == "":
        parser.print_help()

    task_path = args.t

    with open(task_path, "r") as f:
        task_list = json.load(f)
        for task in task_list:
            if args.v:
                print("<" * 40)
                print(colorful_json(json.dumps(task, indent=4)))

            response = requests.post("http://127.0.0.1:8080/process-queue/add", json=task, headers={"Content-Type": "application/json"})
            if args.v:
                print(">" * 40)
            print(colorful_json( json.dumps(response.json(), indent=4)) )

def main():
    global parser
    ptools_cli = argparse.ArgumentParser(prog="PTools")
    ptools_cli.add_argument('-v', help='Verbose', action="store_true")
    ptools_cli.add_argument('-t', help='Path to list of tasks to execute(JSON)', type=str, default="")
    ptools_cli.set_defaults(func=defualt_process_handler)
    parser = ptools_cli

    sub_parser = ptools_cli.add_subparsers(help='sub-command help')

    add_process_parser = sub_parser.add_parser('add', help='Add process to executor queue')
    add_process_parser.add_argument('--process-identity', type=str, help='Identity of process(UUID)', default="")  
    add_process_parser.add_argument('--process-depend-on', type=str, help='Wait until which process finish', default="-1")  
    add_process_parser.add_argument('--process-name', type=str, required=True, help='Name of process')  
    add_process_parser.add_argument('--process-directory', type=str, required=True, help='Directory of process')    
    add_process_parser.add_argument('--process-binary', type=str, required=True, help='Binary of process')  
    add_process_parser.add_argument('--process-binary-options', type=str, required=True, help='Options for passing to binary of process(includes subprogram name)') 
    add_process_parser.add_argument('--process-sub-program', type=str, required=True, help='Subprogram which is run (input to binary other than option)')
    add_process_parser.add_argument('--nice-value', type=int, help='Desire nice value for process', default=0)  
    add_process_parser.add_argument('--ionice-type', type=int, help='Desire ionice type for process', default=psutil.IOPRIO_CLASS_BE,
                        choices=[psutil.IOPRIO_CLASS_RT, psutil.IOPRIO_CLASS_BE, psutil.IOPRIO_CLASS_IDLE, psutil.IOPRIO_CLASS_NONE])   
    add_process_parser.add_argument('--ionice-value', type=int, help='Desire ionice value for process', default=0, choices=range(8))
    add_process_parser.add_argument('--cpus', type=str, help='Cpus for affinity', default="")   
    add_process_parser.add_argument('--scheduler-type', type=str, help='Desire scheduler type for process', default="o", choices=["o", "f", "r", "b", "i"])
    add_process_parser.add_argument('--scheduler-value', type=int, help='Desire scheduler value for process', default=0)
    add_process_parser.add_argument('--prescript-path', type=str, help='Pre execute script to run', default="")
    add_process_parser.add_argument('--prescript-shell', action='store_true', help='Pre script uses shell')
    add_process_parser.add_argument('--prescript-args', type=str, help='Pass more args to pre script', default="")
    add_process_parser.add_argument('--postscript-path', type=str, help='Post execute script to run', default="")
    add_process_parser.add_argument('--postscript-shell', action='store_true', help='Post script uses shell')
    add_process_parser.add_argument('--postscript-args', type=str, help='Pass more args to post script', default="")
    add_process_parser.set_defaults(func=add_process_handler)

    stop_process_parser = sub_parser.add_parser('stop', help='Stop running process')
    stop_process_parser.add_argument('--process-id', type=int, required=True, help="Process id")
    stop_process_parser.set_defaults(func=stop_process_handler)

    list_process_parser = sub_parser.add_parser('list', help='List process')
    list_process_parser.add_argument('--running', help='List of running process', action="store_true", default=False)
    list_process_parser.add_argument('--finished', help='List of finished process', action="store_true", default=False)
    list_process_parser.add_argument('--pending', help='List of pending process', action="store_true", default=False)
    list_process_parser.set_defaults(func=list_process_handler)

    output_process_parser = sub_parser.add_parser('output', help='Print output of process')
    output_process_parser.add_argument('--process-id', type=int, required=True, help="Process id")
    output_process_parser.set_defaults(func=output_process_handler)

    info_process_parser = sub_parser.add_parser('info', help='Get info of process') 
    info_process_parser.add_argument('--process-id', type=int, required=True, help="Process id")
    info_process_parser.set_defaults(func=info_process_handler)

    args = ptools_cli.parse_args()
    args.func(args)
    
if __name__ == "__main__":
    main()
