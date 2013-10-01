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
runs the implementation of the STRIP protocol. Have a look in the 
'labs' folder for examples of how to configure the protocol.
You can start the protocol in two ways: either as a program or as a twistd daemon.
'''

if __name__ == '__main__':
    import os
    import sys
    print os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.append(os.getcwd())

from emu.router import STRIPRouter
import logging
from emu.STRIP import STRIPServerFactory
from emu.STRIP import STRIPClientFactory
from twisted.internet import reactor
from twisted.application import internet, service
import ConfigParser



if __name__ == '__main__':
    #we run it as a program
    #read config
    config = ConfigParser.RawConfigParser()
    config.read(sys.argv[1])
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(config.get('logging','logfile'), 'w')
    lformat = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    fh.setFormatter(lformat)
    logger.addHandler(fh)
    
    
    neighbourAddrs = config.get('neighbours','hosts').split(',')
    neighbourNames = config.get('neighbours','targets').split(',')
    neighbours = zip(neighbourAddrs, neighbourNames)
    router = STRIPRouter(config)
    reactor.addSystemEventTrigger("after", "startup", router.startup)
    reactor.addSystemEventTrigger("before", "shutdown", router.shutdown)
    
    #try to connect to all neighbours
    #for neighbour in config.neighbours:
    for neighbour in neighbours:
        host, port = neighbour[0].split(':')
        reactor.connectTCP(host, int(port), STRIPClientFactory(router,neighbour[1]))
    
    #start server thread
    factory = STRIPServerFactory(router)
    port = reactor.listenTCP(config.getint('server','port'), factory)
    logger.info('started listening at: %s:%d' % (port.getHost(),1234))
    reactor.run()
    
    print 'done'
else:
    #we want to run it as a deamon with twistd
    #read config
    config = ConfigParser.RawConfigParser()
    config.read('/STRIP/strip.cfg')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(config.get('logging','logfile'), 'w')
    lformat = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    fh.setFormatter(lformat)
    logger.addHandler(fh)
    
    application = service.Application('STRIP')
    
    neighbourAddrs = config.get('neighbours','hosts').split(',')
    neighbourNames = config.get('neighbours','targets').split(',')
    neighbours = zip(neighbourAddrs, neighbourNames)
    router = STRIPRouter(config)
    reactor.addSystemEventTrigger("after", "startup", router.startup)
    reactor.addSystemEventTrigger("before", "shutdown", router.shutdown)
    
    #try to connect to all neighbours
    #for neighbour in config.neighbours:
    for neighbour in neighbours:
        host, port = neighbour[0].split(':')
        #reactor.connectTCP(host, int(port), STRIPClientFactory(router,neighbour[1]))
        cs = internet.TCPClient(host, int(port), STRIPClientFactory(router,neighbour[1]))
        cs.setServiceParent(application)
    
    #start server thread
    factory = STRIPServerFactory(router)
    #port = reactor.listenTCP(config.getint('server','port'), factory)
    stripservice = internet.TCPServer(config.getint('server','port'), factory)
    stripservice.setServiceParent(application)
    logger.info('started listening at port: %d' % (config.getint('server','port')))
    