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

import STRIP_Sim
import os
import PathVector_Sim

class Config():
    def __init__(self):
        self.rcrequesttime = 4       #time a router needs to process RCRequest
        self.rcreplytime = 0.1       #time a router needs to process RCReply
        self.waitforrequeststime = 10000 #time the destination router waits before creating the replies
        self.waitforannouncementstime = 30000 #time a router waits after receiving a destination announcement and creating a RCRequest
        self.waitforrepliestime = 20000  #time the source router waits before 
        self.graphFile = 'erdos_renyi_20_20.gml'
        self.resultsDir = 'results'
        self.name = 'firstTesty'
        self.random_seed = 42
        self.logComputations = False
        self.useShortcut = True
        self.useMultiCore = False

def repeatedDelaySeries(config, delayMin, delayMax, delayDelta, repetitions):
    for time in xrange(delayMin, delayMax+1, delayDelta):
        try:
            os.makedirs('results/' + config.graphFile + '/%d' % time)
        except Exception as e:
            print 'Oh no! %s' % str(e)
        config.resultsDir = 'results/' + config.graphFile + '/%d' % time
        for rep in xrange(repetitions):
            print 'delay: %d, repetition: %d' % (time, rep)
            config.waitforannouncementstime = time
            config.random_seed = rep
            config.name = str(rep)
            STRIP_Sim.startSIM(config)
            PathVector_Sim.startSIM(config)

def runTestSeries(config):
    testNets = ('abilene.gml', 'tree_11_4.gml', 'fullyconnected_11.gml')
    repetitions = 20
    for net in testNets:
        config.graphFile = 'graphs/testNets/%s' % net
        try:
            os.makedirs('results/testNets/%s' % net)
        except Exception as e:
            print 'Oh no! %s' % str(e)
        config.resultsDir = 'results/testNets/%s' % net
        for rep in range(repetitions):
            config.random_seed = rep
            config.name = str(rep)
            
            STRIP_Sim.startSIM(config)
        #PathVector_Sim.startSIM(config)

def runBarabasiSeries(config):
    sizes = [10, 20, 50]
    ann = {10:500, 20:2000, 50: 5000, 100:15000}
    repetitions = 50
    for size in sizes:
        filename = 'barabasi_%d_2.gml' % size
        config.graphFile = 'graphs/barabasi/%s' % filename
        config.waitforrequeststime = size * 10
        config.waitforrepliestime = 2 * config.waitforrequeststime
        config.waitforannouncementstime = ann[size]
        config.resultsDir = 'results/barabasiSeries/%s/%d_%d_%d_mc/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
        try:
            os.makedirs(config.resultsDir)
        except Exception as e:
            #print 'Oh no! %s' % str(e)
            pass
        for rep in range(repetitions):
            config.random_seed = rep
            config.name = str(rep)
            STRIP_Sim.startSIM(config)
            PathVector_Sim.startSIM(config)

def runBarabasi(config):
    
    config.graphFile = 'barabasi_20_2.gml'
    config.waitforrequeststime = 200
    config.waitforrepliestime = 2 * config.waitforrequeststime
    for awt in xrange(1500, 15000, 1500):
        config.waitforannouncementstime = awt
        config.name = '%d_%d_%d_mc' %  (config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
        try:
            os.makedirs('results/' + config.graphFile)
        except Exception as e:
            print 'Oh no! %s' % str(e)
        config.resultsDir = 'results/' + config.graphFile
        STRIP_Sim.startSIM(config)
        PathVector_Sim.startSIM(config)

def runWaitForRequestSeries(config):
    filename = 'erdos_renyi_30_15.gml'
    config.graphFile = 'graphs/erdos_renyi/%s' % filename
    config.waitforannouncementstime = 4000
    repetitions = 50
    config.useShortcut = True
    
    for time in range(50,501, 50):
        config.waitforrequeststime = time
        config.waitforrepliestime = 2 * config.waitforrequeststime
        config.resultsDir = 'results/waitForRequestsSeries/%s/%d_%d_%d/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
        try:
            os.makedirs(config.resultsDir)
        except Exception as e:
            #print 'Oh no! %s' % str(e)
            pass
        for rep in range(10,repetitions):
            config.random_seed = rep
            config.name = str(rep)
            STRIP_Sim.startSIM(config)
            #PathVector_Sim.startSIM(config)

def runWaitForAnnouncementsSeries(config, multiCore=False):
    filename = 'erdos_renyi_30_15.gml'
    config.graphFile = 'graphs/erdos_renyi/%s' % filename
    config.waitforrequeststime = 300
    config.waitforrepliestime = 2 * config.waitforrequeststime
    config.useShortcut = True
    config.useMultiCore = multiCore
    
    repetitions = 50
    for time in range(1000,4001, 500):
        config.waitforannouncementstime = time
        if multiCore:
            config.resultsDir = 'results/waitForAnnouncementsSeries/%s_multicore/%d_%d_%d/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
        else:
            config.resultsDir = 'results/waitForAnnouncementsSeries/%s/%d_%d_%d/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
        
        try:
            os.makedirs(config.resultsDir)
        except Exception as e:
            #print 'Oh no! %s' % str(e)
            pass
        for rep in range(5, repetitions):
            config.random_seed = rep
            config.name = str(rep)
            STRIP_Sim.startSIM(config)
            #PathVector_Sim.startSIM(config)


def comparisonOverWaitForAnnouncementTime(config):
    config.graphFile = 'erdos_renyi_30_15.gml'
    config.waitforrequeststime = 300
    config.waitforrepliestime = 2 * config.waitforrequeststime
    repetitions = 50
    for time in range(1500,5501, 500):
        config.waitforannouncementstime = time
        config.resultsDir = 'results/comparison/waitForAnnouncementsSeries/%s/%d_%d_%d/' %  (config.graphFile, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
        try:
            os.makedirs(config.resultsDir)
        except Exception as e:
            #print 'Oh no! %s' % str(e)
            pass
        for rep in range(repetitions):
            config.random_seed = rep
            config.name = str(rep)
            STRIP_Sim.startSIM(config)
            PathVector_Sim.startSIM(config)

def comparisonOverNumberOfNodes(config):
    repetitions = 5
    config.useMultiCore = False
    config.useShortcut = True
    
    
    for n in range(5, 51, 5):
        config.waitforrequeststime = n*10
        config.waitforrepliestime = 2 * config.waitforrequeststime
        for i in range(0,10):
            filename = 'erdos_renyi_%d_10_%d.gml' % (n, i)
            config.graphFile = 'graphs/comparison/NumberOfNodesSeries/%s' % filename
            config.waitforannouncementstime = 15000
            config.resultsDir = 'results/comparison/NumberOfNodesSeries/%s/%d_%d_%d/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
            try:
                os.makedirs(config.resultsDir)
            except Exception as e:
                pass
            for rep in range(repetitions):
                config.random_seed = rep
                config.name = str(rep)
                STRIP_Sim.startSIM(config)
                #PathVector_Sim.startSIM(config)
    for n in range(5, 51, 5):
        config.waitforrequeststime = n*10
        config.waitforrepliestime = 2 * config.waitforrequeststime
        for i in range(0,10):
            filename = 'barabasi_%d_2_%d.gml' % (n, i)
            config.graphFile = 'graphs/comparison/NumberOfNodesSeries/%s' % filename
            config.waitforannouncementstime = 15000
            config.resultsDir = 'results/comparison/NumberOfNodesSeries/%s/%d_%d_%d/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
            try:
                os.makedirs(config.resultsDir)
            except Exception as e:
                pass
            for rep in range(repetitions):
                config.random_seed = rep
                config.name = str(rep)
                STRIP_Sim.startSIM(config)
                #PathVector_Sim.startSIM(config)
        
def maxNodeDegreeDependencySeries(config):
    config.waitforrequeststime = 300
    config.waitforrepliestime = 2 * config.waitforrequeststime
    
    repetitions = 2
    
    for mnd in range(4,13,2):
        for wfat in range(1000,5001,500):
            config.waitforannouncementstime =wfat
            for i in range(5):
                filename = 'maxNodeDegree_%d_%d.gml' % (mnd,i)
                config.graphFile = 'graphs/maxNodeDegree/%s' % filename
                config.resultsDir = 'results/maxDegree/%s/%d_%d_%d/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
        
                try:
                    os.makedirs(config.resultsDir)
                except Exception as e:
                    #print 'Oh no! %s' % str(e)
                    pass
                for rep in range(repetitions):
                    config.random_seed = rep
                    config.name = str(rep)
                    STRIP_Sim.startSIM(config)
    
def densitySeries(config):
    'encryptions and messages over the density'
    n = 30
    config.waitforrequeststime = n*10
    config.waitforrepliestime = 2 * config.waitforrequeststime
    config.waitforannouncementstime = 4000
    repetitions = 10
    
    for degree in range(20,61,5):
        for i in range(5):
            filename = 'FixedNodeDegree_%d_%d_%d.gml' % (n, degree, i)
            config.graphFile = 'graphs/densitySeries/%s' % filename
            config.resultsDir = 'results/densitySeries/%s/%d_%d_%d/' %  (filename, config.waitforannouncementstime, config.waitforrequeststime, config.waitforrepliestime)
            try:
                os.makedirs(config.resultsDir)
            except Exception as e:
                #print 'Oh no! %s' % str(e)
                pass
            for rep in range(repetitions):
                config.random_seed = rep
                config.name = str(rep)
                STRIP_Sim.startSIM(config)
                #PathVector_Sim.startSIM(config)


if __name__ == '__main__':
    config = Config()
    #repeatedDelaySeries(config, 500, 2000, 100, 10)
    runBarabasiSeries(config)
    #densitySeries(config)
    #comparisonOverNumberOfNodes(config)
    #runWaitForRequestSeries(config)
    #runWaitForAnnouncementsSeries(config, multiCore=True)
    #runWaitForAnnouncementsSeries(config)
    #runTestSeries(config)
    #maxNodeDegreeDependencySeries(config)
    
    