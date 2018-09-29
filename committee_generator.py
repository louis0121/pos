#!/usr/bin/env python3

import time, threading, random, logging, os, hashlib, queue#, pdb

from consistent import RANBROAD_TIME, INIWAIT_TIME, COM_INTERVAL, CLEAR_TIME

import glovar

from blockgen import *
from verify import *
from network import broadMessage

# committee process               
class CommitteeGeneration(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory

    def run(self):
        # Config the directory of log file
        filename = self.logdirectory + 'committee_generator.txt'
        self.logger = logging.getLogger('CommitteeGeneration')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info('Start committe generation process')

        # Wait one or two RANBROAD_TIME duration for starting random number propagation
        cur_time = int(time.time())
        prev_time = cur_time - ( cur_time % INIWAIT_TIME )
        while True:
            cur_time = int(time.time())
            if cur_time > prev_time + INIWAIT_TIME + 1:
                break
            else:
                time.sleep(0.5)

       # pdb.set_trace()
        date_stamp = int(time.time())
        while True:
            if date_stamp > prev_time:
                self.com_formation()
                prev_time = date_stamp
            else:
                time.sleep(1)
            cur_time = int(time.time())
            date_stamp = cur_time - ( cur_time % COM_INTERVAL )

    def com_formation(self):
        # initial global status
        glovar.newComLock.acquire()
        glovar.NewComList.clear()
        glovar.newComLock.release()
        glovar.newRanLock.acquire()
        glovar.NewRanList.clear()
        glovar.newRanLock.release()
        glovar.newHashLock.acquire()
        glovar.NewHashList.clear()
        glovar.NewHashSeed = 0
        glovar.newHashLock.release()
        glovar.NewPosList.clear()

        self.logger.info('--------------------------------------------------')
        # Start committee formation
        random.seed()
        genrandom = random.uniform(0,1)
        logcontent = 'Send a random number: ' + str(genrandom)
        self.logger.info(logcontent)
        glovar.newRanLock.acquire()
        glovar.NewRanList.append(str(genrandom))
        glovar.newRanLock.release()

        timestamp = time.time()
        content = {'genrandom':genrandom}
        beforesend = {'type':'newcommittee','No':1,'timestamp':timestamp,'content':content}
        temp = str(beforesend)
        hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
        senddata = {'messageid':hashvalue,'type':'newcommittee','No':1,'timestamp':timestamp,'content':content}

        glovar.messageLock.acquire()
        glovar.MessageList.append(hashvalue)
        glovar.messageLock.release()
        broadMessage(senddata)

        # Wait one or two RANBROAD_TIME duration for generating hashvalue
        starttime = int(time.time())
        curtime = starttime
        while curtime < starttime + RANBROAD_TIME:
            try:
                glovar.newComqueueLock.acquire()
                data = glovar.newcomqueue.get_nowait()
                glovar.newComqueueLock.release()
#                logcontent = 'Get a message:' + str(data['messageid'])
#                self.logger.info(logcontent)
                self.__dataHandle(data)
            except queue.Empty:
                glovar.newComqueueLock.release()
                time.sleep(0.1)
            finally:
                curtime = int(time.time())

        logcontent = 'Received new committee random numbers: ' + str(len(glovar.NewRanList))
        self.logger.info(logcontent)
        self.logger.info(glovar.NewRanList)

#        self.logger.info('Generate hash value of random numbers.')
        glovar.newRanLock.acquire()
        randomstring = "".join(glovar.NewRanList)
        glovar.newRanLock.release()

        hashvalue = int(hashlib.sha256(randomstring.encode('utf-8')).hexdigest(), 16)
        glovar.newHashLock.acquire()
        glovar.NewHashSeed = hashvalue
        glovar.NewHashList.append(hashvalue)
        glovar.newHashLock.release()

        content = {'ranhash':hashvalue,'ranlist':glovar.NewRanList}
        beforesend = {'type':'newcommittee','No':2,'content':content}
        temp = str(beforesend)
        hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
        senddata = {'messageid':hashvalue,'type':'newcommittee','No':2,'content':content}

        glovar.messageLock.acquire()
        glovar.MessageList.append(hashvalue)
        glovar.messageLock.release()
        broadMessage(senddata)

        # Wait one or two RANBROAD_TIME duration for agree on the smallest hashvalue
        starttime = int(time.time())
        curtime = starttime
        while curtime < starttime + RANBROAD_TIME:
            try:
                data = glovar.newcomqueue.get_nowait()
#                logcontent = 'Get a message:' + str(data['messageid'])
#                self.logger.info(logcontent)
                self.__dataHandle(data)
            except queue.Empty:
                time.sleep(0.1)
            finally:
                curtime = int(time.time())

        logcontent = 'Received new committee hashvalue list numbers: ' + str(len(glovar.NewHashList))
        self.logger.info(logcontent)
#        self.logger.info(glovar.HashList)
        logcontent = 'The final new committee HashSeed is:\n' + str(glovar.NewHashSeed)
        self.logger.info(logcontent)

        # Generate random number to choose members for each committee
        nodenum = glovar.Firstcommem * glovar.Firstcomno + glovar.Secondcommem
        comnum = glovar.Firstcomno + 1
        random.seed(glovar.NewHashSeed)
        for i in range(nodenum):
            glovar.NewPosList.append(random.uniform(0,glovar.Stakesum))

        logcontent = 'NewPosList:' + str(len(glovar.NewPosList)) + '\n' + str(glovar.NewPosList)
        self.logger.info(logcontent)
#        logcontent = 'NodeId: ' + str(glovar.NodeId)
#        self.logger.info(logcontent)
#        logcontent = 'Stakemin: ' + str(glovar.Stakemin)
#        self.logger.info(logcontent)
#        logcontent = 'Stakemax: ' + str(glovar.Stakemax)
#        self.logger.info(logcontent)
#        logcontent = 'Firstcommem: ' + str(glovar.Firstcommem)
#        self.logger.info(logcontent)
#        logcontent = 'Firstcomno: ' + str(glovar.Firstcomno)
#        self.logger.info(logcontent)
#        logcontent = 'Secondcommem: ' + str(glovar.Secondcommem)
#        self.logger.info(logcontent)

        # Record the status of committee
        for i in range (nodenum):
            if (glovar.NewPosList[i] > glovar.Stakemin and glovar.NewPosList[i] <= glovar.Stakemax):
                incomno = i // glovar.Firstcommem + 1
                if (incomno < comnum):
                    commember = glovar.NewPosList[(incomno-1)*glovar.Firstcommem:incomno*glovar.Firstcommem]
                else:
                    commember = glovar.NewPosList[(incomno-1)*glovar.Firstcommem:]

                newblock = []
                commitlist = []
                commitblocklist = []
                comstatus = {'genblock':0,'blockhash':'0','stage':0,'commit':0,'commitlist':commitlist,'newblock':newblock,'verify':0,'commitblock':0,'commitblocklist':commitblocklist}
                comnodequeue = queue.Queue()
                cominfo = [incomno, glovar.NewPosList[i], commember, comstatus, comnodequeue]
                glovar.NewComList.append(cominfo)

        self.logger.info('--------------------------------------------')
        if len(glovar.NewComList):
            logcontent = 'Next new committee nodes:\n'
            for each in glovar.NewComList:
                logcontent += str(each) + '\n'
            self.logger.info(logcontent)

    def __dataHandle(self,data):
        if data['No'] == 1:
#            logcontent = 'Handle a random number:' + str(data['content']['genrandom'])
#            self.logger.info(logcontent)
#            if str(data['content']['genrandom']) not in glovar.RanList:
            glovar.newRanLock.acquire()
            glovar.NewRanList.append(str(data['content']['genrandom']))
            glovar.newRanLock.release()

            broadMessage(data)

#                logcontent = ' Broad this committee random number again: ' + str(data['genrandom'])
#                self.logger.info(logcontent)
        # Receive a hashseed
        if data['No'] == 2:
#            logcontent = ' Receive a hashvalue:' + str(data['content']['ranhash'])
#            self.logger.info(logcontent)

#            if data['ranhash'] not in glovar.HashList:
            glovar.newHashLock.acquire()
            glovar.NewHashList.append(data['content']['ranhash'])
            glovar.newHashLock.release()

            if ( glovar.NewHashSeed == 0 or data['content']['ranhash'] < glovar.NewHashSeed ):
                glovar.newHashLock.acquire()
                glovar.NewHashSeed = data['content']['ranhash']
                glovar.newHashLock.release()
                broadMessage(data)

# Test process as main program
if __name__ == '__main__':
    pwd = os.getcwd()
    logdirectory = pwd + '/log/1/'
    user_comselection = RanselectProcessing(logdirectory)
    user_comselection.start()

