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
#from SimPy.SimulationTrace import *
from SimPy.Simulation import *
import networkx as nx
import logging
import os
import cPickle
import math

logging.basicConfig(filename='pathVector.log', level=logging.ERROR)


class ReceiveAnnouncement(Process):
    
    counter = 0
    
    def run(self, node, destination, nexthop, distance, path ):
        yield hold, self, 5 + random.expovariate(1.0)
        ReceiveAnnouncement.counter += 1
        yield request, self, self.sim.routers[node]
        yield hold, self, self.sim.config.rcreplytime
        yield release, self, self.sim.routers[node]
        #check for loop
        if node in path:
            logging.info('found loop. Discard %s to %s via %s. Path: %s' % (str(node),str(destination), str(nexthop), str(path)))
            return
        #compare to current route
        newDist = distance + self.sim.G.edge[node][nexthop]['weight']
        #path.insert(0, node)

        self.sim.updateFwdTable(node, destination, newDist, nexthop, path)
        
        
class AnnouncementDelay(Process):
    
    def __init__(self, node, destination, name='a_process', sim=None):
        Process.__init__(self, name, sim)
        self.node = node
        self.destination = destination
    
    def run(self):
        
        myWaitTime = 0.5 * self.sim.config.waitforannouncementstime + random.randint(0, self.sim.config.waitforannouncementstime)
        yield hold, self, myWaitTime
        
        #yield hold, self, self.sim.config.waitforannouncementstime
        
        del self.sim.announcementDelays[(self.node, self.destination)]
        info = self.sim.G.node[self.node]['fwd'][self.destination]
        distance = info[0]
        nextHop = info[1]
        path = info[2]
        for neighbour in self.sim.G.neighbors_iter(self.node):
            if neighbour == nextHop:
                continue
            ann = ReceiveAnnouncement(sim=self.sim)
            self.sim.activate(ann, ann.run(neighbour, self.destination, self.node, distance, list(path)))
                    
# Model ------------------------------------
#class PathVectorSimulator(SimulationTrace):
class PathVectorSimulator(Simulation):
    
    def initialize(self):
        Simulation.initialize(self)
        self.announcementDelays = {}
        ReceiveAnnouncement.counter = 0
        
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
    
    def _loadNetwork(self, filename):
        self.G = nx.read_gml(filename)
        self._initializeNodeAttributes()
        
    def _initializeNodeAttributes(self):
        for node in self.G.nodes_iter():
            self.G.node[node]['fwd'] = {}
       
    def initialAnnouncementsToNeighbours(self):
        for node in self.G.nodes_iter():
            for neighbour in self.G.neighbors_iter(node):
                distance = self.G.edge[node][neighbour]['weight']
                
                fwdTable = self.G.node[node]['fwd']
                if neighbour in fwdTable:
                    oldDistance = fwdTable[neighbour][0]
                    if oldDistance < distance:
                        #nothing to do then...
                        continue
                fwdTable[neighbour] = (distance, neighbour, [node, neighbour])
                self.updateNeighboursFwdTables(node, neighbour, distance)
                
                #self.updateFwdTable(node, neighbour, distance, neighbour, [neighbour])
        for node in self.G.nodes_iter():
            fwdTable = self.G.node[node]['fwd']
            for destination in fwdTable:
                ad = AnnouncementDelay(node, destination, sim=self, name='AnnDelay_%s:%s' %(str(node),str(destination)))
                self.announcementDelays[(node, destination)] = ad
                self.activate(ad, ad.run())
                logging.info('started new announcementDelay for %s:%s at %s' %(str(node),str(destination),self.now()))

                             
    def updateNeighboursFwdTables(self, source, destination, distance):
        for neighbour in self.G.neighbors_iter(source):
            if not neighbour == destination:
                ReceiveAnnouncement.counter += 1
                fwdTable = self.G.node[neighbour]['fwd']
                if destination in fwdTable:
                    oldDistance = fwdTable[destination][0]
                    if oldDistance < distance:
                        #nothing to do then...
                        continue
                fwdTable[destination] = (distance, source, [neighbour, source, destination])
                             
    def updateFwdTable(self, node, destination, distance, nextHop, path):
        ''' updates the fwd table entry 'destination' of node 'node'
            new entry will be: fwdTable[destination] = (distance, nextHop, path)
        ''' 
        fwdTable = self.G.node[node]['fwd']
        if destination in fwdTable:
            oldDistance = fwdTable[destination][0]
            if oldDistance < distance:
                #nothing to do then...
                return
        path.insert(0, node)
        fwdTable[destination] = (distance, nextHop, path)
        # now let all the neighbours know
        self.notifyNeighbours(node, destination)

        
    def notifyNeighbours(self, node, destination):
        ''' notifies all the neighbours of a node about a new destination entry
            but only after an announcement delay
        '''
        if not (node, destination) in self.announcementDelays:
            #create one
            ad = AnnouncementDelay(node, destination, sim=self, name='AnnDelay_%s:%s' %(str(node),str(destination)))
            self.announcementDelays[(node, destination)] = ad
            self.activate(ad, ad.run())
            logging.info('started new announcementDelay for %s:%s at %s' %(str(node),str(destination),self.now()))
        else:
            # nothing to do. Once the delay is over all the neighbours get informed
            logging.info('announcementDelay already started for %s:%s at %s' %(str(node),str(destination),self.now()))
            pass
           
            
        
    def run(self, config):
        self.initialize()
        self.setUpSim(config)
        if isinstance(self, SimPy.SimulationTrace.SimulationTrace):
            self.trace.tchange(outfile=open('PVPtrace.txt','w'))
        self._loadNetwork(config.graphFile)
        if not self.config.useMultiCore:
            self.routers = [Resource(name=n, sim=self, monitored=True) for n in self.G.nodes_iter()]
        else:
            self.routers = []
            for node in self.G.nodes_iter():
                deg = len(self.G.neighbors(node))
                cores = int(math.ceil(deg/4.0))
                self.routers.append(Resource(capacity=cores, name=node, sim=self, monitored=True))
        self.initialAnnouncementsToNeighbours()

        self.simulate(until=1000000)
        self.results = {}
        self.results['elapsed time'] = self.now()
        self.results['announcements sent'] = ReceiveAnnouncement.counter
        
        print 'elapsed time: %s' % (self.now())
        print 'Announcements sent: %d' % (ReceiveAnnouncement.counter)
        #print 'final graph: %s' % (self.G.nodes(data=True))
        
        rf = open(self.resultsDir+'/PaVec_results.txt', 'w')
        rf.write('elapsed time: %s\n' % (self.now()))
        rf.write('announcements sent: %d\n' % (ReceiveAnnouncement.counter))
        rf.close()

    def compareGraphToOptimum(self):
        shortestPathsWeights = nx.all_pairs_dijkstra_path_length(self.G)
        optimalSum = 0
        graphSum = 0
        mypath = 0
        for source, val in shortestPathsWeights.iteritems():
            for destination, pathLenght in val.iteritems():
                if source == destination:
                    continue
                optimalSum += pathLenght
                mypath = self.G.node[source]['fwd'][destination][0]
                graphSum += mypath
                if not mypath == pathLenght:
                    print 'different path from %s to %s with %d to %d' % (str(source), str(destination), mypath, pathLenght)
        print 'optimal shortest-paths sum: %s, graph shortest-path sum: %s.' % (str(optimalSum), str(graphSum))
        self.results['optimal SP sum'] = optimalSum
        self.results['protocol SP sum'] = graphSum



def startSIM(config):
    simu = PathVectorSimulator()
    simu.run(config)
    
#resultsFile = open('pathVectorDelays_barabasi_50.txt','w')
#resultsFile.write('delay, elapsed time, announcements sent\n')
#for delay in range(250):
#    announcementDelayTime = delay
#    simu = PathVectorSimulator()
#    simu.run(graphFile)
#    simu.compareGraphToOptimum()
#    resultsFile.write('%s, %s, %s\n' %(delay, simu.results['elapsed time'], simu.results['announcements sent']))
#resultsFile.close()
#print nx.all_pairs_dijkstra_path(simu.G)