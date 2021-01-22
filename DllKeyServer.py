

from pyuds.Scripts import DllKeyGen
from ProxyManager import ProxyManager, ServerForever, ServerClient, err_print

class DllKeyProxy(ProxyManager):
    pass

DllKeyProxy.register('DllKeyGen', DllKeyGen)

if __name__ == "__main__":
    print = err_print
    ServerForever(DllKeyProxy)
