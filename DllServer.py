
import json
import platform
import pickle
from argparse import ArgumentParser
from multiprocessing.managers import BaseManager
from multiprocessing import Manager, freeze_support
import os,io
import sys
# from pyuds.Scripts import DllKeyGen, BaseKeyGen
import time
from threading import Thread
import signal

def pack_data(args):
    data = pickle.dumps(args)
    num = len(data)
    num_b = num.to_bytes(4,'little')
    all_num = ((num + 4 + 15)//16) * 16
    res = b'\0' * (all_num - num - 4)
    return num_b + data + res

def unpack_data(data):
    args = pickle.loads(data)
    return args

class Connection(object):
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    def read_bytes(self):
        num_b = self.reader.read(4)
        num = int.from_bytes(num_b, 'little')
        r_num = (num + 4 + 15) // 16
        data = self.reader.read((r_num * 16) - 4)
        data = data[:num]
        return data

    def write_bytes(self, data):
        self.writer.write(data)
        self.writer.flush()

    def recv(self):
        data = self.read_bytes()
        return unpack_data(data)

    def send(self, args):
        data = pack_data(args)
        # num = (len(data) + 15) / 16
        self.write_bytes(data)


def all_methods(obj):
    temp = []
    for name in dir(obj):
        func = getattr(obj, name)
        if callable(func) and name[0] != '_':
            temp.append(name)
    return temp


def dispatch(c, id, methodname, args=(), kwds={}):
    '''
    Send a message to manager using connection `c` and return response
    '''
    c.send((id, methodname, args, kwds))
    kind, result = c.recv()
    if kind == '#RETURN':
        return result


class BaseProxy(object):
    
    def __init__(self, conn, typeid, manager=None, exposed=None):
        self.conn = conn
        self.typeid = typeid

    def _callmethod(self, methodname, args=(), kwds={}):
        self.conn.send((self.typeid, methodname, args, kwds))
        kind, result = self.conn.recv()
        if kind == '#RETURN':
            return result
        elif kind == '#PROXY':
            pass

    def __reduce__(self):
        return (RebuildProxy, (MakeProxyType, self.typeid, self._exposed_))

def MakeProxyType(name, exposed):
    dic = {}
    for meth in exposed:
        exec('''def %s(self, *args, **kwds):
        return self''' % (meth), dic)
        # exec('''def %s(self, *args, **kwds):
        # return self._callmethod(%r, args, kwds)''' % (meth, meth), dic)

    ProxyType = type(name, (BaseProxy,), dic)
    ProxyType._exposed_ = exposed
    return ProxyType

def PipeProxy(conn, typeid, server, exposed=None):

    if exposed is None:
        exposed = dispatch(conn, None, 'get_methods')
    ProxyType = MakeProxyType('PipeProxy[%s]' % typeid, exposed)
    proxy = ProxyType(conn, typeid, server, exposed)
    return proxy

def RebuildProxy(func, name, exposed):
    return func(name, exposed)

def test_func():
    print('test_func')
    return 'test_func'

class TestClass(object):
    def __init__(self):
        print('TestClass')
    def test1(self):
        pass
    pass
class Server(object):

    _registry = {}
    _public = ('_create', '_get_methods')

    def __init__(self):
        reader = io.open(sys.stdin.fileno(), mode='rb', closefd=False)
        writer = io.open(sys.stdout.fileno(), mode='wb', closefd=False)
        self.conn = Connection(reader, writer)

    def public_request(self, funcname, args, kwds={}):
        if funcname in self._public:
            func = getattr(self, funcname)
            result = func(self, *args, **kwds)
            msg = ('#RETURN', result)
            self.conn.send(msg)

    def serve_forever(self):
        try:
            while True:
                request = self.conn.recv()
                typeid, funcname, args, kwds = request
                if typeid == None:
                    pass
                elif typeid in self._registry:
                    pass
                else:
                    pass
                # print('server', args, file=sys.stderr)
                # self.conn.send(args)
        except (KeyboardInterrupt, SystemExit, EOFError):
            print('process ended', file=sys.stderr)

    def _get_conn(self):
        return self.conn

    def _create(self):
        pass

    @classmethod
    def register(cls, typeid, caller=None, proxytype=None):

        if '_registry' not in cls.__dict__:
            cls._registry = cls._registry.copy()

        exposed = all_methods(caller)
        cls._registry[typeid] = (caller, exposed)
        
        def temp(self, *args, **kwds):
            conn = self._get_conn()
            proxy = PipeProxy(conn, typeid, self, exposed)
            return proxy
        temp.__name__ = typeid
        setattr(cls, typeid, temp)

class TestServer(Server):
    pass


TestServer.register('TestClass', TestClass)

def main():
    reader = io.open(sys.stdin.fileno(), mode='rb', closefd=False)
    writer = io.open(sys.stdout.fileno(), mode='wb', closefd=False)
    con = Connection(reader, writer)
    try:
        while True:
            args = con.recv()
            print('server',args, file=sys.stderr)
            con.send(args)
    except (KeyboardInterrupt, SystemExit, EOFError):
        print('process ended', file=sys.stderr)


if __name__ == "__main__":
    t = TestServer()
    # a= 
    print(dir(t.TestClass()))
    print(dir(t.TestClass().test1()))
    # t = PipeProxy(None, 'test', None, ('t1', 't2', 't3'))

    # print(dir(t))
    # print(dir(t.test_func()))
    # pass
    # print(Test().__reduce__())
    # t = MakeProxyType('test',('t1','t2','t3'))
    # print(dir(t))
    # print(dir(t(1,2)))
    # print(callable(Server))
    # print(type('proxy[11]', (Server,), {}))
    # main()
    # data = pack_data(1)
    # print(len(data))
    # print(data)
    # freeze_support()
    # main()
    # os.kill(os.getpid(), signal.SIGINT)
