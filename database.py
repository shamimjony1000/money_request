import sqlite3
from datetime import datetime
import os
import time

class Database:
    def __init__(self, db_name="requests.db"):
        self.db_name = db_name
        self.max_retries = 3
        self.retry_delay = 1  
        self.initialize_database()
    
    def initialize_database(self):
        for attempt in range(self.max_retries):
            try:
                
                self.conn = sqlite3.connect(self.db_name)
                
                self.conn.execute('PRAGMA encoding="UTF-8"')
                
                
                cursor = self.conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='requests'")
                if not cursor.fetchone():
                    self.create_table()
                else:
                    # Verify columns
                    cursor.execute('PRAGMA table_info(requests)')
                    columns = [col[1] for col in cursor.fetchall()]
                    required_columns = ['id', 'timestamp', 'project_number', 'project_name', 'amount', 'reason', 'original_text']
                    
                    if not all(col in columns for col in required_columns):
                        # Backup existing data
                        cursor.execute('ALTER TABLE requests RENAME TO requests_old')
                        self.create_table()
                        # Copy data from old table
                        cursor.execute('''
                            INSERT INTO requests (timestamp, project_number, project_name, amount, reason)
                            SELECT timestamp, project_number, project_name, amount, reason
                            FROM requests_old
                        ''')
                        cursor.execute('DROP TABLE requests_old')
                        self.conn.commit()
                
                return  # Success
            except sqlite3.OperationalError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"Could not initialize database after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Database initialization error: {str(e)}")
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                project_number TEXT,
                project_name TEXT,
                amount REAL,
                reason TEXT,
                original_text TEXT
            )
        ''')
        self.conn.commit()
    
    def add_request(self, project_number, project_name, amount, reason, original_text=""):
        for attempt in range(self.max_retries):
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO requests (timestamp, project_number, project_name, amount, reason, original_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (datetime.now(), project_number, project_name, amount, reason, original_text))
                self.conn.commit()
                return  # Success
            except sqlite3.OperationalError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"Could not add request after {self.max_retries} attempts: {str(e)}")
    
    def get_all_requests(self):
        for attempt in range(self.max_retries):
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT * FROM requests ORDER BY timestamp DESC')
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                return [dict(zip(columns, row)) for row in results]
            except sqlite3.OperationalError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"Could not fetch requests after {self.max_retries} attempts: {str(e)}")
    
    def __del__(self):
        try:
            self.conn.close()
        except:
            pass