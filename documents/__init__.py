# Type imports
from beanie import Document
from typing import List

# Import all documents
from .server import Server

# Create a list of all the documents
__documents__: List[Document] = [Server]
