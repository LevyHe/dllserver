
from DllServer import Connection
from argparse import ArgumentParser, Namespace, ArgumentError
import os
import json
import sys
# from pyuds.Scripts import DllKeyGen, BaseKeyGen
import platform
from subprocess import Popen, PIPE
import time
import signal

import pickle

class DllClient(object):
    def __init__(self, *seed_levels, dll_path=None):
        if platform.architecture()[0] == '64bit':
            # exe_file = [r'dist\DllServer_32bit.exe']
            exe_file = [r'C:\Python\Python37x86\python.exe', 'DllServer.py']
            name_ext = '32bit'
        else:
            name_ext = '64bit'
            exe_file = [r'dist\DllServer_64bit.exe']
            # exe_file = [r'C:\Python\Python37x86\python.exe', 'DllServer.py']
        if dll_path is not None:

            self.seed_levels = list(seed_levels)
            address = r'\\.\pipe\pyuds_dll_server' + name_ext
            authkey = bytes([ord(x) for x in address + 'token'])
            self.address = address
            self.authkey = authkey
            self.dll_path = dll_path

            self._proc = Popen(exe_file, shell=True, stderr=sys.stderr, stdout=PIPE, stdin=PIPE, bufsize=16, universal_newlines=False)
            self.conn = Connection(self._proc.stdout, self._proc.stdin)
            # print(self._proc.stdout.readline())
            # print(self._proc.stdout.readline())
            # print(self._proc.stdout.readline())
            # print(self._proc.stderr.readline())
            # for s in iter(self._proc.stderr.readline, ''):
            #     print(s)
            #     if s == 'start\n':
            #         break

            # self.m = DllManager(address=self.address, authkey=self.authkey)
            # self.m.connect()
            # self.dll = self.m.DllKeyGen(*self.seed_levels, dll_path=os.path.abspath(self.dll_path))
            # self.m.serverstop()

        else:
            self.seed_levels = []

    def KenGen(self, level, seed):
        self.conn.send((level, seed))
        args = self.conn.recv()
        print(args)
        # if level not in self.seed_levels:
        #     return seed
        # return self.dll.KenGen(level, seed)

    def __del__(self):
        # self._proc.stdin.write('stop\n')
        pass
        # self.m.serverstop()

        # self.m.serverstop()

        # self._proc.kill()  # signal.SIGINT


# def main(args):
#     parser = ArgumentParser(description='Start a key Security Dll Server Process')
#     parser.add_argument('-p', '--path', type=str, required=True, help='the dll path')
#     parser.add_argument('-l', '--level', type=lambda js: json.loads(js), required=True, help='supported security level list string')
#     parser.add_argument('-a', '--pipe', type=str, default='dll', help='the pipe name of the server')
#     args = parser.parse_args(args)
#     dll_name = os.path.basename(args.path)
#     address = r'\\.\pipe\pyuds_' + args.pipe + dll_name
#     authkey = bytes([ord(x) for x in 'pipe_pyuds_' + args.pipe + dll_name])
#     m = DllManager(address=address, authkey=authkey)
#     m.connect()
#     dll = m.DllKeyGen(*args.level, dll_path=os.path.abspath(args.path))
#     print(dll.KenGen(0x11, [3, 5, 3, 4]))


if __name__ == "__main__":
    dll = DllClient(1, 3, 5, 0x11, dll_path="GAC_A39_SRS.dll")

    print(dll.KenGen(0x1, [3, 5, 3, 4]))
    print(dll.KenGen(0x1, [3, 5, 3, 4]))
    print(dll.KenGen(0x1, [3, 5, 3, 4]))
    # del dll
    # dll.m.serverstop()
    # main('-p GAC_A39_SRS.dll -l "[1,3,5]"'.split())
