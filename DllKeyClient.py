
import os
from pyuds.Scripts import DllKeyGen, BaseKeyGen
from ProxyManager import ProxyManager, ServerClient
from traceback import format_exc

class DllKeyProxy(ProxyManager):
    pass

DllKeyProxy.register('DllKeyGen', DllKeyGen)


class DllKeyGen_x32(BaseKeyGen):
    def __init__(self, *seed_levels, dll_path=None):
        if dll_path:
            self.dll_path = os.path.abspath(dll_path)
            self.seed_levels = seed_levels
            cmd = [r'dist\DllKeyServer_32bit.exe']
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

if __name__ == "__main__":
    key = DllKeyGen_x32(1, 3, 5, 0x11, dll_path="GAC_A39_SRS.dll")
    print(key.KenGen(0x1, [3, 6, 3, 4]))
    # cmd = [r'dist\DllKeyServer_32bit.exe']
    # proc, obj = ServerClient(cmd, DllKeyProxy)
    # try:
    #     kengen = obj.DllKeyGen(1, 3, 5, 0x11, dll_path="GAC_A39_SRS.dll")
    #     print(kengen.KenGen(0x1, [3, 6, 3, 4]))
    # except:
    #     print(format_exc())
    # finally:
    #     proc.stdout.close()
    #     proc.stdin.close()
    #     proc.kill()
