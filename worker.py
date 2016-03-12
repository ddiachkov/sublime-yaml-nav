"""
Module for executing tasks in separate thread.
"""

try:
    from queue import Queue
except:
    # ST2, Python 2
    from Queue import Queue

import threading
import traceback


class Worker:
    """
    Worker to execute tasks.
    """

    def __init__(self):
        self.q = Queue()
        self.running = False

    def start(self):
        """
        Starts worker thread.
        """

        if not self.running:
            self.running = True
            threading.Thread(target=self.loop).start()

    def stop(self):
        """
        Stops worker thread.
        """

        self.running = False
        self.q.put(lambda: 42)  # no-op to unpause thread

    def execute(self, callback):
        """
        Enqueues task to execute.
        """

        self.q.put(callback)

    def loop(self):
        """
        Thread loop.
        """

        while self.running:
            try:
                callback = self.q.get(block=True)
                callback()
            except:
                print("Error in YAML Nav worker thread:", traceback.format_exc())


# Main worker instance
__worker = None


def execute(callback):
    """
    Executes given callback in separate thread.
    """

    global __worker

    # Create worker on demand
    if not __worker:
        __worker = Worker()
        __worker.start()

    __worker.execute(callback)


def unload_handler():
    """
    Sublime will call this function on plugin reload.
    """

    global __worker

    # Stop the worker
    if __worker:
        __worker.stop()
        __worker = None
