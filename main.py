from fetch_legal_docs import *
from knowledge_graph_indexer import KnowledgeGraphIndexer
from llama_index.core import SimpleDirectoryReader

# Fetch legal documents
#fetch_legal_docs()
perform_search("Domestic Violence Cases in Kolkata")

# Initialize the indexer
api_key = "abcd"
indexer = KnowledgeGraphIndexer(api_key)

# Load documents
documents = SimpleDirectoryReader("content").load_data()

# Build the index
index = indexer.build_index(documents)

# Query the index
query = "Give me important points from the cases? and also provide the source case numbers"
response = indexer.query_index(index, query)
print(f"Response: {response}")

# Visualize the knowledge graph
#indexer.visualize_graph(index)

# Persist the storage context
indexer.persist_storage()
