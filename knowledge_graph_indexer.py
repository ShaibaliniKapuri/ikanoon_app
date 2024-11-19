from llama_index.core import SimpleDirectoryReader, KnowledgeGraphIndex, Settings
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core import StorageContext
from llama_index.llms.groq import Groq
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain_community.embeddings import HuggingFaceEmbeddings
from pyvis.network import Network
import IPython
import re
import os

class KnowledgeGraphIndexer:
    def __init__(self, api_key, model_name="llama-3.1-70b-versatile", embed_model_name="thenlper/gte-large"):
        self.llm = Groq(model=model_name, api_key=api_key)
        self.embed_model = LangchainEmbedding(HuggingFaceEmbeddings(model_name=embed_model_name))
        Settings.llm = self.llm
        Settings.chunk_size = 700
        self.graph_store = SimpleGraphStore()
        self.storage_context = StorageContext.from_defaults(graph_store=self.graph_store)

    def build_index(self, documents, max_triplets_per_chunk=3):
        index = KnowledgeGraphIndex.from_documents(
            documents=documents,
            max_triplets_per_chunk=max_triplets_per_chunk,
            storage_context=self.storage_context,
            embed_model=self.embed_model,
            include_embeddings=True
        )
        return index

    def query_index(self, index, query, similarity_top_k=5):
        query_engine = index.as_query_engine(include_text=True, 
                                             response_mode="tree_summarize", 
                                             embedding_mode="hybrid", 
                                             similarity_top_k=similarity_top_k)

        #message_template = f"<|system|>Please check if the following pieces of context has any mention of the keywords provided in the Question. If not, then don't know the answer, just say that you don't know.</s><|user|>Question: {query}Helpful Answer:</s>"
        message_template = f"<|system|>Please review the following context and check if it includes relevant information or mentions of the keywords provided in the Question.If the context lacks relevant details, respond with 'I don't know.' If relevant information is found, answer the Question in a helpful manner, and include any source case numbers or references available in the context to support your answer.<|user|>Question: {query}\nHelpful Answer (with case references where applicable):</s>"


        response = query_engine.query(message_template)
        return response.response.split("<|assistant|>")[-1].strip()

    """
    def visualize_graph(self, index, output_file="content\Knowledge_graph.html"):
        g = index.get_networkx_graph()
        net = Network(notebook=True, cdn_resources="in_line", directed=True)
        net.from_nx(g)
        net.show(output_file)
        # Explicitly open and write with UTF-8 encoding
        with open(output_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Write the content back to ensure correct encoding
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Knowledge graph has been saved to {output_file}")
        net.save_graph(output_file)
        return IPython.display.HTML(filename=output_file)
    """
    #def persist_storage(self):
    #   self.storage_context.persist(persist_dir="persist_dir")


    def persist_storage(self, search_query):
        # Sanitize search query to create a valid directory name
        sanitized_query = re.sub(r'[^a-zA-Z0-9]', '_', search_query)
        persist_dir = os.path.join("persist_dir", sanitized_query)
        
        # Ensure the directory exists
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)
        
        # Persist storage context in the specific directory
        self.storage_context.persist(persist_dir=persist_dir)
        print(f"Graph has been successfully persisted in {persist_dir}")