#!/usr/bin/env python3
import mysql.connector
import time
import threading
import random
import string
from datetime import datetime
import argparse


class MySQLTester:
    def __init__(self, host, user='root', password='password'):
        self.db_params = {
            'host': host,
            'port': 3306,
            'user': user,
            'password': password,
        }
        self.stop_threads = False
        self.write_count = 0
        self.read_count = 0
        self.errors = []

    def setup_database(self):
        """Create test table in existing database"""
        conn = mysql.connector.connect(**self.db_params, database='dev_db')
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data VARCHAR(255),
                timestamp DATETIME,
                writer_id VARCHAR(50)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def writer_thread(self, writer_id):
        """Write records to database"""
        while not self.stop_threads:
            try:
                conn = mysql.connector.connect(
                    **self.db_params,
                    database='dev_db',
                    connect_timeout=10
                )
                cursor = conn.cursor()

                data = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
                timestamp = datetime.now()

                cursor.execute("""
                    INSERT INTO test_records (data, timestamp, writer_id)
                    VALUES (%s, %s, %s)
                """, (data, timestamp, writer_id))

                conn.commit()
                self.write_count += 1

                cursor.close()
                conn.close()

                time.sleep(0.1)

            except Exception as e:
                self.errors.append(f"Writer {writer_id} error: {str(e)}")
                time.sleep(1)

    def reader_thread(self, reader_id):
        """Read records from database"""
        while not self.stop_threads:
            try:
                conn = mysql.connector.connect(
                    **self.db_params,
                    database='dev_db',
                    connect_timeout=10
                )
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM test_records
                    ORDER BY id DESC LIMIT 10
                """)
                records = cursor.fetchall()

                if records:
                    self.read_count += 1

                cursor.close()
                conn.close()

                time.sleep(0.2)

            except Exception as e:
                self.errors.append(f"Reader {reader_id} error: {str(e)}")
                time.sleep(1)

    def monitor_thread(self):
        """Monitor and display statistics"""
        start_time = time.time()
        last_write_count = 0
        last_read_count = 0

        while not self.stop_threads:
            time.sleep(2)
            current_time = time.time()
            elapsed = current_time - start_time

            writes_per_sec = (self.write_count - last_write_count) / 2
            reads_per_sec = (self.read_count - last_read_count) / 2

            print(f"\nElapsed: {elapsed:.1f}s")
            print(f"Writes/sec: {writes_per_sec:.1f}")
            print(f"Reads/sec: {reads_per_sec:.1f}")
            print(f"Total writes: {self.write_count}")
            print(f"Total reads: {self.read_count}")

            if self.errors:
                print("\nRecent errors:")
                for error in self.errors[-3:]:
                    print(error)

            last_write_count = self.write_count
            last_read_count = self.read_count

    def run_test(self, duration_seconds=300):
        """Run the complete test"""
        try:
            self.setup_database()
        except Exception as e:
            print(f"Failed to setup database: {e}")
            return

        threads = []

        # Start writer threads
        for i in range(3):
            t = threading.Thread(target=self.writer_thread, args=(f"writer_{i}",))
            threads.append(t)
            t.start()

        # Start reader threads
        for i in range(3):
            t = threading.Thread(target=self.reader_thread, args=(f"reader_{i}",))
            threads.append(t)
            t.start()

        # Start monitor thread
        monitor = threading.Thread(target=self.monitor_thread)
        monitor.start()
        threads.append(monitor)

        try:
            time.sleep(duration_seconds)
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        finally:
            self.stop_threads = True
            for t in threads:
                t.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test MySQL HA setup')
    parser.add_argument('--host', default='mysql-mysql', help='MySQL host')
    parser.add_argument('--password', default='password', help='MySQL root password')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds')
    args = parser.parse_args()

    tester = MySQLTester(
        host=args.host,
        password=args.password
    )
    tester.run_test(args.duration)
