from flask import Flask, request, jsonify, render_template, g
from flask import current_app as app
from flask_restful import Api, Resource
from fetch_legal_docs import *
from knowledge_graph_indexer import KnowledgeGraphIndexer
from llama_index.core import SimpleDirectoryReader
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading 
from database_connection import *
import shutil

app = Flask(__name__)
api = Api(app)

# Initialize Knowledge Graph Indexer
api_key = "groq_api_key"
indexer = KnowledgeGraphIndexer(api_key)
source_dir = "content"
index = None
documents = None
loaded_graph_name = None



# Function to check if the directory contains files
def is_directory_empty(directory):
    return not any(os.scandir(directory))

# Function to rebuild index
def rebuild_index():
    global index, documents
    if not is_directory_empty(source_dir):
        documents = SimpleDirectoryReader(source_dir).load_data()
        index = indexer.build_index(documents)
        #g.documents = documents  # Store in g
        #g.index = index  # Store in g
        print("Index built successfully!")
    else:
        print("The content directory is empty. Skipping index building.")

# Watchdog event handler class
class Watcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory and event.src_path == source_dir:
            print("Change detected in content directory. Building new index...")
            rebuild_index()

# Start watching the directory
def start_watching():
    event_handler = Watcher()
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=False)
    observer.start()
    print("Started watching the content directory for changes")



#Run directory watcher in a separate thread
watcher_thread = threading.Thread(target = start_watching, daemon = True)
watcher_thread.start()

#-------------------------------------------------------------------------------------------------------

@app.route('/')
def home():
    return render_template("index.html")

#search API
class Search(Resource):
    def post(self):
        data = request.get_json()
        user_id = "1" #data.get("user_id")
        search_query = data.get("search_query")

        # Generate graph name
        graph_name = search_query.replace(" ", "_").lower()

        # Check if graph already exists
        if graph_exists(graph_name):
            print(f"Graph '{graph_name}' already exists. Reusing it.")
        else:
            # Perform the search query with the documents
            perform_search(search_query)
            rebuild_index()

        #save to chat history
        save_user_history(user_id, search_query, graph_name)

        return jsonify({"message": "Search completed, and index has been built."})
        # Retrieve initial response from the indexer
        #initial_response = indexer.query_index(index, search_query)
        #return jsonify({"response": initial_response})



# Before request hook to ensure index is available in g
@app.before_request
def ensure_index():
    if index is not None:
        g.index = index
    else:
        print("Index is not available. No document in content directory")
    #if not hasattr(g, 'index'):  # If g.index does not exist
    #    rebuild_index()  # Rebuild the index if not available


#Query API
class Query(Resource):
    def post(self):
        global loaded_graph_name
        data = request.get_json()
        user_id = "1" #data.get("user_id")
        query = data.get("query")
        search_query = data.get("search_query") #graph_dict.get("graph_name", "NA")
        user_query = data.get("query")
        
        # Generate graph name
        graph_name = search_query.replace(" ", "_").lower()

        # Check if the graph exists
        if loaded_graph_name:
            # Query the active graph
            results = query_graph(loaded_graph_name, user_query)
            if results:
                response = [str(result[0]) for result in results]  # Format results
                return jsonify({"response": response})
            else:
                return jsonify({"response": "No results found for your query."})
        #else:
            #return jsonify({"error": "No graph is loaded. Please load a graph first."}), 400
        elif hasattr(g, 'index') and g.index is not None:  # Ensure the index exists in g
            response = indexer.query_index(g.index, query)
            print(f"Response: {response}")
            return jsonify({"response": response})
        else:
            return jsonify({"error": "Index not available. Please rebuild the index."})
        """
        if graph_exists(graph_name):
            try:
                # Query the graph in Apache AGE
                results = query_graph(graph_name, query)

                # Update chat history
                update_chat_log(user_id, search_query, {"user_query": query, "response": results})

                return jsonify({"response": results})
            except Exception as e:
                print(f"Error while querying the graph: {e}")
                return jsonify({"error": "An error occurred while querying the graph."})
        #else:
            #return jsonify({"error": f"Graph '{graph_name}' does not exist. Please create it first."})

        """

        
        # Query the index with the user's question
        #response = indexer.query_index(g.index, query)
        #print(f"Response: {response}")
        #return jsonify({"response": response})


class ChatHistory(Resource):
    def get(self):
        user_id = "1" #request.args.get("user_id")
        
        query = """
        SELECT search_query, graph_name, chat_log, created_at
        FROM user_chat_history
        WHERE user_id = %s
        ORDER BY created_at DESC;
        """
        cur.execute(query, (user_id,))
        history = cur.fetchall()
        formatted_history = [
            {"search_query": row[0], "graph_name": row[1], "chat_log": row[2], "created_at": row[3]}
            for row in history
        ]
        return jsonify({"history": formatted_history})


class SearchHistory(Resource):
    def get(self):
        user_id = "1" #request.args.get("user_id", "default_user")  # Replace with actual user ID handling

        # Fetch all search queries for the user
        cur.execute("SELECT search_query FROM user_chat_history WHERE user_id = %s", (user_id,))
        results = cur.fetchall()

        return {"history": [row[0] for row in results]}, 200


class LoadChat(Resource):
    def post(self):
        global loaded_graph_name
        data = request.get_json()
        user_id = "1" #data.get("user_id", "default_user")  # Replace with actual user ID handling
        search_query = data.get("search_query")
        graph_name = search_query.replace(" ", "_").lower()

        # Check if the graph exists
        if graph_exists(graph_name):
            #graph_dict["graph_name"] = graph_name
            loaded_graph_name = graph_name
            print(f"Graph '{graph_name}' loaded successfully.")
            return {"message": f"Graph '{graph_name}' loaded successfully."}, 200
        else:
            return {"error": f"Graph '{graph_name}' does not exist"}, 404
        """
        # Fetch previous chat log
        query = 
        SELECT chat_log FROM user_chat_history
        WHERE user_id = %s AND search_query = %s;
        
        cur.execute(query, (user_id, search_query))
        result = cur.fetchone()

        if result:
            chat_log = result[0]  # JSON stored in chat_log
            return {"messages": chat_log}, 200
        else:
            return {"error": "No previous chat log found."}, 404
        """    

        

class Complete(Resource):
    def post(self):

        data = request.get_json()
        search_query = data.get("search_query")

        # Move files to completed directory
        move_files_to_completed()

        if search_query:
            indexer.persist_storage(search_query) 
            message = f"All files have been moved to the 'completed' directory, and graph has been stored for '{search_query}'."
        else:
            message = "All files have been moved to the 'completed' directory, but no search query was provided for graph storage."

        push_json_to_age(persist_dir)
        base_path = "persist_dir"
        nested_folder_list = os.listdir(base_path)
        for folder in nested_folder_list:
            folder_path = os.path.join(base_path,folder)
            shutil.rmtree(folder_path)

        cur.close()
        conn.close()

        return jsonify({"message": message})
        #return jsonify({"message": "All files have been moved to the 'completed' directory."})


# Add resources to the API
api.add_resource(Search, "/search")
api.add_resource(Query, "/query")
api.add_resource(SearchHistory, "/search_history")
api.add_resource(LoadChat, "/load_chat")
api.add_resource(Complete, "/complete")

if __name__ == "__main__":
    #start_watching()
    app.run(debug=True)
