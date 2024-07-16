# Type imports
from beanie import Document
from typing import List

# Import all documents
from .server import Server


class Database:
    def __init__(self, documents: List[Document]):
        self.documents = documents


# Create a list of all the documents
__documents__: List[Document] = [Server]

# Define database
database = Database(__documents__)
