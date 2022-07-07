from fastapi import FastAPI
from pydantic import BaseModel

server = FastAPI()


@server.get("/process")
def get_all_process():
    
    return {
        "empty": "empty"
    }

@server.get("/process/{process_id}")
def get_process_info(process_id : int):
    return {
        "process_id": process_id
    }

@server.delete("/process/{process_id}")
def cancel_running_process(process_id : int):
    return {
        "canceled": process_id
    }

@server.get("/output/{process_id}")
def get_process_output(process_id: int):
    return {
        "process_output": "output"
    }

@server.get("/watch-output/{process_id}")
def watch_process_output(process_id: int):
    return {
        "output": process_id
    }

@server.get("/process-queue")
def get_process_in_queue():
    return {
        "queue": [
            {
                "process1": "process1"
            },
            {
                "process1": "process1"
            }
        ]
    }

class ProcessReq(BaseModel):
    pass

@server.post("/process-queue/add")
def add_process_in_queue(process_info : ProcessReq):
    return process_info

@server.delete("/process-queue/{process_id}")
def delete_process_from_queue(process_id : int):
    return {
        "process_id": process_id
    }


