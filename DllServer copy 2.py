
import json
import platform

from argparse import ArgumentParser
from multiprocessing.managers import BaseManager
from multiprocessing import Manager, freeze_support
import os
import sys
from pyuds.Scripts import DllKeyGen, BaseKeyGen
import time
from threading import Thread
import signal
server = None
stop_event = None


def serverstop():
    stop_event.set()


def serverinit(event):
    global stop_event
    stop_event = event

def input_thread():
    for s in iter( sys.stdin.readline, ''):
        if s in ['stop\n','']:
            serverstop()
            break

class DllManager(BaseManager):
    pass


DllManager.register('DllKeyGen', DllKeyGen)
DllManager.register('serverstop', serverstop)


def main():
    global stop_event
    e_m = Manager()
    stop_event = e_m.Event()
    name_ext = platform.architecture()[0]
    address = r'\\.\pipe\pyuds_dll_server' + name_ext
    authkey = bytes([ord(x) for x in address + 'token'])
    m = DllManager(address=address, authkey=authkey)
    # server = m.get_server()
    m.start(initializer=serverinit, initargs=(stop_event,))
    sys.stderr.write('start\n')
    sys.stderr.flush()
    print(os.getpid())
    print(m._process.pid)
    stop = Thread(target=input_thread)
    stop.start()
    try:
        while not stop_event.is_set():
            stop_event.wait(1)
    except (KeyboardInterrupt, SystemExit, EOFError):
        pass
    print('stop')
    m.shutdown()
    
    

if __name__ == "__main__":
    freeze_support()
    main()
    os.kill(os.getpid(), signal.SIGINT)
