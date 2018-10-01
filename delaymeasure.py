#!/usr/bin/env python3

import time, threading, logging, hashlib, queue

import glovar

from consistent import INIWAIT_TIME, RANBROAD_TIME, MEASURE_INTERVAL

from network import broadMessage

# Log the state of IDBLOCKCHAIN
class DelayMeasure(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory
        self.firstconfirm = 0

    def run(self):
        # Config the directory of log file
        filename = self.logdirectory + 'DelayMeasurelog.txt'
        self.logger = logging.getLogger('DelayMeasure')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info('Start delay measurement process')
        firstdelayname = self.logdirectory + '/firstdelay.txt'
        seconddelayname = self.logdirectory + '/seconddelay.txt'

        time.sleep(INIWAIT_TIME + 2*RANBROAD_TIME + 10)

        testtime = 10

        # for i in range(10):
        while True:
            self.firstconfirm = 0
            trans_input_no = 1
            trans_input_item = ['123']
            trans_input = [trans_input_no, trans_input_item]

            trans_output_no = 1
            trans_output_output1 = ['456', 1]
            trans_output_item = [trans_output_output1]
            trans_output = [trans_output_no, trans_output_item]

            timestamp = time.time()
            temptransaction = [trans_input, trans_output, timestamp]

            temp = str(temptransaction)
            hashvalue = hashlib.sha256(temp.encode('utf-8')).hexdigest()
            newtransaction = [hashvalue, trans_input, trans_output, timestamp]

            glovar.TransactionList.append(newtransaction)
            senddata = {'messageid':hashvalue,'type':'transaction','No':1,'content':newtransaction}
            glovar.messageLock.acquire()
            glovar.MessageList.append(hashvalue)
            glovar.messageLock.release()
            start_length = len(glovar.BLOCKCHAIN)
            start_time = time.time()
            # Start the firstblock confirmation process
            firstthread = threading.Thread(target=self.__firstCheck, args=(start_time, hashvalue, firstdelayname))
            firstthread.start()
            broadMessage(senddata)

            end_time = start_time - 1

            notfind = True
            while notfind:
                if len(glovar.BLOCKCHAIN) > start_length:
                    block = glovar.BLOCKCHAIN[start_length]
                    for each in block[7]:
                        if hashvalue == each[0]:
                            end_time = time.time()
                            notfind = False
                            break
                    start_length += 1
                else:
                    time.sleep(0.05)

            latency = end_time - start_time
            logcontent = "Transaction:" + str(hashvalue) + " final latency:" + str(latency)
            self.logger.info(logcontent)

            ftps = open(seconddelayname, 'a')
            output = str(latency) + "\n"
            ftps.write(output)
            ftps.close()

            while not self.firstconfirm:
                time.sleep(0.1)

        self.logger.info("Transaction delay measurement is over")

    # Check the firstblock confirmation process
    def __firstCheck(self, start_time, hashvalue, firstdelayname):

        notfind = True
        while notfind:
            try:
                data = glovar.FirstQueue.get_nowait()
#                logcontent = 'VerifyProcessing get a message:' + str(data)
#                self.logger.info(logcontent)
                translist = data['content']['block'][5]
                for each in translist:
                    if hashvalue == each[0]:
                        end_time = time.time()
                        notfind = False
                        break

            except queue.Empty:
                time.sleep(0.05)

        firstlatency = end_time - start_time
        logcontent = "Transaction:" + str(hashvalue) + " first latency:" + str(firstlatency)
        self.logger.info(logcontent)
        self.firstconfirm = 1

        ftps = open(firstdelayname, 'a')
        output = str(firstlatency) + "\n"
        ftps.write(output)
        ftps.close()

        for each in glovar.TransactionList:
            if hashvalue == each[0]:
                transconfirm = each.copy()
                break
        glovar.TransactionList.remove(transconfirm)
