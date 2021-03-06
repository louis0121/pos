#!/usr/bin/env python3
import threading, queue

# Synchronous lock used in program
genranLock = threading.Lock()

# Netowrk config and global status
confnode = []
CONNECTION_LIST = []	# Node connection list
CONNECTEDADDR_LIST = []
CONNECTION_NUMBER = 0

conLock = threading.Lock() # Network status lock
broadLock = threading.Lock() # Broad message queue lock

broadqueue = queue.Queue()

# Message handle status
msgLock = threading.Lock()
msgqueue = queue.Queue() # From network to message handle
messageLock = threading.Lock()
MessageList = [] # Record message id that has been received

# Node information
NodeId = 0
Stakesum = 0
Stakemin = 0
Stakemax = 0
Firstcommem = 0
Firstcomno = 0
Secondcommem = 0

# Mining data
ranLock = threading.Lock() # Random value for committi selection
RanList = [] # Record random number has been received
hashLock = threading.Lock() # Hash value list status lock
HashList = []
HashSeed = 0
PosList = []
ComList = []
ComlistLock = threading.Lock()
ComChange = 0
TransactionList = []
TransLock = threading.Lock()
FirstQueue = queue.Queue()

# State of blockchain 
FIRSTBLOCKCHAIN = []
firstchainLock = threading.Lock()
BLOCKCHAIN = []
blockchainLock = threading.Lock()

####################################

# Not used
NewComList = []
newComLock = threading.Lock()
NewRanList = []
newRanLock = threading.Lock()
NewHashList = []
newHashLock = threading.Lock()
NewHashSeed = 0
NewPosList = []
newcomqueue = queue.Queue()
newComqueueLock = threading.Lock()


#threadLock = threading.Lock()


# State of blockchain and mining parameters
#MINING_TARGET = int('000122d3f4210c9fb88d8da10a2f86d08d28700c2770a7481ac4fab072f31458', 16)
#PREV_BLOCKHASH = 0
#MINEDBLOCK_HEIGHT = 1


