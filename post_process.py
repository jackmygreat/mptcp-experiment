#!/usr/bin/python3.7

import os
import subprocess
import sys
import json
import psutil
import time

def set_process_properties_and_wait(process, cpu):
		# set affinity of process
		try:
				proc = psutil.Process(process.pid)
				proc.cpu_affinity([cpu])
				proc.nice(-19)
				proc.ionice(psutil.IOPRIO_CLASS_RT, 0)
		except Exception as e:
				print(e)
		
		stdout, stderr = process.communicate()
		print(stdout)
		print(stderr)
		p_status = process.wait()
		print(p_status)

def set_properties_on_child(process, cpu):
		try:
				procs = psutil.Process().children()
				for proc in procs:
						proc.cpu_affinity([cpu])
						proc.nice(-19)
						proc.ionice(psutil.IOPRIO_CLASS_RT, 0)
		except Exception as e:
				print(e)

if __name__ == '__main__':
		process_info = sys.argv[1]
		cc_name = str(sys.argv[2])
		pcap_name = str(sys.argv[3])
		try:
			kv_output = str(sys.argv[4])
			kv_output = json.loads(kv_output)
		except:
			pass

		process_info_dict  = json.loads(process_info)
		process_name = process_info_dict["process_options"]["process_name"]
		os.chdir(process_info_dict["process_options"]["process_directory"])
		output_dir = process_info_dict["process_options"]["process_output_dir"]
		cpus = process_info_dict["process_options"]["cpu_affinity"]
		
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

		process = subprocess.Popen(["captcp", "throughput", "-u", "megabit", "-s", "0.3", "-i", "-o", "lte", f"{pcap_name}-1-1.pcap"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)	
		set_process_properties_and_wait(process, cpus[0])		
		
		# make lte subflow pdf based on megabit
		subprocess.run(f"sed -i 's/Throughput\ Graph/Lte\ with\ {cc_name}/g' lte/throughput.gpi", shell=True)
		subprocess.run("make -C ./lte all", shell=True)

		process = subprocess.Popen(["captcp", "throughput", "-u", "megabit", "-s", "0.3", "-i", "-o", "mmwave", f"{pcap_name}-1-0.pcap"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)		
		set_process_properties_and_wait(process, cpus[0])
				
		# make mmwave subflow pdf		
		subprocess.run(f"sed -i 's/Throughput\ Graph/Mmwave\ with\ {cc_name}/g' mmwave/throughput.gpi", shell=True)
		subprocess.run("make -C ./mmwave all", shell=True)

		subprocess.run("cp mmwave/Makefile throughput", shell=True)
		subprocess.run("cp throughput.gpi throughput/throughput.gpi", shell=True)
		
		# make overal throughput pdf
		subprocess.run("cat files-0/var/log/46642/stdout > iperf-data/iperf.txt", shell=True)
		subprocess.run("cd iperf-data && ./extract-iperf.sh iperf.txt && python3 transfer_to_b.py && cd ..", shell=True)
		subprocess.run("cp lte/throughput.data throughput/lte.data", shell=True)
		subprocess.run("cp mmwave/throughput.data throughput/mmwave.data", shell=True)
		subprocess.run("cp iperf-data/iperf.data throughput/iperf.data", shell=True)
		subprocess.run(f"sed -i 's/Throughput\ Graph/Throughput\ {process_name}/g' throughput/throughput.gpi", shell=True)
		subprocess.run("make -C ./throughput all", shell=True)

		# gather some results wihtout compression
		subprocess.run("mkdir -p results", shell=True)	
		subprocess.run("cat files-0/var/log/46642/stdout > results/iperf.txt", shell=True)
		subprocess.run("cp iperf-data/iperf.data results/iperf.data", shell=True)
		subprocess.run("cp lte/throughput.data results/lte.data", shell=True)
		subprocess.run("cp mmwave/throughput.data results/mmwave.data", shell=True)

		subprocess.run("cp mmwave/throughput.pdf results/mmwave.pdf", shell=True)
		subprocess.run("cp lte/throughput.pdf results/lte.pdf", shell=True)
		subprocess.run("cp throughput/throughput.pdf results/throughput.pdf", shell=True)

		# gather all results and compress them
		subprocess.run("mkdir -p archive", shell=True)
		subprocess.run("mv -t archive files* *.pcap *.txt throughput lte mmwave", shell=True)

		process = subprocess.Popen("tar cvf - archive | gzip -9 - > archive.tar.gz", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		set_process_properties_and_wait(process, cpus[0])
		set_properties_on_child(process, cpus[0])

		subprocess.run("rm -rf archive", shell=True)
		subprocess.run("mv archive.tar.gz results", shell=True)
		subprocess.run(f"mv results {output_dir}", shell=True)
