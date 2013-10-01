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

''' Implementation of the distance vector protocl '''

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver
import logging
import cPickle as pickle
from emu.messages import DVAnnouncement, SPCRequest, SPCResponse


logger = logging.getLogger('logger')


class DVClient(NetstringReceiver):
    
    def __init__(self, router, partner):
        self.router = router
        self.partner = partner
    
    def connectionMade(self):
        logger.info('connection made to %s.' % self.partner)
        self.router.addConnection(self.partner, self)
        
        
    
    def stringReceived(self, data):
        try:
            message = pickle.loads(data)
            if isinstance(message, DVAnnouncement):
                self.processDVAnnouncement(message)
            elif isinstance(message, SPCRequest):
                self.processSPCRequest(message)
            elif isinstance(message, SPCResponse):
                self.processSPCResponse(message)
            else:
                logger.error('received unknown message: %s' % message)
        except Exception, err:
            logger.error('Error receiving message: %s' % err)


    def connectionLost(self, reason):
        NetstringReceiver.connectionLost(self, reason=reason)
        logger.info('connection lost to %s: %s' % (self.partner, str(reason)))
        self.router.removeConnection(self.partner)
        
    def processDVAnnouncement(self, ann):
        self.router.processDVAnnouncement(ann)
    
    def sendMessage(self, message):
        self.sendString(pickle.dumps(message))
    

class DVClientFactory(ReconnectingClientFactory):
    factor = 2
    
    def __init__(self, router, partner):
        self.router = router
        self.partner = partner
    
    def startedConnecting(self, connector):
        logger.debug('try to connect to %s' % self.partner)

    def buildProtocol(self, addr):
        #print 'Connected to %s.' % str(addr)
        self.resetDelay()
        return DVClient(self.router, self.partner)

    def clientConnectionLost(self, connector, reason):
        #logger.info('client connection lost: %s' % reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        #print 'connection failed'
        logger.debug('client connection to %s:%d failed: %s' % (connector.host, connector.port, str(reason)))
        ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                         reason)
class DVServer(NetstringReceiver):
    
    def __init__(self, router):
        self.router = router
    
    def connectionMade(self):
        logger.info('client %s:%d connected.' % self.transport.client)
        self.router.sendFib(self.sendMessage)
        pass
    
    def stringReceived(self, data):
        try:
            message = pickle.loads(data)
            if isinstance(message, DVAnnouncement):
                self.processDVAnnouncement(message)
            elif isinstance(message, SPCRequest):
                self.processSPCRequest(message)
            elif isinstance(message, SPCResponse):
                self.processSPCResponse(message)
            else:
                logger.error('received unknown message: %s' % message)
        except Exception, err:
            logger.error('Error receiving message: %s' % err)
            
        pass

    def connectionLost(self, reason):
        NetstringReceiver.connectionLost(self, reason=reason)
        logger.info('connection to client %s lost: %s' % (self.transport.hostname, str(reason)))
    
    def processDVAnnouncement(self, message):
        self.router.processDVAnnouncement(message)
    
    def sendMessage(self, message):
        self.sendString(pickle.dumps(message))
        
class DVServerFactory(ServerFactory):
    def __init__(self, router):
        self.router = router
        
    def buildProtocol(self, addr):
        p = DVServer(self.router)
        p.factory = self
        return p
    