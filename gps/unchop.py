import struct
import collections
import numpy as n
from matplotlib import pyplot as plt
import argparse
from collections import deque

def unchop(file, output):
    '''
    Attemps to find dropped bytes from a list of ints and realign the data to correct for them.
    '''
    o_list = []
    with open(file) as f:
        while True:
            curr = f.read(4)
            if len(curr) < 4:
                break
            else:
                while curr[0] != '\x00' and curr[0] != '\xff':
                    curr_i = struct.unpack('>i',curr)[0]
                    f.seek(-3,1)
                    curr = f.read(4)
                o_list.append(curr)
    d = ''.join(o_list)
    with open(output,'w') as f:
        f.write(d)

def find_jump(file, window = 1024, excur_lim = 1e7):
    '''
    Find sudden jumps in a binary data interpreted as ints.
        find_jump(filename, window), where window is the number of ints to average
        over
    '''
    with open(file) as f:
        data = f.read()
    ints = struct.unpack('>{0}i'.format(len(data)/4), data)
    win = collections.deque(maxlen = window)
    flagged = []
    idx = 0
    prev = 1
    for i in ints:
        win.append(i)
        mean = sum(win)/len(win)
        if abs(i - mean) > 1e7:
            win.clear()
            flagged.append((idx, n.abs(i- prev)))
            prev = i
        idx += 1
    return flagged

def run_fft(file, window = 2048):
    '''
    Takes a running fft of the binary data in file
    '''
    plt.ion()
    with open(file) as f:
        data = f.read()
    ints = struct.unpack('>{0}i'.format(len(data)/4), data)
    win = collections.deque(maxlen = window)
    idx = 0
    a, = plt.plot(n.abs(n.fft.fft(ints[:window]-n.mean(ints[:window]))))
    for i in ints:
        win.append(i)
        if len(win) == window:
            a.set_ydata(n.abs(n.fft.fft(win)-n.mean(win)))
            plt.draw()
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot the data in this file.')
    parser.add_argument('f', type = str, help = 'Name for the file containing the input')
    parser.add_argument('o', type = str, help = 'File to write output to')
    args = parser.parse_args()
    o = unchop(args.f, args.o)