import os
import json
import psycopg2

# Path to the persist storage directory
persist_dir = "persist_dir"

# Connect to PostgreSQL with Apache AGE
conn = psycopg2.connect(
    dbname="postgres",
    user="shaiba",
    password="Shaibathedog8#",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Ensure AGE is loaded
cur.execute("LOAD 'age';")
cur.execute("SET search_path = ag_catalog, public;")

# Function to create a graph
def create_graph(graph_name):
    cur.execute(f"SELECT * FROM ag_catalog.create_graph('{graph_name}');")
    print(f"Graph '{graph_name}' created.")

# Function to add nodes and edges to the graph
def insert_into_graph(graph_name, json_data):
    for node in json_data.get("nodes", []):
        query = f"""
        SELECT * FROM cypher('{graph_name}', $$
        CREATE (n:{node['label']} {{id: {node['id']}, properties: {json.dumps(node['properties'])}}})
        $$) AS (a agtype);
        """
        cur.execute(query)

    for edge in json_data.get("edges", []):
        query = f"""
        SELECT * FROM cypher('{graph_name}', $$
        MATCH (a), (b)
        WHERE a.id = {edge['start_id']} AND b.id = {edge['end_id']}
        CREATE (a)-[:{edge['label']} {{properties: {json.dumps(edge['properties'])}}}]->(b)
        $$) AS (a agtype);
        """
        cur.execute(query)

# Main process to load JSON and push to Apache AGE
def push_json_to_age(persist_dir):
    
    for root, dirs, files in os.walk(persist_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)

                # Read and parse JSON data
                with open(file_path, "r", encoding="utf-8") as json_file:
                    json_data = json.load(json_file)

                # Create a graph for the JSON file (use file name as graph name)
                #graph_name = os.path.splitext(root)[0]
                graph_name = root+"_"+file.split(".")[0]#os.path.splitext(json_file)[0]

                # Check if the graph already exists
                if graph_exists(graph_name):
                    print(f"Graph '{graph_name}' already exists. Skipping creation and data insertion.")
                    return  
                else:
                    create_graph(graph_name)

                # Insert data into the graph
                insert_into_graph(graph_name, json_data)
                print(f"Data from {root} inserted into graph '{graph_name}'.")
    try:
        # Commit changes and close connection
        conn.commit()
        print("All data pushed to Apache AGE.")
    except:
        print("calling commit again")    



def save_user_history(user_id, search_query, graph_name):
    chat_log = []  # Initial empty log
    query = """
    INSERT INTO user_chat_history (user_id, search_query, graph_name, chat_log)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (user_id, search_query)
    DO UPDATE SET chat_log = EXCLUDED.chat_log;
    """
    cur.execute(query, (user_id, search_query, graph_name, json.dumps(chat_log)))
    conn.commit()
    print(f"History saved for user '{user_id}' with graph '{graph_name}'.")




def update_chat_log(user_id, search_query, new_entry):
    query = """
    UPDATE user_chat_history
    SET chat_log = jsonb_set(
        COALESCE(chat_log, '[]'::jsonb), 
        '{-1}', 
        %s::jsonb, 
        true
    )
    WHERE user_id = %s AND search_query = %s;
    """
    cur.execute(query, (json.dumps(new_entry), user_id, search_query))
    conn.commit()
    print(f"Chat log updated for user '{user_id}' and query '{search_query}'.")


def graph_exists(graph_name):
    #cur.execute(f"SELECT name FROM ag_graph WHERE name = '{graph_name}';")
    #return cur.fetchone() is not None
    """
    cur.execute(f"SELECT name FROM ag_catalog.ag_graph WHERE name = '{graph_name}';")
    db_exists = cur.fetchone() is not None
    print(f"Graph exists in database: {db_exists}")

    base_path = f"persist_dir\\{graph_name}"
    files_exist = all(
        os.path.exists(f"{base_path}_{suffix}")
        for suffix in ["vector_store", "docstore", "graph_store", "image__vector_store", "index_store"]
    )
    print(f"Graph files exist: {files_exist}")

    return db_exists and files_exist
    """
    patterns = [
        f"persist_dir\\{graph_name}_default__vector_store",
        f"persist_dir\\{graph_name}_docstore",
        f"persist_dir\\{graph_name}_graph_store",
        f"persist_dir\\{graph_name}_index_store"
    ]
    
    # Iterate through each pattern and check existence
    for pattern in patterns:
        cypher_query = f"""
        SELECT * FROM cypher('{graph_name}', $$
        MATCH (g:graph)
        WHERE g.name = '{pattern}'
        RETURN g
        $$) AS (g agtype);
        """
        try:
            cur.execute(cypher_query)
            result = cur.fetchone()
            if result:  # If any one graph variation exists, return True
                print(f"Graph '{pattern}' exists.")
                return True
        except Exception as e:
            print(f"Error while checking graph '{pattern}': {e}")
    
    # If no variations exist
    print(f"No graph variations found for base name: '{graph_name}'.")
    return False

def query_graph(graph_name, user_query):
    # Formulate the Cypher query based on user input
    cypher_query = f"""
    SELECT * FROM cypher('{graph_name}', $$
    MATCH (n) WHERE n.properties CONTAINS '{user_query}'
    RETURN n
    $$) AS (n agtype);
    """
    cur.execute(cypher_query)
    results = cur.fetchall()
    return results



# Call the function
#push_json_to_age(persist_dir)

# Close the connection
#cur.close()
#conn.close()

