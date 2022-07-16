#!/usr/bin/python3.7

import os
import subprocess
import sys
import json
import psutil


def set_process_properties_and_wait(process):
	# set affinity of process
	try:
		proc = psutil.Process(process.pid)
		proc.cpu_affinity([0])
		proc.nice(-19)
		proc.ionice(psutil.IOPRIO_CLASS_RT, 0)
	except Exception as e:
		print(e)
	
	stdout, stderr = process.communicate()
	print(stdout)
	print(stderr)
	p_status = process.wait()
	print(p_status)

if __name__ == '__main__':
        #process_info = sys.argv[1]
        #process_info_dict  = json.loads(process_info)

        # raise Exception(process_info_dict)
        #os.chdir(process_info_dict["process_options"]["process_directory"])
        #subprocess.run("rm -rf *.pcap *.txt files*", shell=True)
	
	# create necessery directories if does not exists
	subprocess.run("mkdir -p mmwave", shell=True)
	subprocess.run("mkdir -p lte", shell=True)
	subprocess.run("mkdir -p iperf-data", shell=True)
	subprocess.run("mkdir -p throughput", shell=True)

	# remove any files in directories
	subprocess.run("rm -rf mmwave/*", shell=True)
	subprocess.run("rm -rf lte/*", shell=True)
	subprocess.run("rm -rf iperf-data/d iperf-data/iperf.data iperf-data/iperf.txt", shell=True)
	subprocess.run("rm -rf throughput/*.data", shell=True)

	process = subprocess.Popen(["captcp", "throughput", "-s", "0.5", "-i", "-o", "lte", "lte-mmwave2-1-1.pcap"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)	
	set_process_properties_and_wait(process)	
	
	process = subprocess.Popen(["captcp", "throughput", "-s", "0.5", "-i", "-o", "mmwave", "lte-mmwave2-1-0.pcap"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)	
	set_process_properties_and_wait(process)
		
	# make each subflows pdf	
	subprocess.run("make -C ./lte all", shell=True)
	subprocess.run("make -C ./mmwave all", shell=True)
	
	# make overal throughput pdf
	subprocess.run("cat files-0/var/log/46642/stdout > iperf-data/iperf.txt", shell=True)
	subprocess.run("cd iperf-data && ./extract-iperf.sh iperf.txt && python3 transfer_to_b.py && cd ..", shell=True)
	subprocess.run("cp lte/throughput.data throughput/lte.data", shell=True)
	subprocess.run("cp mmwave/throughput.data throughput/mmwave.data", shell=True)
	subprocess.run("cp iperf-data/iperf.data throughput/iperf.data", shell=True)
	subprocess.run("make -C ./throughput all", shell=True)
