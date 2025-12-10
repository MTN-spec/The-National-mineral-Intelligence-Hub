import sqlite3
import hashlib
import os

class AuthService:
    def __init__(self, db_name="users.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialize the users table if it doesn't exist."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                phone TEXT,
                is_subscribed INTEGER DEFAULT 0
            )
        ''')
        # Simple migration for existing DB
        try:
            c.execute('ALTER TABLE users ADD COLUMN is_subscribed INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass # Column likely exists
            
        conn.commit()
        conn.close()

    def _hash_password(self, password):
        """Simple SHA-256 hashing."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, email, password, name, phone):
        """Register a new user. Returns (success, message)."""
        password_hash = self._hash_password(password)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            # Check if admin (auto-subscribe admin)
            is_sub = 1 if email == "mhandutakunda@gmail.com" else 0
            
            c.execute('INSERT INTO users (email, password_hash, name, phone, is_subscribed) VALUES (?, ?, ?, ?, ?)',
                      (email, password_hash, name, phone, is_sub))
            conn.commit()
            return True, "User registered successfully!"
        except sqlite3.IntegrityError:
            return False, "Email already exists."
        except Exception as e:
            return False, f"Error: {e}"
        finally:
            conn.close()

    def login_user(self, email, password):
        """Login a user. Returns (user_data, message)."""
        password_hash = self._hash_password(password)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT id, email, name, phone, is_subscribed FROM users WHERE email = ? AND password_hash = ?',
                  (email, password_hash))
        user = c.fetchone()
        conn.close()
        
        if user:
            return {
                "id": user[0],
                "email": user[1],
                "name": user[2],
                "phone": user[3],
                "is_subscribed": bool(user[4])
            }, "Login successful"
        else:
            return None, "Invalid email or password"
            
    def set_subscription_status(self, user_email, status=True):
        """Update subscription status."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        val = 1 if status else 0
        c.execute('UPDATE users SET is_subscribed = ? WHERE email = ?', (val, user_email))
        conn.commit()
        conn.close()

    def seed_admin(self, email, password, name, phone):
        """Ensure the admin user exists."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        if not c.fetchone():
            self.register_user(email, password, name, phone)
            print(f"Seeded admin: {email}")
        conn.close()

    def get_all_users(self):
        """Fetch all users to populate peer list."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT id, name, phone FROM users')
        users = [{"id": row[0], "name": row[1], "phone": row[2]} for row in c.fetchall()]
        conn.close()
        return users
