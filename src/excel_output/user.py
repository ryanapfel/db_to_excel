import pandas as pd
import sqlite3 as sql
import xlsxwriter
import hashlib
import os
import random
import string

class User:
    def __init__(self, dbpath):
        self.path = dbpath

    def get_users(self):
        with sql.connect(self.path) as con:
            query = "SELECT * FROM ZUSER"
            dfh = pd.read_sql(query, con)
        return dfh

    def generate_password(self, length=8):
        """Generate a secure password if none is provided."""
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for i in range(length))
        return password

    def hash_password(self, password):
        """Hash the password using SHA-256."""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password

    def insert_user(self, email, password=None):
        """Insert a new user into the database."""
        if not password:
            password = self.generate_password()
        
        hashed_password = self.hash_password(password)
        
        with sql.connect(self.path) as con:
            cursor = con.cursor()
            cursor.execute("""
                INSERT INTO ZUSER (ZNAME, ZEMAIL, ZPASSWORD, ZPASSWORDHASH, ZUPLOADDICOM)
                VALUES (?, ?, ?, ?, ?)
            """, (email, email, password, hashed_password, 1))
            con.commit()
        
        print(f"User {email} inserted with password: {password}")


        return email, password

    def find_user_by_email(self, email):
        """Find a user by email and return their information."""
        with sql.connect(self.path) as con:
            query = "SELECT * FROM ZUSER WHERE ZEMAIL = ?"
            df = pd.read_sql(query, con, params=(email,))
        return df
    

    def user_exists(self, email):
        """Check if a user exists by email."""
        with sql.connect(self.path) as con:
            query = "SELECT COUNT(*) FROM ZUSER WHERE ZEMAIL = ?"
            cursor = con.cursor()
            cursor.execute(query, (email,))
            count = cursor.fetchone()[0]
        return count > 0

    def delete_user(self, email):
        """Delete a user by email."""
        with sql.connect(self.path) as con:
            cursor = con.cursor()
            cursor.execute("DELETE FROM ZUSER WHERE ZEMAIL = ?", (email,))
            con.commit()
