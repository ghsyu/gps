#!/usr/bin/env python

import numpy as n
import threading as mp
import struct
import time
import socket
import Queue
#Imports katcp_wrapper only if GpsSampler is instantiated

class MockFpgaClient(object):
    '''
    This class imitates katcp's FpgaClient's behavior so that some of the methods
    that call it can be reused in the case that it is not available
    '''
    def __init__(self, directory):
        self.directory = directory
    def write_int(self, register, data):
        target = '/'.join((self.directory,register))
        data = struct.pack('>I', data)
        with open(target,'w') as f:
            f.write(data)
    def read(self, register, length, offset = 0):
        target = '/'.join((self.directory,register))
        with open(target, 'r') as f:
            output = f.read(length)
        return struct.unpack('%d>I'%(length//4), output)
    def read_int(self, register):
        self.read(4)
        
class GpsSampler(object):
    '''
    
    '''
    def __init__(self, hostname, decimation):
        from corr import katcp_wrapper as kw
        self.fpga = kw.FpgaClient(hostname)
        time.sleep(1)
        self.decimation = decimation
        self.fpga.status()
        
    def progdev(self, boffile):
        self.fpga.progdev(boffile)
        time.sleep(2)
    
    def start(self):
        self.fpga.write_int('throttle_ctrl', self.decimation)
        self.fpga.write_int('enable',1)
    
    def set_decimation(self, decimation):
        self.fpga.write_int('throttle_ctrl', decimation)
    
    def grab_data(self, q, addr_max=2 ** 11):
        BRAM = True
        while True:
            current = self.fpga.read_int('current_address')
            if BRAM and current:
                q.put(self.fpga.read('Shared_BRAM', 4*(addr_max)))
                BRAM = False
            elif not(BRAM or current):
                q.put(self.fpga.read('Shared_BRAM1', 4*(addr_max)))
                BRAM = True
                
    
    def sampler(self, samplerate, bram_size = 2**11, maxtime=None):
        self.start()
        time.sleep(1)
        q = Queue.Queue()
        grab = mp.Thread(target=self.grab_data, args=(q,))
        grab.daemon = True
        start = time.time()
        total_len = 0
        raw = []
        try:
            f = open('gps_frequencies', 'w')
            grab.start()
            f.write('Sample rate = {0}\n'.format(samplerate))
            while maxtime == None or (time.time() - start) < maxtime:
                x = q.get()
                data = struct.unpack('>{0}I'.format(bram_size), x)
                f.write(data)
        except KeyboardInterrupt:
            print('Keyboard interrupt caught, stopping...')
        finally:
            f.close()
    
    

class NoKatcpTx(GpsSampler):
    '''
    A version of GpsSampler for use when katcp is not available.  This requires separate
    processes for sending and receiving data.  This one should run on the fpga.
    '''
    def __init__(self, boffile, decimation, address = '192.168.1.100', port = 8888):
        import subprocess
        proc = subprocess.Popen(['%s%s'%('/boffiles/',boffile)])
        self.dir = '/proc/%d/hw/ioreg'%(proc.pid)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect((address, port))
        self.fpga = MockFpgaClient(self.dir)
        
    def set_decimation(self, decimation):
        self.fpga.write_int('throttle_ctrl', decimation)
    
    def start(self):
        self.grab_data(self.sock)
        
class NoKatcpRx(object):
    '''
    A version of GpsSampler for use when katcp is not available.
    This end runs on the CPU
    '''
    def __init__(self, samplerate, port = 8888, bram_size = 2**11):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        self.samplerate = samplerate
        self.bram_size = bram_size
    def start(self, maxtime = None):
        #XXX convert to old-style format strings for python 2.6 compatibility
        start = time.time()
        total_len = 0
        raw = []
        try:  
            grab.start()
            f = open('gps_frequencies', 'w')
            f.write('Sample rate = {0}\n'.format(self.samplerate))
            while maxtime == None or (time.time() - start) < maxtime:
                x = self.recv(8192)
                data = struct.unpack('>{0}I'.format(bram_size), x)
                f.write(x)
        except KeyboardInterrupt:
            print('Keyboard interrupt caught, stopping...')
        finally:
            f.close()
            grab.close()
