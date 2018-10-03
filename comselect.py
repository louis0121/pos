#!/usr/bin/env python3

import time, threading, random, logging, os, hashlib, queue#, pdb

from consistent import RANBROAD_TIME, INIWAIT_TIME, COM_INTERVAL, CLEAR_TIME

import glovar

from blockgen import *
from verify import *
from network import broadMessage

# committee process               
class Comselect(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory

    def run(self):
        # Config the directory of log file
        filename = self.logdirectory + 'Comselectlog.txt'
        self.logger = logging.getLogger('RanselectProcessing')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info('Start committe random selection process')

        # Wait one or two RANBROAD_TIME duration for starting random number propagation
        cur_time = int(time.time())
        prev_time = cur_time - ( cur_time % INIWAIT_TIME )
        while True:
            cur_time = int(time.time())
            if cur_time > prev_time + INIWAIT_TIME + 1:
                break
            else:
                time.sleep(1)

       # pdb.set_trace()
        date_stamp = int(time.time())
        while True:
            if date_stamp > prev_time:
                self.comformation()
                prev_time = date_stamp
            else:
                time.sleep(1)
            cur_time = int(time.time())
            date_stamp = cur_time - ( cur_time % COM_INTERVAL )

    def comformation(self):
        # initial global status
        glovar.ranLock.acquire()
        glovar.RanList.clear()
        glovar.ranLock.release()
        glovar.hashLock.acquire()
        glovar.HashSeed = 0
        glovar.HashList.clear()
        glovar.hashLock.release()
        glovar.PosList.clear()
#        glovar.ComList.clear()


        cur_time = int(time.time())
        prev_time = cur_time - (cur_time % CLEAR_TIME)
        while True:
            cur_time = int(time.time())
            if cur_time > prev_time + CLEAR_TIME:
                break
            else:
                time.sleep(0.5)
        # Inform other PoS node process to stop
        glovar.ComChange = 1
        notend = True
        while notend:
            notend = False
            for each in glovar.ComList:
                if each[6]:
                    notend = True
                    break

            time.sleep(0.05)

        glovar.ComList.clear()
        glovar.ComChange = 0

        self.logger.info('--------------------------------------------------')
        # Start committee formation
        random.seed()
        genrandom = random.uniform(0,1)
        logcontent = 'Send a random number: ' + str(genrandom)
        self.logger.info(logcontent)
        glovar.ranLock.acquire()
        glovar.RanList.append(str(genrandom))
        glovar.ranLock.release()
        # self.logger.info('put random number to RanList.')

        content = {'genrandom':genrandom}
        beforesend = {'type':'comrandom','No':1,'content':content}
        temp = str(beforesend)
        hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
        senddata = {'messageid':hashvalue,'type':'comrandom','No':1,'content':content}

        glovar.messageLock.acquire()
        glovar.MessageList.append(hashvalue)
        glovar.messageLock.release()
        broadMessage(senddata)

        # Wait one or two RANBROAD_TIME duration for generating hashvalue
        time.sleep(RANBROAD_TIME)

        logcontent = 'Received random numbers: ' + str(len(glovar.RanList))
        self.logger.info(logcontent)
#        self.logger.info(glovar.RanList)

#        self.logger.info('Generate hash value of random numbers.')
        glovar.ranLock.acquire()
        randomstring = "".join(glovar.RanList)
        glovar.ranLock.release()

        hashvalue = int(hashlib.sha256(randomstring.encode('utf-8')).hexdigest(), 16)
        glovar.hashLock.acquire()
        glovar.HashSeed = hashvalue
        glovar.HashList.append(hashvalue)
        glovar.hashLock.release()

        content = {'ranhash':hashvalue,'ranlist':glovar.RanList}
        beforesend = {'type':'comrandom','No':2,'content':content}
        temp = str(beforesend)
        hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
        senddata = {'messageid':hashvalue,'type':'comrandom','No':2,'content':content}

        glovar.messageLock.acquire()
        glovar.MessageList.append(hashvalue)
        glovar.messageLock.release()
        broadMessage(senddata)

        # Wait one or two RANBROAD_TIME duration for agree on the smallest hashvalue
        time.sleep(RANBROAD_TIME)

        logcontent = 'Received hashvalue list numbers: ' + str(len(glovar.HashList))
        self.logger.info(logcontent)
#        self.logger.info(glovar.HashList)
        logcontent = 'The final HashSeed is:\n' + str(glovar.HashSeed)
        self.logger.info(logcontent)

        # Generate random number to choose members for each committee
        nodenum = glovar.Firstcommem * glovar.Firstcomno + glovar.Secondcommem
        comnum = glovar.Firstcomno + 1
        random.seed(glovar.HashSeed)
        for i in range(nodenum):
            glovar.PosList.append(random.uniform(0,glovar.Stakesum))

        logcontent = 'PosList:' + str(len(glovar.PosList)) + '\n' + str(glovar.PosList)
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

        # Inform other PoS node process to stop
#        glovar.ComChange = 1
#        notend = True
#        while notend:
#            notend = False
#            for each in glovar.ComList:
#                if each[6]:
#                    notend = True
#                    break
#
#            time.sleep(0.05)
#
#        glovar.ComList.clear()
#        glovar.ComChange = 0

        # Record the status of committee
        for i in range (nodenum):
            if (glovar.PosList[i] > glovar.Stakemin and glovar.PosList[i] <= glovar.Stakemax):
                incomno = i // glovar.Firstcommem + 1
                if (incomno < comnum):
                    commember = glovar.PosList[(incomno-1)*glovar.Firstcommem:incomno*glovar.Firstcommem]
                else:
                    commember = glovar.PosList[(incomno-1)*glovar.Firstcommem:]

                newblock = []
                commitlist = []
                commitblocklist = []
                addfirstlist = []
                transactionlist = []
                secondcommitlist = []
                newsecondblock = []
                comstatus = {'genblock':0, 'blockhash':'0', 'stage':0, 'commit':0, 'commitlist':commitlist, \
                        'newblock':newblock, 'verify':0, 'commitblocklist':commitblocklist, \
                        'transactionlist':transactionlist, 'secondblockhash':'0', \
                        'secondcommit':0, 'secondcommitlist':secondcommitlist, \
                        'newsecondblock':newsecondblock, 'addfirstlist':addfirstlist}
                comnodequeue = queue.Queue()
                commemberLock = threading.Lock()
                process = 1
                cominfo = [incomno, glovar.PosList[i], commember, comstatus, comnodequeue, commemberLock, process]
                glovar.ComList.append(cominfo)

        self.logger.info('--------------------------------------------')
        if len(glovar.ComList):
            logcontent = 'Node is selected in committee:\n'
            for each in glovar.ComList:
                logcontent += str(each) + '\n'
            self.logger.info(logcontent)

        for each in glovar.ComList:
            # Run the node in Firstcommittee
            if each[0] <= glovar.Firstcomno:
                block_generation = BlockProcessing(each, self.logdirectory)
                block_generation.start()
            else:
                block_verify = VerifyProcessing(each, self.logdirectory)
                block_verify.start()

# Test process as main program
if __name__ == '__main__':
    pwd = os.getcwd()
    logdirectory = pwd + '/log/1/'
    user_comselection = RanselectProcessing(logdirectory)
    user_comselection.start()

