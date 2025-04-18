# Define package-level attributes and constants
__version__ = '1.0'
MAX_RETRIES = 5

# Import modules and sub-packages
from .server import *
from .domain import *
from .utils import *

# Execute code on package import
print('Server initialized')