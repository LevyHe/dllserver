#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 00:09:10 2021

@author: levy.he
@file  : DllKeyServer.py
"""

from .DllKeyClient import DllKeyGenBase
from .ProxyManager import ProxyManager, ServerForever, err_print

class DllKeyProxy(ProxyManager):
    pass


DllKeyProxy.register('DllKeyGen', DllKeyGenBase)

if __name__ == "__main__":
    print = err_print
    ServerForever(DllKeyProxy)
