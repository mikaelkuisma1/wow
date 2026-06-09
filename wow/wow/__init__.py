from taskblaster.repository import Repository
from taskblaster.storage import JSONCodec

# This is just standard taskblaster setup for module to be able
# to encode ASE objects and enable taskblaster to know about parallelization

__version__ = '0.1'


class ASECodec(JSONCodec):
    def encode(self, obj):
        from ase.io.jsonio import default

        return default(obj)

    def decode(self, dct):
        from ase.io.jsonio import object_hook

        return object_hook(dct)


class WOWRepository(Repository):
    def worker_start_hook(self):
        pass

    def worker_finish_hook(self):
        pass


def tb_init_repo(root, read_only=False):
    return WOWRepository(root, usercodec=ASECodec(), read_only=read_only)
