import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

# FastAPI & Network
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# Database
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# Security
from passlib.context import CryptContext
from jose import JWTError, jwt

# Trading
from alpaca_trade_api.rest import REST

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
load_dotenv()

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finbot_db"
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL")
if ALPACA_BASE_URL and ALPACA_BASE_URL.endswith("/v2"):
    ALPACA_BASE_URL = ALPACA_BASE_URL[:-3]

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

# ==============================================================================
# 2. SETUP
# ==============================================================================
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Connect to Alpaca
alpaca = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ==============================================================================
# 3. MODELS & SCHEMAS
# ==============================================================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    side = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str

class TradeRequest(BaseModel):
    symbol: str
    qty: float
    side: str

# ==============================================================================
# 4. HELPERS
# ==============================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = db.query(User).filter(User.email == email).first()
    if user is None: raise HTTPException(status_code=401)
    return user

# ==============================================================================
# 5. APP ENDPOINTS
# ==============================================================================
app = FastAPI(title="Finbot Pro (Live Trading)", version="2.0.0")

# --- CORS FIX IS HERE ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8501"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # Allow specific origins
    allow_credentials=True,        # Allow cookies/auth headers
    allow_methods=["*"],           # Allow all methods (GET, POST, etc)
    allow_headers=["*"],           # Allow all headers
)
# ------------------------

@app.get("/")
def home():
    return {"status": "online", "mode": "Pro Trading Mode"}

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- TRADING ENDPOINTS ---

@app.get("/portfolio")
def get_portfolio(current_user: User = Depends(get_current_user)):
    """See your Money & Positions"""
    acct = alpaca.get_account()
    return {
        "cash": float(acct.cash),
        "equity": float(acct.equity),
        "buying_power": float(acct.buying_power)
    }

@app.get("/price/{symbol}")
def get_price(symbol: str, current_user: User = Depends(get_current_user)):
    """Check live price"""
    bar = alpaca.get_latest_bar(symbol.upper())
    return {"symbol": symbol, "price": bar.c, "time": str(bar.t)}

@app.post("/trades")
def place_trade(trade: TradeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Buy or Sell Stock"""
    # 1. Execute on Alpaca
    try:
        order = alpaca.submit_order(
            symbol=trade.symbol.upper(),
            qty=trade.qty,
            side=trade.side.lower(),
            type='market',
            time_in_force='gtc'
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Save to Database
    new_trade = Trade(
        symbol=trade.symbol.upper(),
        side=trade.side.lower(),
        quantity=trade.qty,
        price=0.0, # Market price isn't known until fill
        status="submitted"
    )
    db.add(new_trade)
    db.commit()
    
    return {"status": "success", "order_id": str(order.id), "symbol": trade.symbol}
