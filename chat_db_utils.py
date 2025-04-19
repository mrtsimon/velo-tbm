import sqlite3
from datetime import datetime

def get_db_connection(db_path='chat_history.db'):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path='chat_history.db'):
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_at TEXT,
        updated_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT,
        content TEXT,
        timestamp TEXT,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id)
    )''')
    conn.commit()
    conn.close()

def create_conversation(title=None, db_path='chat_history.db'):
    conn = get_db_connection(db_path)
    now = datetime.now().isoformat(timespec='seconds')
    if not title:
        title = f"Conversation {now[:10]}"
    c = conn.cursor()
    c.execute('INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)', (title, now, now))
    conv_id = c.lastrowid
    conn.commit()
    conn.close()
    return conv_id

def list_conversations(db_path='chat_history.db'):
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute('SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def get_messages(conversation_id, db_path='chat_history.db'):
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute('SELECT role, content, timestamp FROM messages WHERE conversation_id=? ORDER BY id ASC', (conversation_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_message(conversation_id, role, content, db_path='chat_history.db'):
    conn = get_db_connection(db_path)
    now = datetime.now().isoformat(timespec='seconds')
    c = conn.cursor()
    c.execute('INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)', (conversation_id, role, content, now))
    c.execute('UPDATE conversations SET updated_at=? WHERE id=?', (now, conversation_id))
    conn.commit()
    conn.close()
