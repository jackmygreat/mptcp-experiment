import os
import subprocess
import sys
import json

if __name__ == '__main__':
	process_info = sys.argv[1]
	process_info_dict  = json.loads(process_info)
	
	# raise Exception(process_info_dict)
	os.chdir(process_info_dict["process_options"]["process_directory"])	
	subprocess.run("rm -rf *.pcap *.txt files*", shell=True)
