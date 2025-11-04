from influxdb_client import InfluxDBClient, Point, WritePrecision

def init_db(url, token, org, bucket):
    client = InfluxDBClient(url=url, token=token, org=org)
    return client.write_api(write_options=None), bucket, org

def save_metadata(write_api, bucket, org, data):
    point = (
        Point("metadata")
        .tag("expId", data["expId"])
        .field("fps", data["fps"])
        .field("req_id", data["req_id"])
        .field("image_name", data["image_name"])
        .time(data["gen_at"], WritePrecision.NS)
    )
    write_api.write(bucket=bucket, org=org, record=point)
