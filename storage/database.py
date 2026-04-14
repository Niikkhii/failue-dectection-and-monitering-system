import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                tags TEXT
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_metric(self, name: str, value: float, tags: Optional[str] = None) -> int:
        """Insert a new metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO metrics (name, value, tags) VALUES (?, ?, ?)',
            (name, value, tags)
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def insert_alert(self, level: str, message: str) -> int:
        """Insert a new alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO alerts (level, message) VALUES (?, ?)',
            (level, message)
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def insert_event(self, event_type: str, data: Optional[str] = None) -> int:
        """Insert a new event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO events (event_type, data) VALUES (?, ?)',
            (event_type, data)
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM metrics ORDER BY timestamp DESC LIMIT ?', (limit,))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?', (limit,))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events ORDER BY timestamp DESC LIMIT ?', (limit,))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
