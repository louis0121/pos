#!/usr/bin/env python3

import time, threading, random, logging, os, hashlib, json, queue#, pdb

import glovar

from network import broadMessage

# committee process               
class BlockProcessing(threading.Thread):
    def __init__(self, cominfo, logdirectory):
        threading.Thread.__init__(self)
        self.cominfo = cominfo
        self.logdirectory = logdirectory

    def run(self):
        filename = self.logdirectory + 'PoSnodelog.txt'
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

        # Select a leader to generate block
        randomstring = "".join(str(commember))
        idchoose = int(hashlib.sha256(randomstring.encode('utf-8')).hexdigest(), 16) % len(commember)

        logcontent = 'The ' + str(idchoose+1) + ' member: ' + str(commember[idchoose]) + ' is chosen to generate a block'
        self.logger.info(logcontent)

        # Self is selected
        transactions = []
        if comid == commember[idchoose]:
            # Add transactions into the new block
            for each in glovar.ComList:
                if comid == each[1]:
                    # If the PoS node has received transactions
                    if len(each[3]['transactionlist']):
                        for every in each[3]['transactionlist']:
                            transactions.append(every)
                        each[3]['transactionlist'].clear()

                    # Create a new transaction to add 
                    else:
                        trans_input_no = 1
                        trans_input_item = ['abc']
                        trans_input = [trans_input_no, trans_input_item]

                        trans_output_no = 1
                        trans_output_output1 = ['efg', 5]
                        trans_output_item = [trans_output_output1]
                        trans_output = [trans_output_no, trans_output_item]
                        timestamp = time.time()
                        temptransaction = [trans_input, trans_output, timestamp]
                        temp = str(temptransaction)
                        hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
                        newtransaction = [hashvalue, trans_input, trans_output, timestamp]
                        transactions.append(newtransaction)

            timestamp = time.time()
            temp = str(incomno) + str(comid) + str(commember) + str(timestamp)+ str(transactions)
            hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
            newblock = [incomno, comid, commember, timestamp, hashvalue, transactions]
            json_block = json.dumps(newblock)

            senddata = {'messageid':hashvalue,'type':'firstblock','No':1,'content':json_block}
            # Wait for other Pos node to start up receive process
            time.sleep(3)
            glovar.messageLock.acquire()
            glovar.MessageList.append(hashvalue)
            glovar.messageLock.release()
            broadMessage(senddata)

            self.logger.info('---------------------------------')
            logcontent = str(incomno) + ' :broadcast a block:' + str(hashvalue)
            self.logger.info(logcontent)

            # Change the corresponding global status
            for each in glovar.ComList:
                if comid == each[1]:
                    glovar.ComlistLock.acquire()
                    each[3]['genblock'] = 1
                    each[3]['blockhash'] = hashvalue
                    each[3]['stage'] = 1
                    each[3]['newblock'].append(newblock)
                    glovar.ComlistLock.release()
                    # Check if there is another PoS in the same committee
                    for every in glovar.ComList:
                        if (every[0] == incomno and every[1] != comid):
                            # Send data to this PoS node process
                            glovar.ComlistLock.acquire()
                            every[4].put(senddata)
                            glovar.ComlistLock.release()

        # Get message from its queue belong to this PoS node
        for each in glovar.ComList:
            if comid == each[1]:
                while True:
                    try:
                        data = each[4].get_nowait()
#                        logcontent = 'Get a data'
#                        self.logger.info(logcontent)
                        #broadMessage(data)
                        self.dataHandle(data)
                    except queue.Empty:
                        time.sleep(0.05)

                    # Check if the committee has changed
                    if glovar.ComChange:
                        each[6] = 0
                        break
        # End the process
        logcontent = 'The process is ended.'
        self.logger.info(logcontent)

    # Handle message for the generation committee
    def dataHandle(self, data):
        if data['type'] == 'transaction':
#            logcontent = "Handle a transaction:" + str(data['messageid'])
#            self.logger.info(logcontent)

            for each in glovar.ComList:
                if self.cominfo[1] == each[1]:
                    each[3]['transactionlist'].append(data['content'])

        if data['type'] == 'firstblock':
            # Verify whether it is commited by the committee member
            if data['No'] == 1:
#            logcontent = 'Handle a firstblock:' + str(data['messageid'])
#            self.logger.info(logcontent)
                blockdata = json.loads(data['content'])

                # Verify if the node is in our committee
                if blockdata[1] in self.cominfo[2]:
                    logcontent = 'Verify a firstblock:' + str(blockdata[4]) + ' from comid:' + str(blockdata[1]) + ' in committee:' +str(self.cominfo[0])
                    self.logger.info(logcontent)

                    # Change the corresponding global status
                    for each in glovar.ComList:
                        if self.cominfo[1] == each[1]:
                            # glovar.ComlistLock.acquire()
                            each[3]['newblock'].append(blockdata)
                            # glovar.ComlistLock.release()

                    # Send a commitment message
                    content = {'blockhash':blockdata[4],'incomno':blockdata[0],'comid':self.cominfo[1],'commit':1}
                    beforesend = {'type':'firstblock','No':2,'content':content}
                    temp = str(beforesend)
                    hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
                    senddata = {'messageid':hashvalue,'type':'firstblock','No':2,'content':content}

                    glovar.messageLock.acquire()
                    glovar.MessageList.append(hashvalue)
                    glovar.messageLock.release()
                    broadMessage(senddata)
                    logcontent = 'Send a commitment for block:' + str(senddata['content']['blockhash'])
                    self.logger.info(logcontent)

                    # Check if there is another PoS in the same committee
                    for each in glovar.ComList:
                        if each[0] == self.cominfo[0] and each[1] != self.cominfo[1]:
                            each[5].acquire()
                            each[4].put(senddata)
                            each[5].release()

            elif data['No'] ==2:
#                logcontent = 'Handle a commitment:' + str(data['messageid'])
#                self.logger.info(logcontent)

                # Verify whether it is commited by the committee member
                if data['content']['comid'] in self.cominfo[2]:
                    logcontent = 'Verify a commitment for block:' + str(data['content']['blockhash']) + ' from comid:' + str(data['content']['comid'])
                    self.logger.info(logcontent)

                for each in glovar.ComList:
                    if each[1] == self.cominfo[1]:
                        if each[3]['genblock']:
                            glovar.ComlistLock.acquire()
                            each[3]['commit'] += 1
                            each[3]['commitlist'].append(data['content']['comid'])
                            glovar.ComlistLock.release()
#                            logcontent = 'Block:' + str(each[3]['blockhash']) + ' receive a commit. Total:' + str(each[3]['commit'])
#                            self.logger.info(logcontent)

                            # Receive enough commitment
                            if (each[3]['commit'] >= glovar.Firstcommem//2+1):
#                                logcontent = 'Receive enough commitment for blocblock:' + str(each[3]['blockhash'])
#                                self.logger.info(logcontent)
                                self.broadFirstCommitBlock()
                                self.addBlock(each[3]['newblock'][0])

#                            logcontent = 'Run a new round to Generate a block'
#                            self.logger.info(logcontent)

            elif data['No'] == 3:
#                logcontent = 'Handle a commit firstblock:' + str(data['content']['block'][4])
#                self.logger.info(logcontent)

                # Verify the commit firstblock
                listisin = True
                for each in data['content']['comlist']:
                    if each not in self.cominfo[2]:
                        listisin = False
                        break
                if listisin:
                    logcontent = 'Verified the commit firstblock:' + str(data['content']['block'][4])
                    self.logger.info(logcontent)

                    for each in glovar.ComList:
                        if each[1] == self.cominfo[1]:
                            if len(each[3]['transactionlist']):
                                temptransactions = []
                                for every in each[3]['transactionlist']:
                                    if every not in data['content']['block'][5]:
                                        temptransactions.append(every)
                                each[3]['transactionlist'] = temptransactions.copy()

                            self.addBlock(data['content']['block'])

            else:
                logcontent = "Unkown data with data['type']:firstblock"
                self.logger.info(logcontent)

        # Receive a commit secondblock 
        elif data['type'] == 'secondblock' and data['No'] == 3:
            logcontent = 'Handle a commit secondblock:'
#            self.logger.info(logcontent)

        else:
            logcontent = 'Handle an unkown data'
            self.logger.info(logcontent)

    # Send the commit firstblock to last committee
    def broadFirstCommitBlock(self):

        for each in glovar.ComList:
            if self.cominfo[1] == each[1]:
                if len(each[3]['newblock']):
                    content = {'block':each[3]['newblock'][0],'incomno':each[0],\
                        'comid':each[1],'commitnum':each[3]['commit'],\
                        'comlist':each[3]['commitlist']}
                else:
                    return

                beforesend = {'type':'firstblock','No':3,'content':content}
                temp = str(beforesend)
                hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
                senddata = {'messageid':hashvalue,'type':'firstblock','No':3,'content':content}

        for each in glovar.ComList:
            if each[0] == self.cominfo[0] and each[1] != self.cominfo[1]:
                each[5].acquire()
                each[4].put(senddata)
                each[5].release()
            if each[0] == glovar.Firstcomno + 1:
                each[5].acquire()
                each[4].put(senddata)
                each[5].release()

        glovar.messageLock.acquire()
        glovar.MessageList.append(hashvalue)
        glovar.messageLock.release()
        broadMessage(senddata)
        logcontent = 'Broad a commit firstblock:' + \
        str(senddata['content']['block'][4])
        self.logger.info(logcontent)

    # Add the block to the chain
    def addBlock(self, block):
        glovar.firstchainLock.acquire()
        if len(glovar.FIRSTBLOCKCHAIN):
            if glovar.FIRSTBLOCKCHAIN[len(glovar.FIRSTBLOCKCHAIN)-1][4] != block[4]:
                glovar.FIRSTBLOCKCHAIN.append(block)
#                logcontent = 'Add a firstblock to the chain'
#                self.logger.info(logcontent)
        else:
            glovar.FIRSTBLOCKCHAIN.append(block)
#            logcontent = 'Add a firstblock to the chain'
#            self.logger.info(logcontent)
        glovar.firstchainLock.release()

        # Change the status of committee member
        for each in glovar.ComList:
            if each[1] == self.cominfo[1]:
#                newblock = []
#                commitlist = []
#                commitblocklist = []
#                comstatus = {'genblock':0,'blockhash':'0','stage':0,'commit':0,'commitlist':commitlist,'newblock':newblock,'verify':0,'commitblock':0,'commitblocklist':commitblocklist}
                each[5].acquire()
                each[3]['genblock'] = 0
                each[3]['blockhash'] = '0'
                each[3]['commit'] = 0
                each[3]['commitlist'].clear()
                each[3]['newblock'].clear()
                each[5].release()

#        self.logger.info('----------------------------------------------')
#        logcontent = 'Choose a new leader to Generate a block'
#        self.logger.info(logcontent)

        incomno = self.cominfo[0]
        comid = self.cominfo[1]
        commember = self.cominfo[2]
        # Select a leader to generate block
        randomstring = "".join(str(self.cominfo[2])) + str(block[1]) + str(block[4])
        idchoose = int(hashlib.sha256(randomstring.encode('utf-8')).hexdigest(), 16) % len(commember)

        logcontent = 'The ' + str(idchoose+1) + ' member: ' + str(commember[idchoose]) + ' is chosen to generate a block'
        self.logger.info(logcontent)

        # Self is selected
        transactions = []
        if comid == commember[idchoose]:
            # Add transactions into the new block
            for each in glovar.ComList:
                if comid == each[1]:
                    # If the PoS node has received transactions
                    if len(each[3]['transactionlist']):
                        for every in each[3]['transactionlist']:
                            transactions.append(every)
                        each[3]['transactionlist'].clear()

                    # Create a new transaction to add 
                    else:
                        trans_input_no = 1
                        trans_input_item = ['abc']
                        trans_input = [trans_input_no, trans_input_item]

                        trans_output_no = 1
                        trans_output_output1 = ['efg', 5]
                        trans_output_item = [trans_output_output1]
                        trans_output = [trans_output_no, trans_output_item]
                        timestamp = time.time()
                        temptransaction = [trans_input, trans_output, timestamp]
                        temp = str(temptransaction)
                        hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
                        newtransaction = [hashvalue, trans_input, trans_output, timestamp]
                        transactions.append(newtransaction)

            timestamp = time.time()
            temp = str(incomno) + str(comid) + str(commember) + str(timestamp)+ str(transactions)
            hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
            newblock = [incomno, comid, commember, timestamp, hashvalue, transactions]
            json_block = json.dumps(newblock)

            senddata = {'messageid':hashvalue,'type':'firstblock','No':1,'content':json_block}
            glovar.messageLock.acquire()
            glovar.MessageList.append(hashvalue)
            glovar.messageLock.release()
            broadMessage(senddata)

            self.logger.info('---------------------------------')
            logcontent = str(incomno) + ' :broadcast a block:' + str(hashvalue)
            self.logger.info(logcontent)

            # Change the corresponding global status
            for each in glovar.ComList:
                if comid == each[1]:
                    glovar.ComlistLock.acquire()
                    each[3]['genblock'] = 1
                    each[3]['blockhash'] = hashvalue
                    each[3]['newblock'].append(newblock)
                    glovar.ComlistLock.release()
                    # Check if there is another PoS in the same committee
                    for every in glovar.ComList:
                        if (every[0] == incomno and every[1] != comid):
                            # Send data to this PoS node process
                            each[5].acquire()
                            every[4].put(senddata)
                            each[5].release()
