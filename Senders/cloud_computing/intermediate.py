from flask import Flask, request
import requests, os, io
from minio import Minio
from datetime import datetime
import config
import sys

# Choose DB module dynamically
if config.DB_TYPE == "mysql":
    from db_modules import db_mysql as db_module
    db = db_module.init_db(config.MYSQL_CONFIG)
elif config.DB_TYPE == "mongo":
    from db_modules import db_mongo as db_module
    db = db_module.init_db(config.MONGO_URI, config.MONGO_DB, config.MONGO_COLLECTION)
elif config.DB_TYPE == "influx":
    from db_modules import db_influx as db_module
    db = db_module.init_db(config.INFLUX_URL, config.INFLUX_TOKEN, config.INFLUX_ORG, config.INFLUX_BUCKET)
else:
    raise ValueError("Unsupported DB_TYPE in config.py")

# Setup MinIO client
minio_client = Minio(
    config.MINIO_ENDPOINT,
    access_key=config.MINIO_ACCESS_KEY,
    secret_key=config.MINIO_SECRET_KEY,
    secure=False,
)
if not minio_client.bucket_exists(config.MINIO_BUCKET):
    minio_client.make_bucket(config.MINIO_BUCKET)

app = Flask(__name__)
#uvicorn intermediate:app --reload --host 0.0.0.0 --port 5001

log_filename = f"intermediate.txt"
log_file = open(log_filename, "a", encoding="utf-8")
sys.stdout = log_file  # Redirect all print() output to file
sys.stderr = log_file

def log(msg):
    """Helper function to log messages with timestamp"""
    print(f"[{datetime.now().isoformat()}] {msg}")
    log_file.flush()

@app.route("/yolo/", methods=["POST"])
def receive_data():
    image_file = request.files.get("file")
    metadata = request.form.to_dict()
    log(f"Received: {metadata} at {datetime.now().isoformat()}")
    server_in  = datetime.now().isoformat()

    # Save image to MinIO
    image_name = f"{metadata.get('req_id', 'unknown')}_{datetime.now().timestamp()}.jpg"
    image_data = io.BytesIO(image_file.read())
    minio_client.put_object(config.MINIO_BUCKET, image_name, image_data, length=image_data.getbuffer().nbytes)
    minio_in = datetime.now().isoformat()
    log(f"Saved image to MinIO: {image_name} at {minio_in}")

    # Save metadata to DB
    metadata["image_name"] = image_name
    if config.DB_TYPE == "mysql":
        db_module.save_metadata(db, metadata)
    elif config.DB_TYPE == "mongo":
        db_module.save_metadata(db, metadata)
    elif config.DB_TYPE == "influx":
        write_api, bucket, org = db
        db_module.save_metadata(write_api, bucket, org, metadata)

    db_in = datetime.now().isoformat()
    log(f"Saved metadata to DB at {db_in}")

     # --- Retrieve image again from MinIO ---
    retrieved_obj = minio_client.get_object(config.MINIO_BUCKET, image_name)
    retrieved_bytes = retrieved_obj.read()
    retrieved_obj.close()
    retrieved_obj.release_conn()
    minio_out = datetime.now().isoformat()
    log(f"Retrieved image from MinIO: {image_name} at {datetime.now().isoformat()}")

    # --- Retrieve metadata again from DB ---
    if config.DB_TYPE == "mysql":
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM metadata WHERE image_name = %s", (image_name,))
        db_metadata = cursor.fetchone()
        cursor.close()
    elif config.DB_TYPE == "mongo":
        db_metadata = db_module.init_db(config.MONGO_URI, config.MONGO_DB, config.MONGO_COLLECTION).find_one({"image_name": image_name})
    elif config.DB_TYPE == "influx":
        # For InfluxDB, you’d typically re-query with the client API.
        # Here we just reuse the in-memory metadata for simplicity.
        db_metadata = metadata

    db_out = datetime.now().isoformat()
    log(f"Retrieved metadata from DB at {db_out}")

    if db_metadata is None:
        log("Warning: Metadata not found in DB; using in-memory version.")
        db_metadata = metadata

    # Forward data to receiver B
    files = {"file": (image_name, image_data.getvalue(), "image/jpeg")}
    metadata.update({
        "server_in": server_in,
        "minio_in": minio_in,
        "db_in": db_in,
        "minio_out": minio_out,
        "db_out": db_out,
        "server_out": datetime.now().isoformat()
    })
    try:
        response = requests.post(config.RECEIVER_URL, files=files, data=metadata)
        print(f"Forwarded to receiver: {response.status_code}")
    except Exception as e:
        print(f"Failed to forward to receiver: {e}")

    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
