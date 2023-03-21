# Define package-level attributes and constants
__version__ = '1.0'
MAX_RETRIES = 5

# Import modules and sub-packages
from .root import *
from .teams import *
from .players import *
from .games import *

# Execute code on package import
print('Package domain initialized')