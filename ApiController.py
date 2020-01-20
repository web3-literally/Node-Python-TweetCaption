import threading
import requests
from time import sleep

import Config
import Global
import Helper

class ApiController():

    def __init__(self):
        self.listenThread = None
        self.transThread = None
        self.isListenOn = False
        self.isTransOn = False
        self.listenInterval = 5
        self.transInterval = 1

    def startListen(self):
        Helper.Log('Starting listen thread of api controller')
        self.isListenOn = True
        self.listenThread = threading.Thread(target=self.listenFunc)
        self.listenThread.start()

    def startTrans(self):
        Helper.Log('Starting transmit thread of api controller')
        self.isTransOn = True
        self.transThread = threading.Thread(target=self.transFunc)
        self.transThread.start()

    def listenFunc(self):
        while self.isListenOn:
            # Check if todo-queue is empty
            inProgressTaskExist = False
            Global.todoSync.acquire()
            Global.doneSync.acquire()
            if len(Global.todoQueue) > 0 or len(Global.doneQueue) > 0:
                inProgressTaskExist = True
            Global.doneSync.release()
            Global.todoSync.release()

            # Get todo-task from server only when there is no todo item
            if not inProgressTaskExist:
                newTasks = self.getTodoTasksRequest()
                if newTasks is not None and len(newTasks) > 0:
                    Global.todoSync.acquire()
                    index = 0
                    while index < len(newTasks):
                        task = newTasks[0]
                        id = task['id']
                        if id not in Global.todoQueue:
                            Global.todoQueue[id] = task
                        index += 1
                    Global.todoSync.release()
            sleep(self.listenInterval)

    def transFunc(self):
        while self.isTransOn:
            Global.doneSync.acquire()
            if (len(Global.doneQueue) > 0):
                while len(Global.doneQueue) > 0:
                    doneTask = Global.doneQueue[0]
                    if self.sendDoneTasksResponse(doneTask['id'], doneTask['pdf_name']) == False:
                        break
                    Global.doneQueue.pop(0)
            Global.doneSync.release()
            sleep(self.transInterval)

    def getTodoTasksRequest(self):
        try:
            url = Config.baseUrl + '/get-todo-list'
            data = '''{}'''
            response = requests.get(url, data)
            Helper.Log('ToDo task from server {0} {1}'.format(response, response.json()))
            if response.status_code == requests.codes.ok:
                return response.json()
            else:
                return None
        except Exception as e:
            Helper.Log('Exception in get-todo-list api {0}'.format(e))
            return None

    def sendDoneTasksResponse(self, id, pdf_name):
        try:
            url = Config.baseUrl + '/capture-done?id=' + id + '&pdf_name=' + pdf_name
            data = '''{}'''
            response = requests.get(url, data)
            Helper.Log('Sent done task({0}) to server {1} {2}'.format(id, response, response.json()))
            if response.status_code == requests.codes.ok:
                return True
            else:
                return False
        except Exception as e:
            Helper.Log('Exception in capture-done api {0}'.format(e))
            return False


