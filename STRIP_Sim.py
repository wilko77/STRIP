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

from SimPy.Simulation import *
#from SimPy import SimulationTrace
import networkx as nx
import logging
import os
import string
import cPickle
import Utils
import math

logging.basicConfig(filename='strip.log', level=logging.ERROR)

class RCComputation(Process):
    
    def __init__(self, name='a_process', sim=None):
        Process.__init__(self, name=name, sim=sim)
        self.repliesReceived = []
        self.repliesTimes = []
        self.shortestPath = []
        self.spDistance = -1
        self.distanceChanged = True
        self.repGenTime = -1
    
    def addReply(self, path, time, repGenTime):
        self.repliesReceived.append(path)
        self.repliesTimes.append(time)
        self.repGenTime = repGenTime
        
        
    def run(self, node, destination, pid):
        start = self.sim.now()
        candidates = list(self.sim.G.node[node]['reach'][destination])
            
        replyComputation = RCReplyComputation(pid, self, start, len(candidates), sim=self.sim)
       
        for candidate in candidates:
            rcreq = RCRequestPropagation(name='RCRequest pid: %s, %s to %s via %s' % (str(pid), str(node), str(destination), str(candidate)) , sim=self.sim)
            self.sim.encryptionCount += 1
            self.sim.activate(rcreq, rcreq.run(destination, candidate, [node], pid, replyComputation, start))          
        logging.info('pid: %d (%s to %s): generated %d requests.' % (pid, str(node), str(destination), len(candidates)))
        #wait for them to come back
        waitTime = self.sim.config.waitforrepliestime
        while True:
            yield hold, self, waitTime
            if self.interrupted():
                waitTime = self.interruptLeft
                #check if we received all replies
                if len(self.repliesReceived) == len(candidates) and self.sim.config.useShortcut:
                    #then we can stop waiting
                    break
                else:
                    #keep waiting
                    self.interruptReset()
            else:
                #finished waiting, let's get out of this loop
                break
            
        #did the shortest path answer?
        if self.shortestPath in self.repliesReceived:
            #get old distance to destination
            if destination in self.sim.G.node[node]['fwd']:
                oldDistance = self.sim.G.node[node]['fwd'][destination][1]
                if oldDistance == self.spDistance:
                    self.distanceChanged = False

            if self.distanceChanged:
                self.sim.updateFwdTable(self.shortestPath[0], self.shortestPath[-1], self.shortestPath[1], self.spDistance)
            else:
                if not self.sim.G.node[node]['fwd'][destination][0] == self.shortestPath[1]:
                    self.sim.updateFwdTable(self.shortestPath[0], self.shortestPath[-1], self.shortestPath[1], self.spDistance)
                else:
                    #do nothing
                    pass
        else:
            #no, bummer. Do some logging...
            pass
            #print 'Bummer, shortest path is dead'
            #print 'Shortest path: %s. Paths replied: %s' % (str(self.shortestPath),str(self.repliesReceived))
            #print 'Implement correct handling of this situation!!'
        #now write statistics
        if self.sim.config.logComputations:
            time = self.sim.now()-start
            f = open(self.sim.resultsDir+'/computations.dat','a')
            f.write('%d; %d:%d; %f' % (pid, len(candidates), len(self.repliesReceived), time))       
            pts = string.join(['%s:%f' % (path, time) for path, time in zip(self.repliesReceived, self.repliesTimes)] ,', ')
            f.write('%s; reqSent: %d, repSent: %f\n' % (pts, start, self.repGenTime))
            f.close()

class RCReplyComputation(Process):
    
    def __init__(self, pid, rcComputation, rcStart, nofCandidates, name='a_process', sim=None):
        Process.__init__(self, name, sim)
        self.paths = []
        self.times = []
        self.isStarted = False
        self.pid = pid
        self.rcComputation = rcComputation
        self.rcStart = rcStart #timestamp from when the SPComputation started
        self.nofCandidates = nofCandidates
    
    def addPath(self, path, time):
        self.paths.append(path)
        self.times.append(time)
        if not self.isStarted:
            self.sim.activate(self, self.run())
            self.isStarted = True
        #else:
            #self.interrupt(self)
            
    def pathWeight(self, path):
        curNode = path[0]
        weight = 0
        for nextNode in path[1:]:
            weight += self.sim.G.edge[curNode][nextNode]['weight']
            curNode = nextNode
        return weight
    
    def run(self):
        
        wait = (self.rcStart + self.sim.config.waitforrequeststime) - self.sim.now()
        if wait < 0:
            logging.warning('aborting replies computation. Requests came too late.')
            return
        
        while True:
            yield hold, self, wait
            if self.interrupted():
                wait = self.interruptLeft
                #check if we received all replies
                if self.nofCandidates == len(self.paths) and self.sim.config.useShortcut:
                    #print 'took shortcut. saved %d msecs.' % wait
                    #then we can stop waiting
                    break
                else:
                    #keep waiting
                    self.interruptReset()
            else:
                #finished waiting, let's get out of this loop
                break
        
        # now generate the replies for all paths in paths
        if len(self.paths) > 0:
            #first we have to find out which one's the shortest
            minWeight = self.pathWeight(self.paths[0])
            sPath = self.paths[0]
            for path in self.paths[1:]:
                weight = self.pathWeight(path)
                if weight < minWeight:
                    minWeight = weight
                    sPath = path
            logging.info('%s: shortest path for pid: %d is: %s with weight %s' % (self.sim.now(), self.pid, str(sPath), str(minWeight)))
            self.rcComputation.shortestPath = sPath
            self.rcComputation.spDistance = minWeight
            #now create the replies
            repTime = self.sim.now()
            for path, time  in zip(self.paths, self.times):
                repPro = RCReplyPropagation(sim=self.sim)
                self.sim.activate(repPro, repPro.run(path, self.pid, self.rcComputation, time, self.rcStart, repTime))
        else:
            logging.info('This should never happen!!!!')

class RCRequestPropagation(Process):
        
    def run(self, destination, candidate, path, pid, replyComputation, start):
        startTime = self.sim.now()
        #that's for source to candidate
        yield hold, self, self.sim.transmissionDelay()
        
        curNode = candidate
        while not curNode == destination:
            self.sim.compMessageCount += 1
            self.sim.requestsCount += 1
            yield request, self, self.sim.routers[curNode]
            if self.sim.now() > start + self.sim.config.waitforrequeststime:
                #drop request because it is too old.
                logging.info("dropping request %d in node %s. Too old." % (pid, self.name))
                yield release, self, self.sim.routers[curNode]
                return
            yield hold, self, self.sim.config.rcrequesttime
            yield release, self, self.sim.routers[curNode]
            self.sim.encryptionCount += 1
            yield hold, self, self.sim.transmissionDelay()
            if curNode in path:
                logging.info("loop detected in %s" %(self.name))
                return
            path.append(curNode)
            curNode = self.sim.G.node[curNode]['fwd'][destination][0]
        path.append(curNode)
        self.sim.compMessageCount += 1
        self.sim.requestsCount += 1
        time = self.sim.now()-startTime
        replyComputation.addPath(path, time)
        self.interrupt(replyComputation)


            
class RCReplyPropagation(Process):
   
    def run(self, path, pid, rcComputation, time, rcStart, repGenTime):
        start = self.sim.now()
        yield hold, self, self.sim.transmissionDelay()
        for router in reversed(path[1:-1]):
            self.sim.compMessageCount += 1
            self.sim.repliesCount += 1
            yield request, self, self.sim.routers[router]
            if self.sim.now() > rcStart + self.sim.config.waitforrepliestime:
                logging.warning("dropping response %d in node %s. Too old." % (pid, router))
                yield release, self, self.sim.routers[router]
                return             
            yield hold, self, self.sim.config.rcreplytime
            yield release, self, self.sim.routers[router]           
            yield hold, self, self.sim.transmissionDelay()
        self.sim.compMessageCount += 1
        self.sim.repliesCount += 1
        repTime = self.sim.now()-start
        #now do the last one
        rcComputation.addReply(path, time+repTime, repGenTime)
        self.interrupt(rcComputation)
        
        
class WaitForAnnouncementsThenStartRCRequest(Process):
    
    id = 0
    
    def __init__(self, node, destination, name='a_process', sim=None):
        Process.__init__(self, name=name, sim=sim)
        self.node = node
        self.destination = destination
    
    def nextID(self):
        WaitForAnnouncementsThenStartRCRequest.id += 1
        return WaitForAnnouncementsThenStartRCRequest.id
        
    def run(self):
        logging.info('%s: started waiting for %s to %s' % (self.sim.now(), str(self.node), str(self.destination)))
        myWaitTime = 0.5 * self.sim.config.waitforannouncementstime + random.randint(0, self.sim.config.waitforannouncementstime)
        yield hold, self, myWaitTime
        candidates = self.sim.G.node[self.node]['reach'][self.destination]
        pid = self.nextID()
        logging.info('%s: finished waiting for %s to %s. Candidates: %s. Pid: %d' % (self.sim.now(), str(self.node), str(self.destination), str(candidates), pid))
        self.sim.G.node[self.node]['waitForRC'][self.destination] = False
        
        rccomp = RCComputation(sim=self.sim)
        self.sim.activate(rccomp, rccomp.run(self.node, self.destination, pid))
        self.sim.spComputations += 1

    


## Model -------------------------------
class STRIP_simulator(Simulation):
    
    def _initializeNodeAttributes(self):
        for node in self.G.nodes_iter():
            self.G.node[node]['reach'] = {}
            self.G.node[node]['fwd'] = {}
            self.G.node[node]['waitForRC']={}
            for onode in self.G.nodes_iter():
                self.G.node[node]['waitForRC'][onode] = False
    
    def addNeighboursToFwdAndReachabilityTable(self):
        #first add all neighbours to the reachability dict
        for node in self.G.nodes_iter():
            for neighbour in self.G.neighbors_iter(node):
                self.G.node[node]['reach'][neighbour] = [neighbour]
        #and then put add these entries to the fwd table and inform neighbours about new destinations
        for node in self.G.nodes_iter():
            for neighbour in self.G.neighbors_iter(node):
                self.updateFwdTable(node, neighbour, neighbour, self.G.edge[node][neighbour]['weight'])
        pass
    
    def updateFwdTable(self, node, destination, nextHop, distance):
        self.G.node[node]['fwd'].update({destination:(nextHop, distance)})      
        logging.info('%s: updated fwd table at node %s: {%s : (%s,%d)}' % (self.now(), str(node), str(destination), str(nextHop),distance))
        self.sendDestinationToNeighbours(node, destination)
    
    def transmissionDelay(self):
        return 5 + random.expovariate(1.0)
    
    def sendDestinationToNeighbours(self, source, destination):
        nextHop = self.G.node[source]['fwd'][destination]
        for neighbour in self.G.neighbors_iter(source):
            if not neighbour == nextHop:
                self.addDestinationToNode(neighbour, destination, source)
    
    def addDestinationToNode(self, node, destination, nextHop):
        
        if destination == node:
            return
        self.announcementCount += 1
        #first update the reachability information
        if destination in self.G.node[node]['reach']:
            if not nextHop in self.G.node[node]['reach'][destination]:
                self.G.node[node]['reach'][destination].append(nextHop)
        else:
            self.G.node[node]['reach'][destination] = [nextHop]
        #check if the waitAndThenStartRCRequest process is already running
        if self.G.node[node]['waitForRC'][destination]:
            #then there is nothing else to do
            pass
        else:
            #start the waiting process
            req = WaitForAnnouncementsThenStartRCRequest(node, destination, name='%s:%s' % (str(node), str(destination)), sim=self)
            self.G.node[node]['waitForRC'][destination] = True
            self.activate(req, req.run())
        
    def _loadNetwork(self, filename):
        self.G = nx.read_gml(filename)
        self._initializeNodeAttributes()
       
    def setUpSim(self, config):
        self.config = config
        self.resultsDir = config.resultsDir + '/' + config.name
        try:
            os.mkdir(self.resultsDir)
        except Exception:
            pass
        #save config
        cPickle.dump(config, open(self.resultsDir+'/config.pickle','w'), protocol=0)
        #set seed of random number generator
        random.seed(config.random_seed)
        self.announcementCount = 0
        self.compMessageCount = 0
        self.requestsCount = 0
        self.repliesCount = 0
        self.spComputations = 0
        self.encryptionCount = 0
    
    def run(self, config):
        self.setUpSim(config)
        self.initialize()
        if isinstance(self, SimPy.SimulationTrace.SimulationTrace):
            self.trace.tchange(outfile=open('STRIPtrace.txt','w'))
        self._loadNetwork(config.graphFile)
        Utils.printGraphStatistics(config.graphFile, self.resultsDir + '/graphStatistics.txt')
        self.routersAnn = [Resource(name=n, sim=self) for n in self.G.nodes_iter()]
        if not self.config.useMultiCore:
            self.routers = [Resource(name=n, sim=self, monitored=True) for n in self.G.nodes_iter()]
        else:
            self.routers = []
            for node in self.G.nodes_iter():
                deg = len(self.G.neighbors(node))
                cores = int(math.ceil(deg/4.0))
                self.routers.append(Resource(capacity=cores, name=node, sim=self, monitored=True))
        
        self.addNeighboursToFwdAndReachabilityTable()

        self.simulate(until=1000000)
        print 'elapsed time: %s' % (self.now())

        error, pnf = self.compareGraphToOptimum()
        rf = open(self.resultsDir+'/STRIP_results.txt', 'w')
        rf.write('elapsed time: %s\n' % (self.now()))
        rf.write('announcements sent: %d\n' % (self.announcementCount))
        rf.write('spcomputationmessages sent: %d\n' % (self.compMessageCount))
        rf.write('shortest-path computations: %d\n' % (self.spComputations))
        rf.write('error of found pahts (in %%): %s\n' %(str(error*100)))
        rf.write('paths not found: %d\n' % (pnf))
        rf.write('number of encryptions: %d\n' % self.encryptionCount)
        rf.write('sprequestmessages sent: %d\n' % (self.requestsCount))
        rf.write('spreplymessages sent: %d\n' % (self.repliesCount))
        rf.close()
        rf = open(self.resultsDir+'/router.dat', 'w')
        rf.write('name, time average, max queue\n')
        for router in self.routers:
            rf.write('%s, %f, %d\n' % (router.name, router.waitMon.timeAverage(), max(router.waitMon.yseries())))
        rf.close()
        
        
#        rf = open(self.resultsDir+'/routerhist.dat', 'w')
#        for router in self.routers:
#            rf.write('%s\n' % (string.join(map(str,router.waitMon.tseries()),';')))
#            rf.write('%s\n' % (string.join(map(str,router.waitMon.yseries()),';')))
#        rf.close()
 
    def verifyResult(self):
        sps = nx.all_pairs_dijkstra_path(self.G)
        allGood = True
        errorMsg = ''
        try:
            for source, vals in sps.iteritems():
                for destination, path in vals.iteritems():
                    #print "s: %s, d: %s, path: %s" % (str(source), str(destination), str(path))
                    if not source == path[0]:
                        allGood = False
                        print "this shouldn't happen..."
                    curNode = source
                    for pNode in path[1:]:
                        curNode = self.G.node[curNode]['fwd'][destination]
                        if not pNode == curNode:
                            allGood = False
                            errorMsg += 'In path %s to %s: %s. Expected: %s, found %s \n' % (str(source), str(destination), str(path), str(pNode), str(curNode))
        except KeyError:
            allGood = False
            print 'error!'
        if allGood:
            print 'We found the APSP solution.'
        else:
            print 'Not the APSP solution' + errorMsg
    
    
    def pathLenght(self, source, destination):
        ret = 0
        lastNode = source
        curNode = self.G.node[source]['fwd'][destination][0]
        while True:
            ret += self.G.edge[lastNode][curNode]['weight']
            if curNode == destination:
                break
            else:
                lastNode = curNode
                curNode = self.G.node[curNode]['fwd'][destination][0]
        return ret
      
    def compareGraphToOptimum(self):
        shortestPathsWeights = nx.all_pairs_dijkstra_path_length(self.G)
        optimalSum = 0
        graphSum = 0
        mypath = 0
        pathsNotFound = 0
        for source, val in shortestPathsWeights.iteritems():
            for destination, pathLenght in val.iteritems():
                if source == destination:
                    continue
                try:
                    mypath = self.pathLenght(source, destination)
                    graphSum += mypath
                    optimalSum += pathLenght
                    if not mypath == pathLenght:
                        print 'different path from %s to %s with %d to %d' % (str(source), str(destination), mypath, pathLenght)
                except KeyError:
                    print 'incomplete solultion! No path from %s to %s' % (str(source), str(destination))
                    pathsNotFound += 1
                    optimalSum += pathLenght
                    graphSum += 2*pathLenght
                    #return '','incomplete'
        error = (float(graphSum)-float(optimalSum))/float(optimalSum)
        print "Error of found paths: %f%%, Paths not found: %d" %(100*error,pathsNotFound)
        #print 'optimal shortest-paths sum: %s, graph shortest-path sum: %s.' % (str(optimalSum), str(graphSum))
        return error, pathsNotFound



## Start Simulation --------------------
#simu = STRIP_simulator()
#simu.run('erdos_renyi_20_30.gml')
#simu.verifyResult()
#simu.compareGraphToOptimum()
#print nx.all_pairs_dijkstra_path(simu.G)
#for r in simu.routers:
#    print 'wait: %f, act: %f' % (r.waitMon.timeAverage(), r.actMon.timeAverage())
    #print r.waitMon.histogram(low=0.0, high=10.0, nbins=10)
    #r.actMon.printHistogram()

def startSIM(config):
    simu = STRIP_simulator()
    simu.run(config)
    
