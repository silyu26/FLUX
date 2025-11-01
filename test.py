#import torch
#print(torch.cuda.is_available())
#print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")

#print(torch.version.cuda)   # e.g. '12.1'
#print(torch.cuda.is_available())  # True


from minio import Minio
from minio.error import S3Error
from flask import Flask, request, redirect, url_for, render_template

# --- MinIO Connection Settings ---
MINIO_ENDPOINT = "localhost:9000"  # Note: Use the API port, NOT the console port 9001
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_SECURE = False  # Set to True if using HTTPS/SSL

# Initialize the MinIO Client
try:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )
except Exception as e:
    print(f"Error connecting to MinIO: {e}")
    minio_client = None

app = Flask(__name__)
# The bucket name where you want to store images
BUCKET_NAME = "test"
import os
from io import BytesIO

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return "No file part in the request.", 400
        
        file = request.files['file']
        
        # If the user submits an empty part
        if file.filename == '':
            return "No selected file.", 400

        if file and minio_client:
            try:
                # 1. Read the file into memory as a stream/BytesIO object
                file_data = file.read()
                file_size = len(file_data)
                file_stream = BytesIO(file_data)
                
                # Use a unique name for the object key (e.g., original name + UUID)
                # For simplicity here, we'll use the original filename
                object_name = file.filename
                
                # 2. Upload the file to MinIO using put_object
                minio_client.put_object(
                    BUCKET_NAME,
                    object_name,
                    file_stream,
                    file_size,
                    content_type=file.content_type
                )
                
                # Construct the URL to view the file (if you have the correct bucket policy)
                file_url = f"http://{MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"
                
                return f"File '{object_name}' successfully uploaded! URL: {file_url}"

            except S3Error as e:
                return f"MinIO Upload Error: {e}", 500
            except Exception as e:
                return f"An unexpected error occurred: {e}", 500
    
    # Simple HTML form for GET request
    return '''
    <!doctype html>
    <title>Upload Image to MinIO</title>
    <h1>Upload a File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == '__main__':
    # You'll need to run your Flask app on a different port than MinIO (9000/9001)
    app.run(debug=True, port=5000)