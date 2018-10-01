#!/usr/bin/env python3

import time, threading, logging

import glovar

from consistent import INIWAIT_TIME, RANBROAD_TIME, MEASURE_INTERVAL

# Log the state of IDBLOCKCHAIN
class TpsMeasure(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory

    def run(self):
        # Config the directory of log file
        filename = self.logdirectory + 'TpsMeasurelog.txt'
        self.logger = logging.getLogger('TpsMeasure')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info('Start Tps measurement process')
        tpsrecordname = self.logdirectory + '/tpsrecord.txt'

        time.sleep(INIWAIT_TIME + 2*RANBROAD_TIME + 10)

        start_time = time.time()
        date_stamp = int(start_time)
        prev_time = date_stamp - (date_stamp % MEASURE_INTERVAL) + MEASURE_INTERVAL + 4
        start_length = len(glovar.BLOCKCHAIN)

        while True:
            date_stamp = time.time()
            if date_stamp > prev_time:
                end_length = len(glovar.BLOCKCHAIN)
                logcontent = "Start time: " + str(start_time) + " End time: " \
                + str(date_stamp) + " start length: " + str(start_length) + \
                " end length:" + str(end_length)
                self.logger.info(logcontent)

                blocklist = glovar.BLOCKCHAIN[start_length:(end_length)]
                firstblocknum = 0
                for each in blocklist:
                    firstblocknum += len(each[6])
                    logcontent = "This block cotains:" + str(len(each[6])) + \
                            " first blocks\n"# + str(each)
                    self.logger.info(logcontent)

                transactionsum = 4200 * firstblocknum
                tps = transactionsum / (date_stamp - start_time)

                ftps = open(tpsrecordname, 'a')
                output = str(tps) + "\n"
                ftps.write(output)
                ftps.close()

                self.logger.info('-----------------------------------')
                logcontent = "Firstblock total:" + str(firstblocknum) + " tps: " + str(tps)
                self.logger.info(logcontent)

                prev_time += MEASURE_INTERVAL
                start_time = int(time.time())
                start_length = len(glovar.BLOCKCHAIN)

            else:
                    time.sleep(0.5)

