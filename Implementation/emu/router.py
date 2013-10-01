'''
The MIT License (MIT)

Copyright (c) 2013 wilko.henecka@adelaide.edu.au

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import os
import cPickle as pickle
from emu.messages import DVAnnouncement
from emu.messages import Announcement
from emu.messages import SPCRequest
from emu.messages import SPCResponse
import logging
import threading
import time
from operator import attrgetter
import random
from Paillier import encrypt, add, decrypt
from datetime import datetime
from twisted.internet import reactor
from zlib import crc32

logger = logging.getLogger('logger')



class STRIPRouter(object):
    def __init__(self, config):
        #the forwading information base. format: {target: [nextHop, enc(distance)]}
        self.fib = {}
        #the reachability information base. format: {target: ([nextHops], waitingForAnnouncements, spcomputationstarted, newSPCrequested)}
        self.rib = {}
        #the routers identity
        self.identity = config.get('server','identity')
        self.distances = dict(zip(config.get('neighbours', 'targets').split(','),map(int,config.get('neighbours','distances').split(','))))
        self.keystore = {}
        self._readKeys(config.get('server','keyfiles'))
        self.connections = {}
        self.cidstore = {}
        self.annDelay = float(config.get('server','AnnouncementDelay'))
        self.waitForMoreRequestsDelay = float(config.get('server','WaitForMoreRequestsDelay'))
        self.waitForResponsesDelay = float(config.get('server','WaitForResponsesDelay'))
        self.waitForRepliesDelay = 2 * self.waitForResponsesDelay
        self.trrt = {} #temporary response routing table
        self.cids = {} #holds all the requests to a pid while in processing
        self.rcids = {}
        #self.fibFile = self.identity + '.fib'
        self.fibFile = config.get('logging','fibfile')
        self.measurement = Measurement(config.get('logging', 'measurementfile'))
        
    def startup(self):
        try:
            os.remove(self.fibFile)
        except:
            pass
    
    def shutdown(self):
        self.measurement.writeToFile()
    
    def getNextHop(self, target):
        return self.rib[target]

    def getDistance(self, target):
        return self.distances[target]

    def getPublicKey(self, target):
        return self.keystore[target]
    
    def addTargetToRibAndFib(self, target):
        self.rib[target] = target
        try:
            d = self.fib[target]
            if d<self.getDistance(target):
                return
        except:
            pass
        self.fib[target] = target
    
    def _readKeys(self, path):
        keyFiles = os.listdir(path)
        for keyFile in keyFiles:
            if keyFile[-2:] == 'pk':
                self.keystore[keyFile[:-3]]=pickle.load(open("%s/%s" %(path,keyFile),'r'))
            if keyFile == '%s.sk' % self.identity:
                self.sk = pickle.load(open("%s/%s" %(path,keyFile),'r'))

    def addConnection(self, partner, connection):
        self.connections[partner] = connection
        #send him announcements for all entries in the fib
        for target, nexthop in self.fib.iteritems():
            self.connections[partner].sendMessage(Announcement(target, self.identity))
        #now update rib and fib
        self.updateInformationBase(partner, partner)

    def updateInformationBase(self, target, nexthop):
        if target == self.identity:
            return
        #now the rib
        try:
            entries, wfa, spcs, nsr = self.rib[target]
            if not nexthop in entries:
                entries.append(nexthop)

        except: #no entries for target yet
            entries = [nexthop]
            self.rib[target] = [entries,False, False, None]
        #now update fib
        #if the waitForAnnouncement flag is set, then we don't have to do anything
        if not self.rib[target][1]:
            #lets see if a spc is already running
            if self.rib[target][2]:
                if self.rib[target][3] == None:
                    self.rib[target][3] = time.time()
            else:
                SPComputationThread(target, self).start()
        logger.info('rib updated: %s' % self.rib)
    
    def updateFIB(self, target, nexthop, distance, issmaller):
        if target in self.fib:
            oldNextHop, oldDistance = self.fib[target]
            if oldNextHop == nexthop:
                if not issmaller:
                    return
        self.fib[target] = [nexthop, distance]
        logger.debug('fib updated: %s' % self.fib)
        self.dumpFib()
        self.sendAnnouncementToNeighbours(target, nexthop)
    
    def dumpFib(self):
        f = open(self.fibFile,'a')
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S '))
        f.write(', '.join(['%s:%s(%d)' % (target,data[0],crc32(str(data[1]))) for target, data in self.fib.iteritems()]))
        f.write('\n')
        f.close()
    
    def sendAnnouncementToNeighbours(self, target, nexthop):
        ann = Announcement(target, self.identity)
        for neighbour, connection in self.connections.iteritems():
            if not neighbour == nexthop:
                reactor.callFromThread( connection.sendMessage, ann )
        
    def processSPCRequest(self, request):
        if self.identity == request.target:
            #first check the timestamp
            ct = datetime.now()
            delta = ct - request.timestamp
            if delta.total_seconds() > self.waitForMoreRequestsDelay:
                logger.info('drop old request: %s' % request)
                return
            
            #first check if we are already waiting...
            if request.cid in self.cids:
                self.cids[request.cid].append(request)
            #if not, start waiting thread
            else:
                self.cids[request.cid] = [request]
                wait = self.waitForMoreRequestsDelay - delta.total_seconds()
                ProcessingRequestThread(request.cid, self, wait).start()
            
        else:
            try:
                if (request.cid, request.pid) in self.trrt:
                    #then we have a loop!
                    logger.info('found a loop for (%d, %d) at %s' % (request.cid, request.pid, str(self.identity)))
            except:
                #no entry in trrt. Everything is fine
                pass
            nexthop = self.fib[request.target][0]
            dist = self.distances[nexthop]
            #update distance
            pk = self.keystore[request.target]
            edist = encrypt(dist, pk)
            self.measurement.addEncryption()
            request.distance = add(request.distance, edist, pk)
            #store route for response
            self.trrt[(request.cid, request.pid)] = request.lasthop
            request.lasthop = self.identity
            #send request to nexthop
            self.connections[nexthop].sendMessage(request)
    
    def processSPCResponse(self, response):
        if response.cid in self.cidstore:
            #then we initiated this computation
            #first check if in time
            ct = datetime.now()
            delta = ct - response.timestamp
            if delta.total_seconds() > self.waitForResponsesDelay:
                logger.info('drop old response: %s' % response)
                return
            #then decrypt shortest pid and compare to response.pid
            cinfo = self.cidstore[response.cid]
            key = cinfo[0]
            pid, smaller = self.sdecrypt(response.spid, key)
            dist = key ^ response.dist
            #if they match, than add to self.cids
            if pid == response.pid:
                cinfo[3] = pid
                cinfo[4] = smaller
                cinfo[5] = dist
                logger.info('shortest path for %d is %d. smaller: %s' % (response.cid, pid, str(smaller)))
            else:
                pass
        else:
            #we have to pass it on...
            try:
                nexthop = self.trrt[(response.cid, response.pid)]
                del self.trrt[(response.cid, response.pid)]
                self.connections[nexthop].sendMessage(response)
            except Exception, err:
                logger.error('Error in handling response: %s' % err)
    
    def processAnnouncement(self, ann):
        
        self.updateInformationBase(ann.target, ann.nexthop)
               
    def sdecrypt(self, cipher, key):
        t = cipher ^ key
        smaller = t % 2 == 1
        pid = t>>1
        return pid, smaller
    
class SPComputationThread(threading.Thread):
    def __init__(self, target, router, noOfTries=1):
        self.router = router
        self.target = target
        self.noOfTries = noOfTries
        logger.info('SPCThread created for target %s' % self.target)
        threading.Thread.__init__ ( self )
            
    def run(self):
        #first wait for more announcement
        self.router.rib[self.target][1] = True
        #we have to randomize the sleep time here
        waittime = self.router.annDelay
        if self.router.rib[self.target][3] != None:
            delta = time.time() - self.router.rib[self.target][3]
            waittime = waittime - delta
            self.router.rib[self.target][3] = None
        if waittime < 0:
            waittime = 0
        t = self.noOfTries*waittime
        ti = t/2 + random.random()*t
        logger.debug('sleeping for %f sec' % ti)
        time.sleep(ti)
        #send request to all hops in rib
        #create request
        cid = random.randint(0,(1<<32)-1)
        tpk = self.router.keystore[self.target]
        try:
            olddistance = self.router.fib[self.target][1]
        except:
            olddistance = encrypt(0, tpk)
            self.router.measurement.addEncryption()
        key = random.randint(0,(1<<64)-1)
        ekey = encrypt(key, tpk)
        self.router.measurement.addEncryption()
        ts = datetime.now()
        #send it out
        self.router.rib[self.target][2] = True
        candidates = self.router.rib[self.target][0]
        self.router.rib[self.target][1] = False
        piddict = {}
        for candidate in candidates:
            pid = random.randint(0,(1<<16)-1)
            piddict[pid] = candidate
            distance = encrypt(self.router.distances[candidate], tpk)
            self.router.measurement.addEncryption()
            req = SPCRequest(self.target, distance, cid, pid, ekey, self.router.identity, olddistance, ts)
            reactor.callFromThread(self.router.connections[candidate].sendMessage, req)
            logger.info('sending SPCR(%d) to %s (%d)' % (cid,candidate, pid))
            #self.router.connections[candidate].sendMessage(req)
        self.router.cidstore[cid] = [key, self.target, piddict, None, None, None]
        #start waitingForReplies
        logger.debug('waiting for %f sec for replies to come' % self.router.waitForRepliesDelay)
        time.sleep(self.router.waitForRepliesDelay)
        #TODO: extend here!
        #then update fib or if computation fails start again...
        res = self.router.cidstore[cid]
        if res[3] == None or res[4] == None:
            #then we didn't get a valid result... poo
            logger.info('computation %d for target %s was unsuccessful. Lets try again' % (cid,self.target))
            if not self.router.rib[self.target][1]:
                SPComputationThread(self.target, self.router, noOfTries=self.noOfTries+1).start()
            
            #maybe we want to try again?
        else:
            #write it in the fib
            logger.info('comp. result (%d): target: %s, nextHop: %s, issmaller: %s' % (cid, res[1], res[2][res[3]], str(res[4])))
            logger.info('res: %s' % res)
            self.router.updateFIB(res[1], res[2][res[3]], res[5], res[4])
            if self.router.rib[self.target][3] != None:
                SPComputationThread(self.target, self.router).start()
        self.router.rib[self.target][2] = False
            
class ProcessingRequestThread(threading.Thread):
    def __init__(self, cid, router, wait):
        self.cid = cid
        self.router = router
        self.wait = wait
        logger.info('ProcessingRequestThread created for cid %s' % self.cid)
        threading.Thread.__init__ ( self )
        
    def run(self):
        #first wait
        logger.debug('waiting for %f sec for more requests' % self.wait)
        time.sleep(self.wait)
        #get all requests
        requests = self.router.cids[self.cid]
        logger.info('received %d messages for request %d. %s' %(len(requests), self.cid, str(requests)))
        #find the minimum
        mpid = None
        mdist = None
        mdist_enc = None
        for request in requests:
            if mpid == None:
                mpid = request.pid
                mdist = decrypt(request.distance, self.router.sk)
                mdist_enc = request.distance
            else:
                dis = decrypt(request.distance, self.router.sk)
                if dis < mdist:
                    mdist = dis
                    mpid = request.pid
                    mdist_enc = request.distance
        #compare distance to oldDistance
        
        request = requests[0]
        shorterDist = mdist < decrypt(request.olddistance, self.router.sk)
        #prepare replies
        key = decrypt(request.key, self.router.sk)
        res = mpid << 1
        if shorterDist:
            res += 1
        res = res ^ key
        dist = key ^ mdist_enc
        logger.info('PRT %d: shortestPath: %d with %d distance. issmaller: %s' % (self.cid, mpid, mdist, str(shorterDist)))
        logger.debug('old distance was: %d' % decrypt(request.olddistance, self.router.sk))
        for request in requests:
            response = SPCResponse(self.cid, request.pid, res, request.timestamp, dist)
            reactor.callFromThread(self.router.connections[request.lasthop].sendMessage, response)
            #self.router.connections[request.lasthop].sendMessage(response)
        #clean up. remove requests from self.router.pids
        del self.router.cids[self.cid]


            
class RIBEntry(object):
    def __init__(self, nexthop, distance, path):
        self.nexthop = nexthop
        self.distance = distance
        self.path = path
    def __repr__(self):
        return 'nh: %s, d: %d, p: %s' %(self.nexthop,self.distance, self.path)
    def __eq__(self, other):
        return self.nexthop == other.nexthop
        
class DVRouter(object):
    def __init__(self, config):
        #the forwading information base. format: {target: (nextHop, dist, path)}
        self.fib = {}
        #the reachability information base. format: {target: ([RIBEntry],spComputationStarted)}
        self.rib = {}
        #the routers identity
        self.identity = config.get('server','identity')
        self.distances = dict(zip(config.get('neighbours', 'targets').split(','),config.get('neighbours','distances').split(',')))
        self.connections = {}
        self.annDelay = float(config.get('server','AnnouncementDelay'))
    
    def updateInformationBase(self, target, distance, nexthop, path):
        if self.identity in path:
            #then we have a loop
            logging.debug('drop message because of a loop.')
            return
        distance += int(self.distances[nexthop])
        #now the rib
        newEntry = RIBEntry(nexthop, distance, path)
        try:
            entries,spcs = self.rib[target]
            if newEntry in entries:
                entries[entries.index(newEntry)] = newEntry
            else:
                entries.append(newEntry)
        except: #no entries for target yet
            entries = [newEntry]
            self.rib[target] = [entries,False]
        logger.info('rib: %s' % self.rib)
        #now update fib
        
        #first find the shortest distance to target 
        minhop = nexthop
        mindist = distance
        minpath = path
        for entry in entries:
            if entry.distance<mindist:
                minhop = entry.nexthop
                mindist = entry.distance
                minpath = entry.path
        try:
            oldhop, olddist, oldpath = self.fib[target]
            if minhop != oldhop or mindist != olddist:
                self.fib[target] = (minhop, mindist, minpath)
                logger.info('fib changed: %s' % self.fib)        
                AnnouncementDelayThread(target, self).start()
            else:
                #no change, no announcement
                pass
        except:
            #no entry for target in fib
            self.fib[target] = (minhop, mindist, minpath)
            logger.info('fib changed: %s' % self.fib)
            self.sendAnnouncement(target, minhop, mindist, minpath)
    
    def sendAnnouncement(self, target, nexthop, dist, path):
        anpath = list(path)
        anpath.append(self.identity)
        nl = []
        for neighbour in self.connections:
            if not neighbour == nexthop:
                self.connections[neighbour].sendMessage(DVAnnouncement(target, self.identity, dist, anpath))
                nl.append(neighbour)
        if len(nl) > 0:
            logger.info('sending annoucement: (%s,%s,%d,%s) to %s' % (target, self.identity, dist, str(anpath), nl))
                
        
    def addConnection(self, partner, connection):
        self.connections[partner] = connection
        #send him announcements for all entries in the fib
        for target, entry in self.fib.iteritems():
            path = list(entry[2])
            path.append(self.identity)
            self.connections[partner].sendMessage(DVAnnouncement(target, self.identity,entry[1], path))
        #now update rib and fib
        self.updateInformationBase(partner, 0, partner, [partner])
        
    def sendFib(self, callback):
        for target, entry in self.fib.iteritems():
            path = list(entry[2])
            path.append(self.identity)
            callback(DVAnnouncement(target, self.identity,entry[1], path))

        
    def removeConnection(self, target):
        del self.connections[target]
    
    def processDVAnnouncement(self, announcement):
        self.updateInformationBase(announcement.target, announcement.distance, announcement.nexthop, announcement.path)
        
        
class AnnouncementDelayThread(threading.Thread):
    def __init__(self, target, router):
        self.router = router
        self.target = target
        logger.debug('annDelayThread created for target %s' % self.target)
        threading.Thread.__init__ ( self )
            
    def run(self):
        self.router.rib[self.target][1] = True
        logger.debug('sleeping for %f sec' % self.router.annDelay)
        time.sleep(self.router.annDelay)
        self.router.rib[self.target][1] = False
        entries = self.router.rib[self.target][0]
        entry = sorted(entries, key=attrgetter('distance'))[0]
        self.router.sendAnnouncement(self.target, entry.nexthop, entry.distance, entry.path)
        
class Measurement:
    def __init__(self, path):
        self.filename = path
        self.lock = threading.Lock()
        self.encryptions = 0
        self.announcements = 0
        self.othermessages = 0
    
    def addEncryption(self):
        with self.lock:
            self.encryptions += 1
    
    def addAnnouncement(self):
        with self.lock:
            self.announcements += 1
    
    def addOtherMessage(self):
        with self.lock:
            self.othermessages += 1
    
    def writeToFile(self):
        f = open(self.filename, 'w')
        f.write('encryptions: %d\n' % self.encryptions)
        f.write('announcements: %d\n' % self.announcements)
        f.write('other messages: %d\n' % self.othermessages)
        f.close()
    