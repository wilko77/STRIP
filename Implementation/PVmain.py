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


'''
runs the implementation of the distance vector protocol. Have a look in the 
'labs' folder for examples of how to configure the protocol.
You can start the protocol in two ways: either as a program or as a twistd daemon.
'''
import sys
#if __name__ == '__main__':
    #import os
    #import sys
    #os.chdir(os.path.dirname(sys.argv[0]))
    #sys.path.append(os.getcwd())

from emu.router import DVRouter
import logging
from emu.DistanceVector import DVServerFactory
from emu.DistanceVector import DVClientFactory
from twisted.application import internet, service
from twisted.internet import reactor
import ConfigParser



if __name__ == '__main__': #we are running it as a program
    #parse config file
    config = ConfigParser.RawConfigParser()
    config.read(sys.argv[1])
    #set logger
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(config.get('logging','logfile'), 'w')
    format = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    fh.setFormatter(format)
    logger.addHandler(fh)
    
    #read config
    neighbourAddrs = config.get('neighbours','hosts').split(',')
    neighbourNames = config.get('neighbours','targets').split(',')
    neighbours = zip(neighbourAddrs, neighbourNames)
    router = DVRouter(config)
    #try to connect to all neighbours
    for neighbour in neighbours:
        host, port = neighbour[0].split(':')
        reactor.connectTCP(host, int(port), DVClientFactory(router,neighbour[1]))
    
    #start server thread
    factory = DVServerFactory(router)
    port = reactor.listenTCP(config.getint('server','port'), factory)
    logger.info('started listening at: %s:%d' % (port.getHost(),1234))
    reactor.run()
    
    print 'done'
else: #we are running it as a daemon with twistd
    #read config
    config = ConfigParser.RawConfigParser()
    #config.read(sys.argv[1])
    config.read('/STRIP/strip.cfg')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(config.get('logging','logfile'), 'w')
    format = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    fh.setFormatter(format)
    logger.addHandler(fh)
    
    neighbourAddrs = config.get('neighbours','hosts').split(',')
    neighbourNames = config.get('neighbours','targets').split(',')
    neighbours = zip(neighbourAddrs, neighbourNames)
    router = DVRouter(config)
    
    application = service.Application('STRIP')
    
    #try to connect to all neighbours
    #for neighbour in config.neighbours:
    for neighbour in neighbours:
        host, port = neighbour[0].split(':')
        cs = internet.TCPClient(host, int(port), DVClientFactory(router,neighbour[1]))
        #reactor.connectTCP(host, int(port), DVClientFactory(router,neighbour[1]))
        cs.setServiceParent(application)
    
    #start server thread
    factory = DVServerFactory(router)
    #port = reactor.listenTCP(config.getint('server','port'), factory)
    stripservice = internet.TCPServer(config.getint('server','port'), factory)
    stripservice.setServiceParent(application)
    logger.info('started listening at port: %d' % (config.getint('server','port')))
   