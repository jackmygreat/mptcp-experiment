import uvicorn
import queue
import logging
import threading

from executor.executor_thread import *
from monitor.monitor_thread import *
from server import *

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)

if __name__ == "__main__":
    executor_monitor_queue = queue.Queue(1000)
    server_executor_queue = queue.Queue(1000)

    monitor_thread = MonitorThread(kwargs = {
        "queue": executor_monitor_queue,
        "sleep_time_in_second": 10
    })
    monitor_thread.start()

    executor_thread = ExecutorThread(kwargs = {
        "process_queue": server_executor_queue,
        "process_outputs": "/root/playground/outputs",
        "process_monitor_queue": executor_monitor_queue,
        "executor_thread_loop_time": 10
    })
    executor_thread.start()

    uvicorn.run("server.api:server", host="0.0.0.0", port=8080, reload=True)
    monitor_thread.join()
    executor_thread.join()
