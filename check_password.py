from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The stored hash from the database
stored_hash = '$2b$12$ihYwNxVx33nHBNhJ.AspQuuk/JQq.PqxhU1pwlI8upc4WDXj1RLli'

# Test the password
password = 'adminpass'
is_valid = pwd_context.verify(password, stored_hash)
print(f"Password 'adminpass' valid: {is_valid}")

# Generate a new hash for 'adminpass'
new_hash = pwd_context.hash('adminpass')
print(f"New hash for 'adminpass': {new_hash}")

# Check if the new hash matches the stored one
print(f"New hash matches stored: {new_hash == stored_hash}")
