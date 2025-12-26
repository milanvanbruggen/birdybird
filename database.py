import sqlite3
import json
from datetime import datetime

DB_NAME = "birdybird.db"

def init_db():
    """Initialize the database with the detections table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species TEXT,
            confidence REAL,
            image_path TEXT,
            timestamp DATETIME,
            interesting_fact TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_detection(species, confidence, image_path, interesting_fact):
    """Add a new bird detection to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO detections (species, confidence, image_path, timestamp, interesting_fact)
        VALUES (?, ?, ?, ?, ?)
    ''', (species, confidence, image_path, datetime.now(), interesting_fact))
    conn.commit()
    return c.lastrowid
    conn.close()

def get_recent_detections(limit=10):
    """Get the most recent detections."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT * FROM detections ORDER BY timestamp DESC LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_all_detections():
    """Delete all detections from the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM detections')
    conn.commit()
    conn.close()

def update_detection(id, species, interesting_fact, confidence):
    """Update a detection's species, fact, and confidence."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE detections 
        SET species = ?, interesting_fact = ?, confidence = ?
        WHERE id = ?
    ''', (species, interesting_fact, confidence, id))
    conn.commit()
    rows_affected = c.rowcount
    conn.close()
    return rows_affected > 0

def delete_detection(id):
    """Delete a specific detection."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM detections WHERE id = ?', (id,))
    conn.commit()
    rows_affected = c.rowcount
    conn.close()
    return rows_affected > 0

def clear_all_detections():
    """Delete all detections from the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM detections')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
