#!/usr/bin/env python3

import time, threading, random, logging, os, hashlib, queue#, pdb

import glovar

from consistent import INIWAIT_TIME, RANBROAD_TIME, MEASURE_INTERVAL
# update lists process               
class UpdateList(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory

    def run(self):
        # Config the directory of log file
        filename = self.logdirectory + 'updatelist.txt'
        self.logger = logging.getLogger('updatelist')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info('Start UpdateList process')

        # Wait one or two RANBROAD_TIME duration 
        time.sleep(INIWAIT_TIME + 2*RANBROAD_TIME + 10)
        listnum = 500
        interval = 20

        cur_time = int(time.time())
        prev_time = cur_time - ( cur_time % interval ) + interval
        while True:
#            cur_time = int(time.time())
            if len(glovar.MessageList) > listnum:
                glovar.messageLock.acquire()
                glovar.MessageList.pop(0)
                glovar.messageLock.release()

#            if cur_time > prev_time:
#                logcontent = "MessageList:" + str(len(glovar.MessageList))# + "\n" + str(glovar.MessageList)
#                self.logger.info(logcontent)
#                prev_time += interval

            time.sleep(0.05)

