# Type imports
from beanie import Document
from typing import List

# Import all documents and BaseModels
from .server import *

# Create a list of all the documents
__documents__: List[Document] = [Server]
