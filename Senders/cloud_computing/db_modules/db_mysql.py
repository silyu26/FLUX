import mysql.connector

def init_db(config):
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id INT AUTO_INCREMENT PRIMARY KEY,
            gen_at VARCHAR(64),
            req_id INT,
            fps INT,
            expId VARCHAR(64),
            image_name VARCHAR(255)
        )
    """)
    conn.commit()
    cursor.close()
    return conn

def save_metadata(conn, data):
    cursor = conn.cursor()
    sql = "INSERT INTO metadata (gen_at, req_id, fps, expId, image_name) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (data["gen_at"], data["req_id"], data["fps"], data["expId"], data["image_name"]))
    conn.commit()
    cursor.close()
