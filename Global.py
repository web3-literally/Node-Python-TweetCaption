import threading

def init():
    global todoQueue        # The queue of tasks should be done now
    todoQueue = {}
    global doneQueue        # The queue of tasks have been finished
    doneQueue = []
    global todoSync         # Synchronize machine for the todo queue
    todoSync = threading.Lock()
    global doneSync         # Synchronize machine for the done queue
    doneSync = threading.Lock()

