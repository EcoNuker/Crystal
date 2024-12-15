# Type imports
from beanie import Document
from typing import List

# Import all documents
from .server import *

# Import all models
from .models.models import *
from . import projections

# Create a list of all the documents
__documents__: List[Document] = [Server]
