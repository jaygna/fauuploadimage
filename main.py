import os
from flask import Flask, redirect, request, send_file
from google.cloud import datastore, storage
import time

# Initialize Google Cloud clients
datastore_client = datastore.Client()
storage_client = storage.Client()

# Initialize Flask app
app = Flask(__name__)

# Create 'files' directory if it doesn't exist
os.makedirs('files', exist_ok=True)

# Google Cloud Storage bucket name
BUCKET_NAME = 'fau-image-storage'

# Routes
@app.route('/')
def index():
    index_html = """
    <form method="post" enctype="multipart/form-data" action="/upload">
      <div>
        <label for="file">Choose file to upload</label>
        <input type="file" id="file" name="form_file" accept="image/jpeg"/>
      </div>
      <div>
        <button>Submit</button>
      </div>
    </form>
    """

    for file in list_files():
        index_html += "<li><a href='/files/" + file + "'>" + file + "</a></li>"

    return index_html


@app.route('/upload', methods=["POST"])
def upload():
    file = request.files['form_file']  # The file item name must match the form's input name
    if file:
        # Save to Google Cloud Storage
        file_name = file.filename
        save_to_gcs(file_name, file)

        # Add metadata to Google Cloud Datastore
        metadata = {
            "name": file_name,
            "url": f'https://storage.googleapis.com/{BUCKET_NAME}/{file_name}',
            "user": "rdeandrade",  # You can customize this based on the actual user
            'timestamp': int(time.time())
        }
        add_db_entry(metadata)

    return redirect("/")


@app.route('/files')
def list_files():
    # List files in Google Cloud Storage bucket
    return get_list_of_files(BUCKET_NAME)


@app.route('/files/<filename>')
def get_file(filename):
    # Serve file from Google Cloud Storage
    return send_file_from_gcs(BUCKET_NAME, filename)


### Google Cloud Storage functions ###
def get_list_of_files(bucket_name):
    """Lists all the blobs in the bucket."""
    print(f"Fetching file list from bucket: {bucket_name}")
    blobs = storage_client.list_blobs(bucket_name)
    return [blob.name for blob in blobs]


def save_to_gcs(file_name, file):
    """Upload file to Google Cloud Storage."""
    print(f"Uploading {file_name} to {BUCKET_NAME}")
    bucket = storage_client.bucket(bucket_name=BUCKET_NAME)
    blob = bucket.blob(file_name)
    blob.upload_from_file(file)
    print(f"File {file_name} uploaded successfully.")


def send_file_from_gcs(bucket_name, file_name):
    """Serve a file from Google Cloud Storage."""
    blob = storage_client.bucket(bucket_name).blob(file_name)
    return blob.public_url


### Google Cloud Datastore functions ###
def add_db_entry(metadata):
    """Add metadata to Google Cloud Datastore."""
    entity = datastore.Entity(key=datastore_client.key('photos'))
    entity.update(metadata)
    datastore_client.put(entity)


def fetch_db_entry(query_filters):
    """Fetch entries from Datastore based on query filters."""
    query = datastore_client.query(kind='photos')
    for attr, value in query_filters.items():
        query.add_filter(attr, '=', value)

    return list(query.fetch())


### Main execution ###
if __name__ == '__main__':
    app.run(debug=True, port=8080)
    

