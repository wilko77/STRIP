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
Paillier Cryptosystem

usage example:
#keypair generation
sk, pk = generateKeyPair(1024)
message = 42
#normal encryption
ciphertext = encrypt(message, pk)
#homomorphic mulitplication with a scalar
ciphertext_mul = multiply(ciphertext, 100, pk)
#homomorphic addition of two ciphertexts
ciphertext_add = add(ciphertext_mul, ciphertext, pk)
#decryption
newMessage = decrypt(ciphertext_add, sk)

'''
import gmpy
from random import randint
import time


class PrivateKey(object):
    def __init__(self, keysize, n, nsquared, p, q, p_inv, hp, hq):
        self.keysize =keysize
        self.n = n
        self.nsquared = nsquared
        self.p = p
        self.q = q
        self.p_inv = p_inv
        self.hp = hp
        self.hq = hq

class PublicKey(object):
    def __init__(self, keysize, n, nsquared):
        self.keysize = keysize
        self.n = n
        self.nsquared = nsquared

def generateKeyPair(keySize):
    
    primelength = keySize/2
    p = _randomPrime(primelength)
    q = _randomPrime(primelength)
    n = p*q
    nsquared = pow(n,2)
    hp = _L(((p-1)*n+1) % p**2 ,p)
    hp = gmpy.invert(hp,p)
    hq = _L(((q-1)*n+1) % q**2 ,q)
    hq = gmpy.invert(hq, q)
    return PrivateKey(keySize, n, nsquared, p, q, gmpy.invert(p,q), hp, hq),PublicKey(keySize, n, nsquared)


def encrypt(message, publicKey, privateKey=None):
    # Compute ciphertext = (mn+1)r^n (mod n^2) in two stages: (mn+1) and (r^n).
    r = randint(0,2**publicKey.keysize - 1)
    tmp = message * publicKey.n + 1 % publicKey.nsquared      
    randomness = pow(r,publicKey.n,publicKey.nsquared)
    return tmp*randomness % publicKey.nsquared
        

def decrypt(ciphertext, privateKey):
    mp = _L(pow(ciphertext,privateKey.p-1,pow(privateKey.p,2)), privateKey.p) * privateKey.hp % privateKey.p
    mq = _L(pow(ciphertext,privateKey.q-1,pow(privateKey.q,2)), privateKey.q) * privateKey.hq % privateKey.q
    return _CRT(mp, mq, privateKey);

def add(ciphertext1, ciphertext2, publicKey):
    """ addition of two ciphertexts
    Such that Dec(add(Enc(m1),Enc(m2))) = m1+m2
    """
    return ciphertext1 * ciphertext2 % publicKey.nsquared


def multiply(ciphertext, scalar, publicKey):
    """ multiplication of a scalar to a ciphertext
    such that Dec(multiply(Enc(m),k)) = k*m
    """
    return pow(ciphertext, scalar, publicKey.nsquared)
    

def _randomPrime(bitlength):
    """ returns a random prime number consisting of bitlength bits """
    while True:
        p = gmpy.next_prime(randint(2**(bitlength-1), 2**bitlength - 1))
        if p < 2**bitlength:
            return p

def _L(u,n):
# L(u)=(u-1)/n
    return (u-1)/n

def _CRT(m1, m2, privateKey):
    u = (m2-m1) * privateKey.p_inv % privateKey.q
    return m1 + u * privateKey.p

if __name__ == '__main__':
    sk, pk = generateKeyPair(1024)
    message = 123456789
    start = time.clock()
    m2 = 987654321
    c1 = encrypt(message, pk)
    c2 = encrypt(m2, pk)
    m = decrypt(multiply(c1,10,pk),sk)
    print m
    