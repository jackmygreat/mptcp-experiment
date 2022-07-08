import argparse
import psutil


def add_process_handler(args):
    pass

def stop_process_handler(args):
    pass

def list_process_handler(args):
    pass

def output_process_handler(args):
    pass

def info_process_handler(args):
    pass

def main():
	ptools_cli = argparse.ArgumentParser(prog="PTools")
	ptools_clie.add_argument('-v', help='Verbose')

	sub_parser = parser.add_subparsers(help='sub-command help')

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
	list_process_parser.add_argument('--running', help='List of running process', action=argparse.BooleanOptionalAction)
	list_process_parser.add_argument('--pending', help='List of pending process', action=argparse.BooleanOptionalAction)
    list_process_parser.set_defaults(func=list_process_handler)

	output_process_parser = sub_parser.add_parser('output', help='Print output of process')
	output_process_parser.add_argument('--process-id', type=int, required=True, help="Process id")
    output_process_parser.set_defaults(func=output_process_handler)

	info_process_parser = sub_parser.add_parser('info', help='Get info of process')	
	info_process_parser.add_argument('--process-id', type=int, required=True, help="Process id")
    info_process_parser.set_defaults(func=info_process_handler)

    args = parser.parse_args()
    args.func(args)
	
if __name__ == "__main__":
	main()
