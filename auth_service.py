import sqlite3
import hashlib
import hmac
import os
import re

PBKDF2_ITERATIONS = 310_000


class AuthService:
    """
    Banking-Grade Authentication Service (MTN-SPEC Corporate Security Standard).
    - OWASP PBKDF2-HMAC-SHA256 password derivation (310,000 iterations + 16-byte random salt)
    - Constant-time digest verification via hmac.compare_digest
    - Parameterized SQL queries across all operations
    - Automatic transparent upgrade of legacy unsalted SHA-256 hashes upon verified login
    """

    def __init__(self, db_name: str = "users.db"):
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
        try:
            c.execute('ALTER TABLE users ADD COLUMN is_subscribed INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

    def _hash_password(self, password: str, salt: bytes = None) -> str:
        """Derive salted PBKDF2-HMAC-SHA256 password hash."""
        if salt is None:
            salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS
        )
        return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> tuple[bool, bool]:
        """
        Verify password in constant time.
        Returns (is_valid, needs_rehash).
        """
        if not stored_hash:
            return False, False

        if stored_hash.startswith("pbkdf2_sha256$"):
            try:
                _, iter_str, salt_hex, hash_hex = stored_hash.split("$", 3)
                iterations = int(iter_str)
                salt = bytes.fromhex(salt_hex)
                expected = bytes.fromhex(hash_hex)
                candidate = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt,
                    iterations
                )
                valid = hmac.compare_digest(candidate, expected)
                return valid, (valid and iterations < PBKDF2_ITERATIONS)
            except (ValueError, TypeError):
                return False, False

        # Legacy unsalted SHA-256 fallback with automatic upgrade flag
        legacy_candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
        valid = hmac.compare_digest(legacy_candidate, stored_hash)
        return valid, valid

    @staticmethod
    def _clean_email(email: str) -> str:
        return (email or "").strip().lower()

    def register_user(self, email: str, password: str, name: str, phone: str):
        """Register a new user. Returns (success, message)."""
        clean_mail = self._clean_email(email)
        if not clean_mail or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_mail):
            return False, "Please provide a valid email address."
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters."

        safe_name = (name or "").strip()[:120]
        safe_phone = (phone or "").strip()[:32]
        admin_email = self._clean_email(os.environ.get("NMIH_ADMIN_EMAIL", "mhandutakunda@gmail.com"))
        password_hash = self._hash_password(password)

        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            is_sub = 1 if clean_mail == admin_email else 0
            c.execute(
                'INSERT INTO users (email, password_hash, name, phone, is_subscribed) VALUES (?, ?, ?, ?, ?)',
                (clean_mail, password_hash, safe_name, safe_phone, is_sub)
            )
            conn.commit()
            return True, "User registered successfully!"
        except sqlite3.IntegrityError:
            return False, "Email already exists."
        except Exception:
            return False, "Unable to complete registration."
        finally:
            conn.close()

    def login_user(self, email: str, password: str):
        """Authenticate a user in constant time. Returns (user_data, message)."""
        clean_mail = self._clean_email(email)
        if not clean_mail or not password:
            return None, "Invalid email or password"

        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            'SELECT id, email, password_hash, name, phone, is_subscribed FROM users WHERE LOWER(email) = ?',
            (clean_mail,)
        )
        row = c.fetchone()
        if not row:
            conn.close()
            # Perform dummy PBKDF2 work to equalize response timing against user enumeration
            self._hash_password(password)
            return None, "Invalid email or password"

        is_valid, needs_rehash = self._verify_password(password, row[2])
        if not is_valid:
            conn.close()
            return None, "Invalid email or password"

        if needs_rehash:
            upgraded_hash = self._hash_password(password)
            c.execute('UPDATE users SET password_hash = ? WHERE id = ?', (upgraded_hash, row[0]))
            conn.commit()

        conn.close()
        return {
            "id": row[0],
            "email": row[1],
            "name": row[3],
            "phone": row[4],
            "is_subscribed": bool(row[5])
        }, "Login successful"

    def set_subscription_status(self, user_email: str, status: bool = True):
        """Update subscription status."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        val = 1 if status else 0
        c.execute('UPDATE users SET is_subscribed = ? WHERE LOWER(email) = ?', (val, self._clean_email(user_email)))
        conn.commit()
        conn.close()

    def delete_user(self, email: str) -> bool:
        """Delete a user by email."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE LOWER(email) = ?', (self._clean_email(email),))
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        return deleted_count > 0

    def seed_admin(self, email: str, password: str, name: str, phone: str):
        """Ensure the admin user exists only when credentials are supplied securely."""
        if not email or not password:
            return
        clean_mail = self._clean_email(email)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE LOWER(email) = ?', (clean_mail,))
        exists = c.fetchone()
        conn.close()
        if not exists:
            self.register_user(clean_mail, password, name, phone)

    def get_all_users(self):
        """Fetch public peer directory."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT id, name, phone FROM users')
        users = [{"id": row[0], "name": row[1], "phone": row[2]} for row in c.fetchall()]
        conn.close()
        return users

    def get_all_users_details(self):
        """Fetch user metadata (never exposes password hashes)."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT id, email, name, phone, is_subscribed FROM users')
        users = [{
            "id": row[0],
            "email": row[1],
            "name": row[2],
            "phone": row[3],
            "is_subscribed": bool(row[4])
        } for row in c.fetchall()]
        conn.close()
        return users
