#!/usr/bin/env python3

import time, threading, logging, hashlib

import glovar

from consistent import INIWAIT_TIME, RANBROAD_TIME, MEASURE_INTERVAL

from network import broadMessage

# Log the state of IDBLOCKCHAIN
class DelayMeasure(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory

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
        tpsrecordname = self.logdirectory + '/delayrecord.txt'

        time.sleep(INIWAIT_TIME + 2*RANBROAD_TIME + 10)

        testtime = 10

        for i in range(10):
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
            
            senddata = {'messageid':hashvalue,'type':'transaction','No':1,'content':newtransaction}
            glovar.messageLock.acquire()
            glovar.MessageList.append(hashvalue)
            glovar.messageLock.release()
            start_length = len(glovar.BLOCKCHAIN)
            broadMessage(senddata)
            
            start_time = int(time.time())
            end_time = start_time
            
            notfind = True
            while notfind:
                if len(glovar.BLOCKCHAIN) > start_length:
                    block = glovar.BLOCKCHAIN[start_length]
                    for each in block[7]:
                        if hashvalue == each[0]:
                            end_time = int(time.time())
                            notfind = False
                            break
                    start_length += 1
                else:
                    time.sleep(0.05)

            latency = end_time - start_time
            logcontent = "Transaction:" + str(hashvalue) + " latency:" + str(latency)
            self.logger.info(logcontent)


#        while True:
#            date_stamp = int(time.time())
#            if date_stamp > prev_time:
#                end_length = len(glovar.BLOCKCHAIN)
#                logcontent = "Start time: " + str(start_time) + " End time: " \
#                + str(date_stamp) + " start length: " + str(start_length) + \
#                " end length:" + str(end_length)
#                self.logger.info(logcontent)
#
#                blocklist = glovar.BLOCKCHAIN[start_length:(end_length)]
#                firstblocknum = 0
#                for each in blocklist:
#                    firstblocknum += len(each[6])
#                    logcontent = "This block cotains:" + str(len(each[6])) + \
#                            " first blocks\n" + str(each)
#                    self.logger.info(logcontent)
#
#                transactionsum = 4200 * firstblocknum
#                tps = transactionsum / (date_stamp - start_time)
#
#                ftps = open(tpsrecordname, 'a')
#                output = str(tps) + "\n"
#                ftps.write(output)
#                ftps.close()
#
#                self.logger.info('-----------------------------------')
#                logcontent = "Firstblock total:" + str(firstblocknum) + " tps: " + str(tps)
#                self.logger.info(logcontent)
#
#                prev_time += MEASURE_INTERVAL
#                start_time = int(time.time())
#                start_length = len(glovar.BLOCKCHAIN)
#
#            else:
#                    time.sleep(0.5)

