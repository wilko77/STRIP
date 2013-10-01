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

#from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import NetstringReceiver
import logging
import cPickle as pickle
from emu.messages import Announcement, SPCRequest, SPCResponse

logger = logging.getLogger('logger')

class STRIPClient(NetstringReceiver):
    
    MAX_LENGTH = 9999999
    
    def __init__(self, router, partner):
        self.router = router
        self.partner = partner
    
    def connectionMade(self):
        logger.debug('connection made to %s.' % self.partner)
        self.sendString(self.router.identity)
        self.router.addConnection(self.partner, self)
    
    def stringReceived(self, data):
        try:
            message = pickle.loads(data)
            if isinstance(message, Announcement):
                self.processAnnouncement(message)
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
        #self.router.removeConnection(self.partner)
        
    def processAnnouncement(self, ann):
        logger.debug('announcement received from %s: %s' % (self.partner, ann))
        self.router.processAnnouncement(ann)
        
    def processSPCRequest(self, req):
        self.router.processSPCRequest(req)
    
    def processSPCResponse(self, res):
        self.router.processSPCResponse(res)
    
    def sendMessage(self, message):
        logger.debug('sending message: %s' % message)
        if isinstance(message, Announcement):
            self.router.measurement.addAnnouncement()
        else:
            self.router.measurement.addOtherMessage()
        try:
            s = pickle.dumps(message)
            self.sendString(s)
        except Exception, err:
            logger.error('error sending message: %s' % err)
        
    
class STRIPServer(NetstringReceiver):
    
    MAX_LENGTH = 9999999
    
    def __init__(self, router):
        self.router = router
        self.firstMessage = True
        self.partner = None
        
    def connectionMade(self):
        logger.debug('connection made.')
        pass
    
    def stringReceived(self, data):
        if self.firstMessage:
            self.partner = data
            self.router.connections[self.partner] = self
            self.firstMessage = False
        else:
            try:
                message = pickle.loads(data)
                logger.debug('received message: %s' % message)
                if isinstance(message, Announcement):
                    self.processAnnouncement(message)
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
        logger.info('connection lost: %s' % str(reason))
    
    def processAnnouncement(self, ann):
        logger.debug('announcement received from %s: %s' % (self.partner, ann))
        self.router.processAnnouncement(ann)
    
    def processSPCRequest(self, message):
        self.router.processSPCRequest(message)
    
    def processSPCResponse(self, message):
        self.router.processSPCResponse(message)
    
    def sendMessage(self, message):
        logger.debug('sending message: %s' % message)
        if isinstance(message, Announcement):
            self.router.measurement.addAnnouncement()
        else:
            self.router.measurement.addOtherMessage()
        try:
            s = pickle.dumps(message)
            self.sendString(s)
        except Exception, err:
            logger.error('error sending message: %s' % err)
        
class STRIPServerFactory(ServerFactory):
    def __init__(self, router):
        self.router = router
        
    def buildProtocol(self, addr):
        p = STRIPServer(self.router)
        p.factory = self
        return p
    
class STRIPClientFactory(ReconnectingClientFactory):
    factor = 2
    
    def __init__(self, router, partner):
        self.router = router
        self.partner = partner
    
    def startedConnecting(self, connector):
        #logger.debug('started connecting')
        pass

    def buildProtocol(self, addr):
        #print 'Connected to %s.' % str(addr)
        #print 'Resetting reconnection delay'
        self.resetDelay()
        
        return STRIPClient(self.router, self.partner)

    def clientConnectionLost(self, connector, reason):
        #logger.info('client connection lost: %s' % reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        #print 'connection failed'
        #logger.info('client connection to %s:%d failed: %s' % (connector.host, connector.port, str(reason)))
        ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                         reason)