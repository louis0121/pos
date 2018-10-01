#!/usr/bin/env python3

import time, threading, random, logging, os, hashlib, json, queue#, pdb

import glovar

from consistent import BLOCK_INTERVAL

from network import broadMessage

# committee process               
class VerifyProcessing(threading.Thread):
    def __init__(self, cominfo, logdirectory):
        threading.Thread.__init__(self)
        self.cominfo = cominfo
        self.logdirectory = logdirectory

    def run(self):
        filename = self.logdirectory + 'verifylog.txt'
        self.logger = logging.getLogger(str(self.cominfo[1]))
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        incomno = self.cominfo[0]
        comid = self.cominfo[1]
        commember = self.cominfo[2]
        logcontent = 'Start committee ' + str(incomno)
        self.logger.info(logcontent)

        # Start the second block generaton process
        generatethread = threading.Thread(target=self.__gendatablock)
        generatethread.start()

        # Receive data for this process to handle
        for each in glovar.ComList:
            if comid == each[1]:
                while True:
                    try:
                        data = each[4].get_nowait()
#                        logcontent = 'VerifyProcessing get a message:' + str(data)
#                        self.logger.info(logcontent)
                        self.__dataHandle(data)
                    except queue.Empty:
                        time.sleep(0.05)

                    if glovar.ComChange:
                        each[6] = 0
                        break

        # End the process
        logcontent = 'The process is ended.'
        self.logger.info(logcontent)

    # Handle message for the last committee member
    def __dataHandle(self, data):
        if data['type'] == 'firstblock' and data['No'] == 3:
            # Verify whether it is commited by the committee member
            if (data['content']['commitnum'] >= glovar.Firstcommem//2+1):
#                logcontent = 'A valid commit firstblock:' + str(data['content']['block'][4])
#                self.logger.info(logcontent)

                for each in glovar.ComList:
                    if self.cominfo[1] == each[1]:
                        if data['content']['block'][4] not in each[3]['addfirstlist']:
                            each[5].acquire()
                            each[3]['commitblocklist'].append(data['content']['block'][4])
                            each[3]['transactionlist'].extend(data['content']['block'][5])
                            each[5].release()
#                        logcontent = 'Save a commit firstblock:' + str(data['content']['block'][4])
#                        self.logger.info(logcontent)

        if data['type'] == 'secondblock' and data['No'] == 1:
#            logcontent = 'Handle a secondblock:' + str(data['messageid'])
#            self.logger.info(logcontent)
            blockdata = data['content']

            # Verify if the node is in our committee
            if blockdata[3] in self.cominfo[2]:
                logcontent = 'Verify a secondblock:' + str(blockdata[1]) + 'from comid:' + str(blockdata[3])
                self.logger.info(logcontent)

                # Change the corresponding global status
                for each in glovar.ComList:
                    if self.cominfo[1] == each[1]:
                        each[5].acquire()
                        each[3]['newsecondblock'].append(blockdata)
                        each[5].release()

                # Send a commitment message
                content = {'blockhash':blockdata[1],'incomno':self.cominfo[0],'comid':self.cominfo[1],'commit':1}
                beforesend = {'type':'secondblock','No':2,'content':content}
                temp = str(beforesend)
                hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
                senddata = {'messageid':hashvalue,'type':'secondblock','No':2,'content':content}

                glovar.messageLock.acquire()
                glovar.MessageList.append(hashvalue)
                glovar.messageLock.release()
                broadMessage(senddata)
                logcontent = 'Send a second commitment for block:' + str(senddata['content']['blockhash'])
                self.logger.info(logcontent)

                # Check if there is another PoS in the same committee
                for each in glovar.ComList:
                    if each[0] == self.cominfo[0] and each[1] != self.cominfo[1]:
                        each[5].acquire()
                        each[4].put(senddata)
                        each[5].release()

        if data['type'] == 'secondblock' and data['No'] == 2:
#            logcontent = 'Handle a second commitment:' + str(data['messageid'])
#            self.logger.info(logcontent)

            # Verify whether it is commited by the committee member
            if data['content']['comid'] in self.cominfo[2]:
                logcontent = 'Verify a second commitment for block:' + str(data['content']['blockhash']) + ' from comid:' + str(data['content']['comid'])
                self.logger.info(logcontent)

            for each in glovar.ComList:
                if each[1] == self.cominfo[1]:
                    if each[3]['verify']:
                        each[5].acquire()
                        each[3]['secondcommit'] += 1
                        each[3]['secondcommitlist'].append(data['content']['comid'])
                        each[5].release()
                        logcontent = 'Secondblock:' + str(each[3]['secondblockhash']) + ' receive a commit. Total:' + str(each[3]['secondcommit'])
                        self.logger.info(logcontent)

                        # Receive enough commitment
                        if (each[3]['secondcommit'] >= glovar.Secondcommem//2+1):
                            logcontent = 'Receive enough commitment for blocblock:' + str(each[3]['secondblockhash'])
                            self.logger.info(logcontent)
                            self.broadSecondCommitBlock()
                            self.addBlock(each[3]['newsecondblock'][0])

        if data['type'] == 'secondblock' and data['No'] == 3:
#            logcontent = 'Handle a commit secondblock:' + str(data['content']['block'][1])
#            self.logger.info(logcontent)

            # Verify if the firstblock has received enough commitment from its committee
            listisin = True
            for each in data['content']['comlist']:
                if each not in self.cominfo[2]:
                    listisin = False
                    break
            if listisin:
                logcontent = 'Verified the commit secondblock:' + str(data['content']['block'][1])
                self.logger.info(logcontent)

                for each in glovar.ComList:
                    if each[1] == self.cominfo[1]:
                        # Delate the blockhash has been included in the
                        # secondblock from commitblocklist
                        each[5].acquire()
#                        logcontent = "each[3]['commitblocklist']:" + str(each[3]['commitblocklist'])
#                        self.logger.info(logcontent)
#                        logcontent = "data['content']['block'][6]:" + str(data['content']['block'][6])
#                        self.logger.info(logcontent)
                        templist = []
                        for every in each[3]['commitblocklist']:
                            if every not in data['content']['block'][6]:
                                templist.append(every)

                        each[3]['commitblocklist'] = templist.copy()

                        temptranslist = []
                        for every in each[3]['transactionlist']:
                            if every not in data['content']['block'][7]:
                                temptranslist.append(every)

                        each[3]['transactionlist'] = temptranslist.copy()

                        each[3]['addfirstlist'].extend(data['content']['block'][6])
#                        logcontent = "each[3]['addfirstlist']:" + str(each[3]['addfirstlist'])
#                        self.logger.info(logcontent)
#                        logcontent = "each[3]['commitblocklist']:" + str(each[3]['commitblocklist'])
#                        self.logger.info(logcontent)
                        each[5].release()

#                        self.addBlock(each[3]['newsecondblock'][0])
                        self.addBlock(data['content']['block'])

    def __gendatablock(self):

        stillin = True
        cur_time = int(time.time())
        prev_time = cur_time - ( cur_time % BLOCK_INTERVAL ) + BLOCK_INTERVAL
        while stillin:
            cur_time = int(time.time())
            if cur_time > prev_time:
                # Select a leader to generate block 
                self.logger.info('----------------------------------------')
                logcontent = 'Choose a new leader to generate a secondblock'
                self.logger.info(logcontent)

                randomstring = "".join(str(self.cominfo[2]))
                glovar.blockchainLock.acquire()
                if len(glovar.BLOCKCHAIN):
                    prevhash = glovar.BLOCKCHAIN[len(glovar.BLOCKCHAIN)-1][1]
                else:
                    prevhash = 0
                glovar.blockchainLock.release()
                randomstring += str(prevhash)

                logcontent = "randomstring:" + str(randomstring)
                self.logger.info(logcontent)
                idchoose = int(hashlib.sha256(randomstring.encode('utf-8')).hexdigest(), 16) % len(self.cominfo[2])

                logcontent = str(idchoose+1) + ' member: ' + \
                str(self.cominfo[2][idchoose]) + ' is chosen to generate a second block'
                self.logger.info(logcontent)

                # Self is selected
                if self.cominfo[1] == self.cominfo[2][idchoose]:
                    for each in glovar.ComList:
                        if self.cominfo[1] == each[1]:
                            each[5].acquire()
                            commitblocklist = each[3]['commitblocklist'].copy()
                            transactionlist = each[3]['transactionlist'].copy()
                            each[3]['commitblocklist'].clear()
                            each[3]['transactionlist'].clear()
                            each[3]['verify'] = 1
                            logcontent = "each[3]['commitblocklist']:" + str(len(each[3]['commitblocklist']))
                            self.logger.info(logcontent)
                            each[5].release()

                    timestamp = time.time()
                    temp = str(prevhash) + str(self.cominfo[0]) + str(self.cominfo[1]) + str(self.cominfo[2]) + str(timestamp) + str(commitblocklist) + str(len(transactionlist))
                    hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
                    newblock = [prevhash,hashvalue,self.cominfo[0],self.cominfo[1],self.cominfo[2],timestamp,commitblocklist,transactionlist]

                    for each in glovar.ComList:
                        if self.cominfo[1] == each[1]:
                            each[5].acquire()
                            each[3]['secondblockhash'] = hashvalue
                            each[3]['newsecondblock'].append(newblock)
                            each[5].release()

                    senddata = {'messageid':hashvalue,'type':'secondblock','No':1,'content':newblock}
                    glovar.messageLock.acquire()
                    glovar.MessageList.append(hashvalue)
                    glovar.messageLock.release()
                    broadMessage(senddata)
                    self.logger.info('---------------------------------')
                    logcontent = str(self.cominfo[1]) + ' :broadcast a second block:' + str(hashvalue)
                    self.logger.info(logcontent)

                    # Send data to this PoS node process
                    for each in glovar.ComList:
                        if each[0] == self.cominfo[0] and each[1] != self.cominfo[1]:
                            each[5].acquire()
                            each[4].put(senddata)
                            each[5].release()

                prev_time += BLOCK_INTERVAL

            else:
                time.sleep(0.2)

            # Check if the PoS node is still in the verify committee
            if glovar.ComChange:
                each[6] = 0
                break

        logcontent = "The secondblock generation pocess is ended"
        self.logger.info(logcontent)

    # Broad the commit secondblock
    def broadSecondCommitBlock(self):

        for each in glovar.ComList:
            if each[1] == self.cominfo[1]:
                content = {'block':each[3]['newsecondblock'][0],'incomno':self.cominfo[0],'comid':self.cominfo[1],'commitnum':each[3]['secondcommit'],'comlist':each[3]['secondcommitlist']}
                beforesend = {'type':'secondblock','No':3,'content':content}
                temp = str(beforesend)
                hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
                senddata = {'messageid':hashvalue,'type':'secondblock','No':3,'content':content}

        for each in glovar.ComList:
            if each[1] != self.cominfo[1]:
                each[5].acquire()
                each[4].put(senddata)
                each[5].release()

        glovar.messageLock.acquire()
        glovar.MessageList.append(hashvalue)
        glovar.messageLock.release()
        broadMessage(senddata)
        logcontent = 'Broad a second commit block:' + str(senddata['content']['block'][1])
        self.logger.info(logcontent)

    # Add the block to the chain
    def addBlock(self, block):
        glovar.blockchainLock.acquire()
        if len(glovar.BLOCKCHAIN):
            if glovar.BLOCKCHAIN[len(glovar.BLOCKCHAIN)-1][1] != block[1]:
                glovar.BLOCKCHAIN.append(block)
                logcontent = 'Add a secondblock to the chain'
                self.logger.info(logcontent)
        else:
            glovar.BLOCKCHAIN.append(block)
            logcontent = 'Add a secondblock to the chain'
            self.logger.info(logcontent)
        glovar.blockchainLock.release()

        # Change the status of committee member
        for each in glovar.ComList:
            if each[1] == self.cominfo[1]:
                each[5].acquire()
                each[3]['verify'] = 0
                each[3]['secondblockhash'] = '0'
                each[3]['secondcommit'] = 0
                each[3]['secondcommitlist'].clear()
                each[3]['newsecondblock'].clear()
                each[5].release()

