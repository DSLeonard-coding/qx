# Import the module object itself under a safe alias first
from . import qx as _qx_module

# Now import everything from .qx (this will bind 'qx' to the instance)
from .qx import *
from .version import __version__

# Access __all__ from the module alias safely
__all__ = list(getattr(_qx_module, '__all__', [])) + ['__version__']