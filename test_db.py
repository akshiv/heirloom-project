import mysql.connector
from mysql.connector import pooling
import time
import os

dbconfig = {
    "pool_name": "mypool",
    "pool_size": 5,
    "host": "localhost",  # Update with LoadBalancer IP
    "user": "root",
    "password": "your-root-password",
    "database": "dev_db"
}

def get_connection():
    return mysql.connector.connect(pool_name="mypool")

def main():
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**dbconfig)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT, name VARCHAR(50))")
    cursor.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
    conn.commit()

    print("Initial data:", read_data(cursor))

    print("Disabling primary...")
    os.system("kubectl delete pod mysql-primary-0")

    # Try immediate operations
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users VALUES (3, 'Charlie')")
    conn.commit()

    print("Final data:", read_data(cursor))

if __name__ == "__main__":
    main()