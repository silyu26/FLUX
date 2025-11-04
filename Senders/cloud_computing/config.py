MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "test"

RECEIVER_URL = "http://127.0.0.1:5000/yolo/"  # Receiver B URL

# Database type: 'mysql', 'mongo', 'influx'
DB_TYPE = "mysql"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "root",
    "database": "cloud"
}

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "testdb"
MONGO_COLLECTION = "metadata"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "my-token"
INFLUX_ORG = "my-org"
INFLUX_BUCKET = "metadata"
