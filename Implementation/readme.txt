This is the implementation of STRIP: Privacy=Preserving Vector-Based Routing.

It is probably a good idea to read the paper to get an idea what STRIP does...

Everything is written in Python. But you will need to install some additional libraries:
Twisted - http://twistedmatrix.com/trac/
gmpy - http://code.google.com/p/gmpy/

!!!!!! WARNING !!!!!!!!!!
This is not a fully implemented routing protocol! In its current state
the protocol doesn't handle losing a connection properly.
Also, it does not!!! manipulate the systems routing table. It holds its
own virtual forwarding table in memory.
The whole idea of this exercise was to showcase the practicability of 
the added privacy-preserving crypto. Not to create a new routing protocol.


This software is released under the MIT license: 

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

Feedback is always welcome. You can reach me at wilko.henecka@adelaide.edu.au