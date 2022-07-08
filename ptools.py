import argparse
import psutil
import requests
import json
from pydantic import BaseModel

from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.web import JsonLexer

# TODO: dublicate
class ProcessReq(BaseModel):
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


def colorful_json(json_str: str):
    return highlight(
        json_str,
        lexer=JsonLexer(),
        formatter=Terminal256Formatter(),
    )

def add_process_handler(args):
    process_req = ProcessReq()
    process_req.process_name = args.process_name
    process_req.process_directory = args.process_directory
    process_req.process_binary = args.process_binary
    process_req.process_binary_options = args.process_binary_options
    process_req.process_example_name = args.process_sub_program
    process_req.nice_value = args.nice_value
    process_req.ionice_type = args.ionice_type
    process_req.ionice_value = args.ionice_value
    process_req.cpu_affinity = [int(cpu) for cpu in args.cpus.split(",")]
    process_req.scheduler_type = args.scheduler_type
    process_req.scheduler_value = args.scheduler_value

    if args.v:
        raw_json = process_req.json()
        print(colorful_json(raw_json))


    response = requests.post("http:/127.0.0.1:8080/process-queue/add", json=process_req.json())
    print(colorful_json(response.json()))

def stop_process_handler(args):
    pass

def list_process_handler(args):
    pass

def output_process_handler(args):
    pass

def info_process_handler(args):
    pass

def defualt_process_handler(args):
    parser.print_help()
    
def main():
    global parser
    ptools_cli = argparse.ArgumentParser(prog="PTools")
    ptools_cli.add_argument('-v', help='Verbose', action="store_true")
    ptools_cli.set_defaults(func=defualt_process_handler)
    parser = ptools_cli

    sub_parser = ptools_cli.add_subparsers(help='sub-command help')

    add_process_parser = sub_parser.add_parser('add', help='Add process to executor queue')
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
    add_process_parser.add_argument('--scheduler-type', type=str, help='Desire scheduler type for process', default="-o", choices=["-o", "-f", "-r", "-b", "-i"])
    add_process_parser.add_argument('--scheduler-value', type=int, help='Desire scheduler value for process', default=0)
    add_process_parser.set_defaults(func=add_process_handler)

    stop_process_parser = sub_parser.add_parser('stop', help='Stop running process')
    stop_process_parser.add_argument('--process-id', type=int, required=True, help="Process id")
    stop_process_parser.set_defaults(func=stop_process_handler)

    list_process_parser = sub_parser.add_parser('list', help='List process')
    list_process_parser.add_argument('--running', help='List of running process', action="store_true")
    list_process_parser.add_argument('--pending', help='List of pending process', action="store_true")
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
