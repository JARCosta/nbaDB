# Define package-level attributes and constants
__version__ = '1.0'
MAX_RETRIES = 5

# Import modules and sub-packages
from .server import *
from .serverImpl import *
from .domain import *

# Execute code on package import
print('Package server initialized')