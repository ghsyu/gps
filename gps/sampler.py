#!/usr/bin/env python

import numpy as n
import threading as mp
import struct
import time
import Queue
import argparse

class GpsSampler(object):
    '''
    
    '''
    def __init__(self, hostname, decimation):
        from corr import katcp_wrapper as kw
        self.fpga = kw.FpgaClient(hostname)
        time.sleep(1)
        self.decimation = decimation
        
    def progdev(self, boffile):
        self.fpga.progdev(boffile)
        time.sleep(2)
        self.fpga.status()
        
    def setup(self):
        self.fpga.write_int('enable',0)
        self.fpga.write_int('throttle_ctrl', self.decimation)
        self.fpga.write_int('enable',1)
    
    def set_decimation(self, decimation):
        self.fpga.write_int('throttle_ctrl', decimation)
    
    def grab_data(self, q, maxtime, start, addr_max=2 ** 11):
        BRAM = True
        while maxtime == None or (time.time() - start) < maxtime:
            current = self.fpga.read_int('current_BRAM')
            if BRAM and current:
                q.put(self.fpga.read('Shared_BRAM', 4*(addr_max)))
                BRAM = False
            elif not(BRAM or current):
                q.put(self.fpga.read('Shared_BRAM1', 4*(addr_max)))
                BRAM = True
                
    
    def start(self, filename, bram_size = 2**11, maxtime=None, raw_output = True):
        self.setup()
        time.sleep(1)
        q = Queue.Queue()
        start = time.time()
        grab = mp.Thread(target=self.grab_data, args=(q, maxtime, start))
        grab.daemon = True
        total_len = 0
        raw = []
        try:
            f = open(filename, 'w')
            grab.start()
            while maxtime == None or (time.time() - start) < maxtime:
                if not q.empty():
                    x = q.get(timeout = 1)
                    if raw_output:
                        f.write(x)
                    else:
                        data = struct.unpack('>{0}i'.format(bram_size), x)
                        output = '\n'.join((str(i) for i in data))
                        f.write(output+'\n')
        except KeyboardInterrupt:
            print('Keyboard interrupt caught, stopping...')
        finally:
            f.close()
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot the data in this file.')
    parser.add_argument('f', type = str, help = 'Name for the file containing the output')
    parser.add_argument('--d', type = int, default = 2000, help = 'How much the filter decimates by.')
    parser.add_argument('--t', type = int, default = 6000, help = 'how long to take data')
    args = parser.parse_args()
    A = GpsSampler('169.254.7.1', args.d/20)
    A.setup()
    time.sleep(.5)
    A.start(args.f, maxtime = args.t)