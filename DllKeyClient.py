#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 00:08:58 2021

@author: levy.he
@file  : DllKeyClient.py
"""

import os
from ..SecurityKey import BaseKeyGen
from .ProxyManager import ProxyManager, ServerClient
import ctypes
import platform
import struct

if platform.architecture()[0] == '64bit':
    is_64bit = True
else:
    is_64bit = False

KEY_ARRAY_SIZE = 64
c_byte_a = ctypes.c_char_p
c_size = ctypes.c_uint32
c_level = ctypes.c_uint32
c_buf = ctypes.c_char * KEY_ARRAY_SIZE
rtn_status = ctypes.c_int

class DllFileError(Exception):
    pass

class DllKeyGenBase(BaseKeyGen):
    
    def __init__(self, *seed_levels, dll_path=None):
        self.dll_path = dll_path
        if dll_path is not None:
            self.seed_levels = seed_levels
            self.dll = ctypes.cdll.LoadLibrary(dll_path)
            try:
                self.GenerateKeyEx = self.dll.GenerateKeyEx
                self.GenerateKeyEx.argtypes = [c_byte_a, c_size, c_level, c_byte_a, c_byte_a, c_size, ctypes.POINTER(c_size)]
                self.dll_type = 'Basic'
            except:
                self.GenerateKeyEx = self.dll.GenerateKeyExOpt
                self.GenerateKeyEx.argtypes = [c_byte_a, c_size, c_level, c_byte_a, c_byte_a, c_byte_a, c_size, ctypes.POINTER(c_size)]
                self.dll_type = 'Opt'
            
            self.GenerateKeyEx.restype = rtn_status
        else:
            self.seed_levels = []
    
    def KenGen(self, level, seed):
        if self.dll_path is None:
            return None
        key = c_buf()
        _seed = c_buf(*seed)
        key_out_size = c_size(0)
        varint = ''
        if self.dll_type == 'Opt':
            rtn = self.GenerateKeyEx(_seed, len(seed), level, varint.encode(
                'ascii'), varint.encode('ascii'), key, KEY_ARRAY_SIZE, ctypes.byref(key_out_size))
        else:
            rtn = self.GenerateKeyEx(_seed, len(seed), level, varint.encode(
                'ascii'), key, KEY_ARRAY_SIZE, ctypes.byref(key_out_size))
        if rtn == 0:
            key = key[0:key_out_size.value]
            return list(key)
        else:
            return None


def arch_type(dll_file):
    with open(dll_file, 'rb') as f:
        doshdr = f.read(64)
        magic, padding, offset = struct.unpack('2s58si', doshdr)
        if magic != b'MZ':
            return None
        f.seek(offset, os.SEEK_SET)
        pehdr = f.read(6)
        magic, padding, machine = struct.unpack('2s2sH', pehdr)
        if magic != b'PE':
            return None
        archs = {0x014c: 'i386', 0x0200: 'IA64', 0x8664: 'x64'}
        return archs.get(machine, 'unknown')

if is_64bit:
    class DllKeyProxy(ProxyManager):
        pass

    DllKeyProxy.register('DllKeyGen', DllKeyGenBase)

    class DllKeyGen_x32(object):
        def __init__(self, *seed_levels, dll_path=None):
            if dll_path:
                self.dll_path = dll_path
                self.seed_levels = seed_levels
                server_exe = os.path.join(os.path.dirname(__file__),'DllKeyServer_32bit.exe')
                cmd = [server_exe]
                self.proc, self.obj = ServerClient(cmd, DllKeyProxy)
                self.kengen = self.obj.DllKeyGen(*seed_levels, dll_path=self.dll_path)
                
            else:
                self.seed_levels=[]

        def KenGen(self, level, seed):
            if level in self.seed_levels:
                return self.kengen.KenGen(level, seed)
            else:
                return seed

        def __del__(self):
            self.proc.stdout.close()
            self.proc.stdin.close()
            self.proc.kill()

    class DllKeyGen(BaseKeyGen):
        def __init__(self, *seed_levels, dll_path=None):
            arch = arch_type(dll_path)
            if arch == 'i386':
                gen_type = DllKeyGen_x32
                DllKeyGen_x32(*seed_levels, dll_path=dll_path)
            elif arch == 'x64':
                gen_type = DllKeyGenBase
                DllKeyGenBase(*seed_levels, dll_path=dll_path)
            else:
                raise DllFileError(f'A not supported dll type [{arch}]')
            self.keygen = gen_type(*seed_levels, dll_path=dll_path)

        def KenGen(self, level, seed):
            return self.keygen.KenGen(level, seed)
else:
    DllKeyGen = DllKeyGenBase


if __name__ == "__main__":
    key = DllKeyGen(1, 3, 5, 0x11, dll_path="GAC_A39_SRS.dll")
    print(key.KenGen(0x1, [3, 6, 3, 4]))

