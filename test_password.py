from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The stored hash from the database
stored_hash = '$2b$12$vUZhKd7XA3ju/ZzR.INVRudHl.vSlyeGWKPgmsqAtKdxFNDd7cn.C'

# Test the password
password = 'adminpass'
is_valid = pwd_context.verify(password, stored_hash)
print(f"Password 'adminpass' valid: {is_valid}")

# Test other possible passwords
test_passwords = ['adminpass', 'admin', 'password', '123456']
for pwd in test_passwords:
    valid = pwd_context.verify(pwd, stored_hash)
    print(f"Password '{pwd}' valid: {valid}")
