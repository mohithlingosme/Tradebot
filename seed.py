from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from passlib.context import CryptContext

# 1. Connect to Database
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finbot_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# 2. Setup Password Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_pw = pwd_context.hash("admin123") # <--- THIS IS YOUR PASSWORD

# 3. Create the User
print("Checking for existing user...")
existing_user = db.query(User).filter(User.email == "admin@finbot.com").first()

if not existing_user:
    new_user = User(
        email="admin@finbot.com",
        hashed_password=hashed_pw,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    print("? SUCCESS: User created!")
    print("   Email:    admin@finbot.com")
    print("   Password: admin123")
else:
    print("??  User 'admin@finbot.com' already exists.")

db.close()
