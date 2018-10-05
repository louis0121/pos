#!/usr/bin/env python3

import socket, threading, time, json, sys, hashlib, logging

import glovar

from network import broadMessage

# Message handle function
class msghandle(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory

    def run(self):
        filename = self.logdirectory + 'msghandlelog.txt'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.logger.info('Start Message handle thread process')

        while True:
            message = glovar.msgqueue.get()
#            logcontent = "Messages in the queue:" + str(glovar.msgqueue.qsize())
#            self.logger.info(logcontent)
            self.connectednode = message[0]
            msgdata = message[1]
            self.addr = message[2]
            data = json.loads(msgdata.decode('utf-8'))
#            logcontent = 'Receive data: ' + str(data)
#            self.logger.info(logcontent)

            # The first time to receive this message
            if (data['messageid'] not in glovar.MessageList) and ((not glovar.ComChange) or \
                        (glovar.ComChange and data['type'] == 'comrandom')) :
                glovar.messageLock.acquire()
                glovar.MessageList.append(data['messageid'])
                glovar.messageLock.release()

#                logcontent = "Message:" + str(data)
#                self.logger.info(logcontent)

                # Receive a committee formation message
                if data['type'] == 'comrandom':
                    self.__comrandom_handle(data)

                # Receive a block generated by first committee
                elif data['type'] == 'firstblock':
                    self.__firstblock_handle(data)

                # Receive a block generated by the second committee
                elif data['type'] == 'secondblock':
                    self.__secondblock_handle(data)

                # Receive a newcommitte generation message
#                elif data['type'] == 'newcommittee':
#                    self.__newcommittee_handle(data)

                # Receive a transaction 
                elif data['type'] == 'transaction':
                    self.__transaction__handle(data)

                # Unkown received data
                else:
                    logcontent = "Unkown data with data['type']:" + \
                    str(data['type'])
                    self.logger.info(logcontent)

    # Handle mined id information
    def __comrandom_handle(self, data):
        # Receive a random number
        if data['No'] == 1:
            logcontent = 'Handle a random number:' + str(data['content']['genrandom'])
            self.logger.info(logcontent)

            glovar.ranLock.acquire()
            glovar.RanList.append(str(data['content']['genrandom']))
            glovar.ranLock.release()

            broadMessage(data)

#                logcontent = ' Broad this committee random number again: ' + str(data['genrandom'])
#                self.logger.info(logcontent)
        # Receive a hashseed
        elif data['No'] == 2:
            logcontent = ' Receive a hashvalue:' + str(data['content']['ranhash'])
            self.logger.info(logcontent)
#            msgnum = glovar.msgqueue.qsize()
#            if glovar.msgqueue.empty():
#                self.logger.info("The msgqueue is empty")
#            logcontent = "Number of messages in the msgqueue is:" + str(msgnum)
#            self.logger.info(logcontent)

            glovar.hashLock.acquire()
            glovar.HashList.append(data['content']['ranhash'])
            glovar.hashLock.release()

            broadMessage(data)

            if ( glovar.HashSeed == 0 or data['content']['ranhash'] < glovar.HashSeed ):
                logcontent = "Replace HashSeed:\n" +str(glovar.HashSeed) + \
                        " with hashvalue:\n" + str(data['content']['ranhash'])
                self.logger.info(logcontent)
                glovar.hashLock.acquire()
                glovar.HashSeed = data['content']['ranhash']
                glovar.hashLock.release()

#                    logcontent = 'Broad this hashvalue again: ' + str(data['ranhash'])
#                    self.logger.info(logcontent)

        else:
            logcontent = "Unkown newcommittee with data['No']:" + str(data['No'])
            self.logger.info(logcontent)

    # Handle the first block
    def __firstblock_handle(self, data):
        broadMessage(data)
        # Receive a data block
        if data['No'] == 1:
#            logcontent = 'Receive a firstblock:' + str(data['messageid'])
#            self.logger.info(logcontent)

            # This node is selected in at least one committees
            if len(glovar.ComList):
                blockdata = json.loads(data['content'])
                for each in glovar.ComList:
                    # The block is generated by this committee
                    if blockdata[0] == each[0]:
                        glovar.ComlistLock.acquire()
                        each[4].put(data)
                        glovar.ComlistLock.release()

        # Receive a block commition message
        elif data['No'] == 2:
#            logcontent = 'Receive a commitment:' + str(data['messageid'])
#            self.logger.info(logcontent)

            # This node is selected in at least one committees
            if len(glovar.ComList):
                for each in glovar.ComList:
                    if data['content']['incomno'] == each[0]:
                        each[5].acquire()
                        each[4].put(data)
                        each[5].release()

        # Receive a commit firstblock
        elif data['No'] == 3:
#            logcontent = 'Receive a commit firstblock:' + \
#            str(data['content']['block'][4])
#            self.logger.info(logcontent)

            # This node is selected in at least one committees
            if len(glovar.ComList):
                for each in glovar.ComList:
                    if data['content']['incomno'] == each[0]:
                        each[5].acquire()
                        each[4].put(data)
                        each[5].release()
                    if each[0] == glovar.Firstcomno + 1:
                        each[5].acquire()
                        each[4].put(data)
                        each[5].release()

            # This node has send a transaction waiting for confirmation
            if len(glovar.TransactionList):
                glovar.FirstQueue.put(data)
#                logcontent = "Check the firstblock for confirmation:" + str(data['content']['block'][4])
#                self.logger.info(logcontent)

        else:
            logcontent = "Unkown data['type']:firsblock"
            self.logger.info(logcontent)

    # Handle the secondlock information
    def __secondblock_handle(self, data):
        broadMessage(data)
        # Receive a secondblock
        if data['No'] == 1:
#            logcontent = 'Receive a secondblock:' + str(data['messageid'])
#            self.logger.info(logcontent)

            # This node is selected in at least one committees
            if len(glovar.ComList):
                blockdata = data['content']
                for each in glovar.ComList:
                    # The block is generated by this committee
                    if blockdata[2] == each[0]:
                        each[5].acquire()
                        each[4].put(data)
                        each[5].release()

        # Receive a secondblock commition 
        elif data['No'] == 2:
#            logcontent = 'Receive a second commitment:' + \
#            str(data['content']['blockhash'])
#            self.logger.info(logcontent)

            # This node is selected in at least one committees
            if len(glovar.ComList):
                for each in glovar.ComList:
                    if data['content']['incomno'] == each[0]:
                        each[5].acquire()
                        each[4].put(data)
                        each[5].release()

        # Receive a commit secondblock
        elif data['No'] == 3:
#            logcontent = 'Receive a commit secondblock:' + \
#            str(data['content']['block'][1])
#            self.logger.info(logcontent)

            # This node is selected in any committee
            if len(glovar.ComList):
                for each in glovar.ComList:
#                    if each[0] == glovar.Firstcomno + 1:
                    each[5].acquire()
                    each[4].put(data)
                    each[5].release()
#                        logcontent = 'transmit a commit firstblock to generation committee'
#                        self.logger.info(logcontent)
            else:
                glovar.blockchainLock.acquire()
                if len(glovar.BLOCKCHAIN):
                    if glovar.BLOCKCHAIN[len(glovar.BLOCKCHAIN)-1][1] != data['content']['block'][1]:
                        glovar.BLOCKCHAIN.append(data['content']['block'])
#                        logcontent = 'Add a secondblock to the chain'
#                        self.logger.info(logcontent)
                else:
                    glovar.BLOCKCHAIN.append(data['content']['block'])
#                    logcontent = 'Add a secondblock to the chain'
#                    self.logger.info(logcontent)
                glovar.blockchainLock.release()

        else:
            logcontent = "Unkown data['type']:secondblock"
            self.logger.info(logcontent)

    # Handle idblock information
    def __newcommittee_handle(self, data):
#        glovar.newComqueueLock.acquire()
        glovar.newcomqueue.put(data)
#        glovar.newComqueueLock.release()
#        logcontent = 'Receive a new committee message:' + str(data['messageid'])
#        self.logger.info(logcontent)

    # Handle the transaction
    def __transaction__handle(self, data):
        broadMessage(data)

        comchoose = int(data['messageid'], 16) % glovar.Firstcomno + 1
        # This node is selected in at least one first committees
        if len(glovar.ComList):
            for each in glovar.ComList:
                # The block is generated by this committee
                if comchoose == each[0]:
                    # glovar.ComlistLock.acquire()
                    each[4].put(data)
                    # glovar.ComlistLock.release()
