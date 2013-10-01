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

''' STRIP messages '''
class Announcement(object):
    def __init__(self, target, nexthop):
        self.target = target
        self.nexthop = nexthop
    
    def __repr__(self):
        return 'announcing: %s over %s' % (self.target, self.nexthop)
        
class SPCRequest(object):
    def __init__(self, target, distance, cid, pid, key, identity,olddistance, timestamp):
        self.target = target
        self.distance = distance
        self.cid = cid
        self.pid = pid
        self.key = key
        self.lasthop = identity
        self.olddistance = olddistance
        self.timestamp = timestamp
        
    def __repr__(self):
        return 'requesting: %s cid/pid: %d/%d at %s' % (self.target, self.cid, self.pid, self.timestamp)
    
class SPCResponse(object):
    def __init__(self, cid, pid, spid, timestamp, dist):
        self.cid = cid
        self.pid = pid
        self.spid = spid #this is encrypted (the pid of the shortest path)
        self.timestamp = timestamp
        self.dist = dist #this is encrypted (the distance of the shortest path)
        
    def __repr__(self):
        return 'responding: %d/%d' % (self.cid, self.pid)


class HandshakeRequest(object):
    def __init__(self, source):
        self.source = source

class HandshakeResponse(object):
    def __init__(self, accept, destination):
        self.accept = accept      
        self.destination = destination  
        
''' messages for the distance vector protocol '''
class DVAnnouncement(object):
    def __init__(self, target, nexthop, distance, path):
        self.target = target
        self.nexthop = nexthop
        self.distance = distance
        self.path = path
    
    def __repr__(self):
        return 'announcing: %s,%s,%d,%s' % (self.target, self.nexthop, self.distance, str(self.path))