import uvicorn
import queue
import logging
import threading
import json
import psutil
import uuid

from typing import Union, List

from executor.executor_thread import *
from monitor.monitor_thread import *
from process.process_info import *
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)

hooks = {
        "get_all_process": None,
        "get_process_info": None,
        "cancel_running_process": None,
        "get_process_output": None,
        "watch_process_output": None,
        "get_process_in_queue": None,
        "add_process_in_queue": None,
        "delete_process_from_queue": None,
        "get_finished_process": None
}

server = FastAPI()

@server.get("/process")
def get_all_process():
    all_process = hooks["get_all_process"]()
    return all_process

@server.get("/process/{process_id}")
def get_process_info(process_id : int):
    all_process = hooks["get_all_process"]()
    process = [process_info for process_info in all_process if process_info.process_id == process_id]

    if len(process) > 0:
        return process[0]
    else:
        return {}

@server.delete("/process/{process_id}")
def cancel_running_process(process_id : int):

    if hooks["cancel_running_process"](process_id):
        return {
            "status": "the process canceld successfully"
        }
    else:
        return {
            "status": "couldnt cancel the process"
        }

@server.get("/output/{process_id}")
def get_process_output(process_id: int):
    return hooks["get_process_output"](process_id)

@server.get("/watch-output/{process_id}")
def watch_process_output(process_id: int):
    return {
        "output": process_id
    }

@server.get("/process-queue")
def get_process_in_queue():
    return [queue_obj for queue_obj in server.server_executor_queue.queue]

class HelperScriptBody(BaseModel):
    use_script = False
    script_path = ""
    script_use_shell = False
    pass_args = ""

def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test

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

@server.post("/process-queue/add")
def add_process_in_queue(process_req : ProcessReq):
    process_options = ProcessOptions()
    process_options.process_name = process_req.process_name
    process_options.process_directory = process_req.process_directory
    process_options.process_binary = process_req.process_binary
    process_options.process_binary_options = process_req.process_binary_options
    process_options.process_example_name = process_req.process_example_name
    process_options.nice_value = process_req.nice_value
    process_options.ionice_type_value = (process_req.ionice_type, process_req.ionice_value)
    process_options.cpu_affinity = process_req.cpu_affinity
    process_options.scheduler_type_value = (process_req.scheduler_type, process_req.scheduler_value)

    process_options.pre_execute_script = process_req.pre_script
    process_options.post_execute_script = process_req.post_script

    process_info = ProcessInfo(server.start_process_id, process_options)
    if process_req.process_identity != "":
        if is_valid_uuid(process_req.process_identity):
            process_info.process_identity = process_req.process_identity
        else:
            return {
                "status": "cannot add to queue because provided process identity is not valid uuid"
            }

    if process_req.process_depend_on != "-1":
        if is_valid_uuid(process_req.process_depend_on):
            process_info.process_depend_on = process_req.process_depend_on
        else:
            return {
                "status": "cannot add to queue because depend_on is not valid uuid"
            }

    server.start_process_id = server.start_process_id + 1
    server.server_executor_queue.put(process_info)

    return {
        "status": "added to queue"
    }

@server.get("/finished-process")
def get_finished_process():
    return hooks["get_finished_process"]()

@server.on_event("startup")
def startup_event():
    executor_monitor_queue = queue.Queue(1000)
    server_executor_queue = queue.Queue(1000)

    monitor_thread = MonitorThread(name="MonitorThread", kwargs = {
        "queue": executor_monitor_queue,
        "sleep_time_in_second": 10
    })
    monitor_thread.start()

    executor_thread = ExecutorThread(name="ExecutorThread", kwargs = {
        "process_queue": server_executor_queue,
        "process_outputs": "/root/playground/outputs",
        "process_monitor_queue": executor_monitor_queue,
        "executor_thread_loop_time": 1,
        "maximum_number_of_concurrent_running": 6
    })
    executor_thread.start()
    server.server_executor_queue = server_executor_queue
    hooks["get_all_process"] = executor_thread.get_all_running_process
    hooks["get_process_info"] = executor_thread.get_process_info_by_process_id
    hooks["get_process_output"] = executor_thread.get_process_output_by_id
    hooks["cancel_running_process"] = executor_thread.terminate_process_by_id
    hooks["get_finished_process"] = executor_thread.get_finished_process

    server.start_process_id = 1

if __name__ == "__main__":
    uvicorn.run("ptools_daemon:server", host="127.0.0.1", port=8080, reload=True, workers=1)
    
