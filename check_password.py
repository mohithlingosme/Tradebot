from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The stored hash from the database
stored_hash = os.getenv('STORED_HASH', '$2b$12$ihYwNxVx33nHBNhJ.AspQuuk/JQq.PqxhU1pwlI8upc4WDXj1RLli')

# Test the password (use environment variable or input)
import os
password = os.getenv('TEST_PASSWORD', 'default_test_password')  # Use env var or default
is_valid = pwd_context.verify(password, stored_hash)
print(f"Password '{password}' valid: {is_valid}")

# Generate a new hash for the password
new_hash = pwd_context.hash(password)
print(f"New hash for '{password}': {new_hash}")

# Check if the new hash matches the stored one
print(f"New hash matches stored: {new_hash == stored_hash}")
