import sqlite3

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

def create_tables():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                chat_id INTEGER, 
                username TEXT, 
                name TEXT, 
                age INTEGER, 
                description TEXT, 
                gender TEXT, 
                seeking_gender TEXT, 
                photo BLOB, 
                current_profile_id INTEGER, 
                next_profile_index INTEGER)''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS likes_queue
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    liked_user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (liked_user_id) REFERENCES users(id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS admins
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    level INTEGER,
                    joined_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS likes
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    liked_user_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (liked_user_id) REFERENCES users(id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS mutual_likes
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user1_id) REFERENCES users(id),
                    FOREIGN KEY (user2_id) REFERENCES users(id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS dislikes
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    disliked_user_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (disliked_user_id) REFERENCES users(id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS inactive_users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS reports
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_username TEXT,
                    reporter_user_id INTEGER,
                    reported_username TEXT,
                    reported_user_id INTEGER,
                    reason TEXT,
                    report_text TEXT,
                    resolved INTEGER DEFAULT 0,
                    resolved_by INTEGER,
                    FOREIGN KEY (resolved_by) REFERENCES admins(user_id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS blocked_users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS frozen_users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    freeze_until DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()

create_tables()
