
import json
import platform
import pickle
from argparse import ArgumentParser
from multiprocessing.managers import BaseManager
from multiprocessing import Manager, freeze_support, Process
import os,io
import sys
# from pyuds.Scripts import DllKeyGen, BaseKeyGen
import time
from threading import Thread
import signal
from subprocess import Popen, PIPE

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


class Token(object):
    '''
    Type to uniquely identify a shared object
    '''
    __slots__ = ('typeid', 'conn', 'id')

    def __init__(self, typeid, conn, id):
        (self.typeid, self.conn, self.id) = (typeid, conn, id)

    def __getstate__(self):
        return (self.typeid, self.conn, self.id)

    def __setstate__(self, state):
        (self.typeid, self.conn, self.id) = state

    def __repr__(self):
        return '%s(typeid=%r, conn=%r, id=%r)' % \
               (self.__class__.__name__, self.typeid, self.conn, self.id)

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

def err_print(*args,**kwargs):
    print(*args, **kwargs, file=sys.stderr)

class BaseProxy(object):
    
    def __init__(self, token, manager=None, exposed=None):
        self._conn = token.conn
        self._typeid = token.typeid
        self._id = token.id

    def _callmethod(self, methodname, args=(), kwds={}):
        self._conn.send((self._id, methodname, args, kwds))
        kind, result = self._conn.recv()
        if kind == '#RETURN':
            return result
        elif kind == '#PROXY':
            pass

    def __reduce__(self):
        return (RebuildProxy, (MakeProxyType, self._typeid, self._exposed_))

def MakeProxyType(name, exposed):
    dic = {}
    for meth in exposed:
        exec('''def %s(self, *args, **kwds):
        return self._callmethod(%r, args, kwds)''' % (meth, meth), dic)

    ProxyType = type(name, (BaseProxy,), dic)
    ProxyType._exposed_ = exposed
    return ProxyType


def PipeProxy(token, server, exposed=None):
    ProxyType = MakeProxyType('PipeProxy[%s]' % token.typeid, exposed)
    proxy = ProxyType(token, server, exposed)
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
        return 'test1'

class Server(object):

    _registry = {}
    _public = ('_create', '_get_methods')

    def __init__(self, reader, writer):
        self.conn = Connection(reader, writer)
        self.obj_list = {}

    def public_request(self, funcname, typeid, args, kwds={}):
        if funcname in self._public:
            func = getattr(self, funcname)
            result = func(typeid, *args, **kwds)
            msg = ('#RETURN', result)
            self.conn.send(msg)

    def call_handler(self, ident, funcname, args, kwds={}):
        obj, exposed = self.obj_list[ident]
        func = getattr(obj, funcname)
        result = func(*args, **kwds)
        msg = ('#RETURN', result)
        self.conn.send(msg)

    def serve_forever(self):
        try:
            while True:
                request = self.conn.recv()
                ident, funcname, args, kwds = request
                if ident == None:
                    typeid = args[0]
                    self.public_request(funcname, typeid, args[1:], kwds)
                elif ident in self.obj_list:
                    self.call_handler(ident, funcname, args, kwds)
                else:
                    pass
                # print('server', args, file=sys.stderr)
                # self.conn.send(args)
        except (KeyboardInterrupt, SystemExit, EOFError, OSError):
            print('process ended', file=sys.stderr)

    def _get_conn(self):
        return self.conn

    def _create(self, typeid, *args, **kwds):
        caller, exposed = self._registry[typeid]
        obj = caller(*args, **kwds)
        ident = '%x' % id(obj)
        self.obj_list[ident] = (obj, exposed)
        return ident, tuple(exposed)

    @classmethod
    def register(cls, typeid, caller=None, proxytype=None):

        if '_registry' not in cls.__dict__:
            cls._registry = cls._registry.copy()

        exposed = all_methods(caller)
        cls._registry[typeid] = (caller, exposed)
        
        def temp(self, *args, **kwds):
            conn = self._get_conn()
            ident,  exposed = dispatch(conn, None, '_create', (typeid,)+args, kwds)
            token = Token(typeid, conn, ident)
            proxy = PipeProxy(token, self, exposed)
            return proxy
        temp.__name__ = typeid
        setattr(cls, typeid, temp)

class TestServer(Server):
    pass


TestServer.register('TestClass', TestClass)

# def main():
#     reader = io.open(sys.stdin.fileno(), mode='rb', closefd=False)
#     writer = io.open(sys.stdout.fileno(), mode='wb', closefd=False)
#     con = Connection(reader, writer)
#     try:
#         while True:
#             args = con.recv()
#             print('server',args, file=sys.stderr)
#             con.send(args)
#     except (KeyboardInterrupt, SystemExit, EOFError):
#         print('process ended', file=sys.stderr)

def ServerStart():
    reader = io.open(sys.stdin.fileno(), mode='rb', closefd=False)
    writer = io.open(sys.stdout.fileno(), mode='wb', closefd=False)
    t = TestServer(reader, writer)
    t.serve_forever()



if __name__ == "__main__":
    if len(sys.argv) > 1:
        err_print('start',os.getpid())
        ServerStart()
        err_print(os.getpid())
    else:
        cmd = ['python', 'DllServer.py', 'server']
        _proc = Popen(cmd, shell=False, stderr=sys.stderr,
                           stdout=PIPE, stdin=PIPE, bufsize=16, universal_newlines=False)
        t = TestServer(_proc.stdout, _proc.stdin)
        test = t.TestClass()
        print(test.test1())
        print(test.test1())
        _proc.stdout.close()
        _proc.stdin.close()
        _proc.kill()
        print(_proc.pid, os.getpid())
        
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
