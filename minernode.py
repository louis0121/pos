#!/usr/bin/env python3

# Copyright (C) 2018 Mining node
#
# This file is the main program of mining node.

# Check python version to make sure it executes under python3
import sys, os
if sys.version_info.major < 3:
    sys.stderr.write('Sorry, Python 3.x required by this example.\n')
    sys.exit(1)

# Import required packages
import glovar, configparser
from comselect import *
from msghandle import *
from network import *
from committee_generator import *
from tpsmeasure import *

# main function
def main():
    if len(sys.argv) < 4:
        print('Lack of parameters: logdirectory or bindport!')
        pwd = os.getcwd()
        logdirectory = pwd + '/log/1/'
#        clientconf = pwd + '/log/1/bitcoin.conf'
        bindport = 18000
        glovar.NodeId = 1
        meanode = 0
        print('Use the default logdirectory and bindport.\n',logdirectory,'\n',bindport)
    else:
        logdirectory = sys.argv[1]
#        clientconf = sys.argv[2]
        bindport = int(sys.argv[2])
        glovar.NodeId = int(sys.argv[3])
        meanode = int(sys.argv[4])

    # Read the configuration file and config network
    cf = configparser.ConfigParser()
    cfpath = logdirectory + 'clicf.ini'
    cf.read(cfpath)
    nodenumber = int(cf.get('baseconf', 'nodenumber'))
    for i in range(nodenumber):
        host = 'host' + str(i+1)
        port = 'port' + str(i+1)
        hostip = cf.get('baseconf', host)
        hostport = cf.get('baseconf', port)
        glovar.confnode.append((hostip, int(hostport)))
    glovar.Stakemin = int(cf.get('baseconf', 'stakemin'))
    glovar.Stakemax = int(cf.get('baseconf', 'stakemax'))
    glovar.Firstcommem = int(cf.get('baseconf', 'firstcommem'))
    glovar.Firstcomno = int(cf.get('baseconf', 'firstcomno'))
    glovar.Secondcommem = int(cf.get('baseconf', 'secondcommem'))
    glovar.Stakesum = int(cf.get('baseconf', 'stakesum'))

    # Start network layer service
    tcp_server = TcpServer(SERVER_ADDR, bindport, CONNECTIONMAX, logdirectory)
    tcp_server.start()
    msg_handle = msghandle(logdirectory)
    msg_handle.start()
    msg_broad = BroadMsg(logdirectory)
    msg_broad.start()
    # Connect to config network node
    time.sleep(3)
    tcp_connect = ConnectionCreation(logdirectory)
    tcp_connect.start()

    # Start protocol process
    time.sleep(3)
    user_comselection = RanselectProcessing(logdirectory)
    user_comselection.start()
    new_comgeneration = CommitteeGeneration(logdirectory)
    new_comgeneration.start()

    if meanode:
#        print('NodeId: ', glovar.NodeId, ' is a tps measure node.')
        tpsprocess = TpsMeasure(logdirectory)
        tpsprocess.start()

# Execute as main program
if __name__ == '__main__':
    main()

