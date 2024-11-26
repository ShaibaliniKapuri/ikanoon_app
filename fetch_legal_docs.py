import sys
sys.path.append("ikapi.py")  # Path to where the script is located
from ikapi import IKApi
from argparse import Namespace
import re
import shutil
import os

api_token = "xxxx"#ikanoon api key

args = Namespace(
    token=api_token,
    maxcites=5,
    maxcitedby=5,
    orig=False,
    maxpages=1,
    pathbysrc=False,
    datadir="/content"
)

storage = None  # Depending on your requirement
ik_api = IKApi(args, storage)


#------------------------------------------------------------------------------------------------------------

# Function for fetching legal docs based on doc_id 
# Not using this function in original Application
def fetch_legal_docs():
    doc_id = 18837715  # Replace with the actual document ID you want to fetch
    try:
        fetched_data = ik_api.fetch_doc(doc_id)

        # Write the fetched data to a file
        with open("content\legal.txt", "w", encoding="utf-8") as f:
            f.write(fetched_data.decode('utf-8'))  # Convert bytes to string before writing
        print("Data has been successfully written to legal.txt")

    except Exception as e:
        print(f"An error occurred: {e}")


#-----------------------------------------------------------------------------------------------------------


#Function performing keyword search using ik_api
#writing the search contents in a text file inside a source directory

def perform_search(query):
    try:
        pagenum = 1  # Example page number
        maxpages = args.maxpages
        search_results = ik_api.search(query, pagenum, maxpages)
        source_dir = "content"
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)
        # Sanitize the search query to create a safe filename
        sanitized_query = re.sub(r'[^a-zA-Z0-9]', '_', query)
        filename = f"{source_dir}/{sanitized_query}_search_results.txt"
        # Write the search results to a file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(search_results.decode('utf-8'))  # Convert bytes to string before writing
        print("Search results have been successfully written to ",filename)

    except Exception as e:
        print(f"An error occurred during search: {e}")


#--------------------------------------------------------------------------------------------------------------------


#moving the files containing searched items in another directory after finishing the session with user

def move_files_to_completed():
    source_dir = "content"
    target_dir = "completed"
    
    # Ensure the target directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Move each file in the source directory to the target directory
    for filename in os.listdir(source_dir):
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        # Only move files, not directories
        if os.path.isfile(source_path):
            shutil.move(source_path, target_path)
            print(f"Moved {filename} to {target_dir}")

    print("All files have been moved to the 'completed' directory.")
