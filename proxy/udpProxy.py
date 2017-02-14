#! /bin/python

# UDP Proxy by Eric Freudenthal with assistance from David Pruitt, Adrian Veliz, and Catherine Tabor

import sys, re
import time, random
import Queue
from select import select
from socket import *
from sys import exit

def usage():
    """ print usage information """
    print """usage: %s \n
          Option                                   Default     Description
         [--clientPort <port#>]                      50000     Client port number
         [--serverAddr host:port]          localhost:50001     Server port number

         [--byteRate <bytes-per-second>]             10000     Byterate at which to forward messages
         [--propLat <latency_secs>]                   0.01     Propogational Latency
         [--qCap <queue-capacity>]                       4     Maximium number of messages to queue

         [--pDelay <prob-delayed-msg>]                 0.0     Probability message delayed
             [--delayMin <sec>] [--delayMax <sec>      1.0       w/ uniform distribution
         [--pDrop <prob-drop-msg]                      0.0     Probability of message being dropped
         [--pDup <prob-dup-msg]                        0.0     Probability of a msg duplication 

         [--verbose]                                    off    Verbose Mode
         [--help]                                              This help screen""" % sys.argv[0]
    sys.exit(1)

def relTime(when):
   """ Time since program started """
   return when-startTime

###################### Initialization ##############################

# default values
startTime = time.time()                 # time the proxy was started at
toClientAddr = ("", 50000)              # client address
serverAddr = ("localhost", 50001)       # server port number
byteRate = 1.0e5                        # 100k bytes/sec (roughly 1Mbit/sec)
propLat = 1.0e-2                        # 10 ms
pDelay = 0.0
delayMin = 1.0                          # min delay 
delayMax = 1.0                          # max delay 
qCap = 4                                # queue capacity
pDrop = 0.0                             # drop probability
pDup = 0.0                              # duplicate probability
verbose = 0                             # verbose mode

try:
    args = sys.argv[1:]
    while args:
        sw = args[0]; del args[0]
        if sw == "--clientPort":
            toClientAddr = ("", int(args[0])); del args[0]
        elif sw == "--serverAddr":
            addr, port = re.split(":", args[0]); del args[0]
            serverAddr = (addr, int(port))
        elif sw == "--byteRate":
            byteRate = float(args[0]); del args[0]
        elif sw == "--propLat":
            propLat = float(args[0]); del args[0]
        elif sw == "--pDelay":
            print "pdelay!", args[0]
            pDelay = float(args[0]); del args[0]
        elif sw == "--delayMin":
            delayMin = float(args[0]); del args[0]
            if delayMin > delayMax:
                delayMax = delayMin
        elif sw == "--delayMax":
            delayMax = float(args[0]); del args[0]
        elif sw == "--qCap":
            qCap = int(args[0]); del args[0]
        elif sw == "--pDrop":
            pDrop = float(args[0]); del args[0]
        elif sw == "--pDup":
            pDup = float(args[0]); del args[0]
        elif sw == "-v" or sw == "--verbose":
            verbose = 1
        elif sw == "-h" or sw == "--help":
            usage();
        else:
            print "unexpected parameter %s" % sw
            usage();
except Exception as e:
    print "Error parsing arguments %s" % (e)
    usage()

#print parameters
print "argv=", sys.argv
print """Parameters: \nclientAddr=%s, serverAddr=%s, byteRate=%g, propLat=%g,
        pDelay=%f, delayMin=%d, delayMax=%d, qCap=%d, pDrop=%g, pDup=%g, verbose=%d""" % \
      (repr(toClientAddr), repr(serverAddr), byteRate, propLat, pDelay, delayMin, delayMax, qCap, pDrop, pDup, verbose)

# setup up connections
toServerSocket = socket(AF_INET, SOCK_DGRAM)  # outgoing socket

toClientSocket = socket(AF_INET, SOCK_DGRAM)  # incoming socket
toClientSocket.bind(toClientAddr)             # bind so we can listen on incoming port

# pair and name sockets
otherSocket = {toClientSocket:toServerSocket, toServerSocket:toClientSocket}
sockName = {toClientSocket:"toClientSocket", toServerSocket:"toServerSocket"}

# ready data structures
timeActions = Queue.PriorityQueue()           # minheap of (when, action).   <Action>() should be called at time <when>.

###################### Initialization complete ##############################

class TransmissionSim:
    def __init__(self, outSock, destAddr, byteRate, propLat, pDelay, delayMin, delayMax, qCap, pDrop, pDup):
        self.outSock, self.destAddr, self.byteRate, self.propLat =  \
         outSock, destAddr, 1.0*byteRate, propLat
        self.pDelay, self.delayMin, self.delayMax, self.qCap, self.pDrop, self.pDup = \
         pDelay, delayMin, delayMax, qCap, pDrop, pDup
        self.busyUntil = time.time()
        self.xmitCompTimes = []

    def scheduleDelivery(self, msg, eventQueue, duplicateMessage):
        """ returns a list of delivery times for a message"""
        deliveryTimes = {}
        now = time.time()
        if verbose:
            global sockName
            print "msg for %s rec'd at %f seconds" % (sockName[self.outSock], relTime(now))

        length = len(msg)
        q = self.xmitCompTimes  # flush messages transmitted in the past
        while len(q) and q[0] < now:
            del q[0]
        if len(q) >= self.qCap: # drop if q full
            if verbose: print "... queue full (oldest relTime = %f).  :(" % relTime(q[0])
            return

        # we really don't throttle (bytes/second) so a message is sent as a burst
        # we simulate throttling by sending the entire message at the time
        # it would be done if we were throttling

        # compute start and completion time if we were throttling
        startTransmissionTime = max(now, self.busyUntil)
        endTransmissionTime = startTransmissionTime + length/self.byteRate

        if verbose:
            print "... will be transmitted at reltime %f" % relTime(endTransmissionTime)
   
        q.append(endTransmissionTime) # in transmit q until transmitted
        self.busyUntil = min(self.busyUntil, endTransmissionTime) # earliest time for next msg

        deliveryTime = endTransmissionTime + self.propLat

        # check for drops
        if self.pDrop > random.random(): # random drops
            if verbose: print "... random drop ;)"
            return

        # add delay
        delay = 0
        if self.pDelay > random.random():
            delay = self.delayMin + random.random() * (self.delayMax - self.delayMin)
            if verbose: print ".. delaying %fs" % (delay)
        deliveryTime += delay

        if verbose: print "... scheduled for delivery at relTime %f" % relTime(deliveryTime)

        # check if we duplicate message
        if duplicateMessage is False and self.pDup > random.random():
            if verbose: print "Duplicating message ..."
            self.scheduleDelivery(msg, eventQueue, True) 

        if verbose: print "Message enqueued ... \n\n"    
        eventQueue.put((deliveryTime, lambda : TransmissionSim.deliver(self, msg)))

    def setDest(self, destAddr):
        """ update destination address """
        self.destAddr = destAddr

    def deliver(self, msg):
        """ deliver a message to the existing destination """
        if verbose: print "sending <%s> to %s at relTime=%f" % (msg, repr(self.destAddr), relTime(time.time()))
        self.outSock.sendto(msg, self.destAddr)

transmissionSims = {}                   # inSock -> simulatorForOutSock
for inSock, outAddr in ((toClientSocket, serverAddr), (toServerSocket, ("", None))): # client's addr will be set when msg rec'd
    # send to other sock!
    transmissionSims[inSock] = TransmissionSim(otherSocket[inSock],
                                               outAddr, byteRate, propLat, pDelay, delayMin, delayMax, qCap, pDrop, pDup) 

rSet = set([toClientSocket, toServerSocket])
wSet = set()
xSet = set([toClientSocket, toServerSocket])

while True:                             # forever
    now = time.time()
    sleepUntil = now+1.0                # default, 1s from now
    while not timeActions.empty():      # deal with all actions in the past
        when, action = timeActions.get() 
        if when > now:                  # if when in the future
            sleepUntil = min(sleepUntil, when) #   awaken no later than when
            timeActions.put((when, action)) # and put back in heap
            break;                          # done with scheduled events thus far
        action()                        # otherwise, when is in the past, therefore perform the action
    rReady, wReady, xReady = select(rSet, wSet, xSet, sleepUntil - now) # select uses relative time
    for sock in rReady:
        msg,addr = sock.recvfrom(2048)
        if sock == toClientSocket:      # if from client, update dest of toServer's transmission simulator 
            transmissionSims[toServerSocket].setDest(addr)
        transmissionSims[sock].scheduleDelivery(msg, timeActions, False)
         
    for sock in xReady:
        print "weird.  UDP socket reported an error.  Bye."
        sys.exit(1)

