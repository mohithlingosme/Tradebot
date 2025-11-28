from setuptools import setup, find_packages

setup(
    name="market-data-backend",
    version="0.1.0",
    python_requires=">=3.11.9,<3.12",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "websockets==12.0",
        "python-multipart==0.0.6",
        "pydantic==2.5.0",
        "sqlmodel==0.0.14",
        "alembic==1.13.1",
        "python-dotenv==1.0.0",
        "pandas",
        "numpy",
        "scikit-learn",
        "sqlalchemy",
        "psutil",
        "pytest",
        "pytest-asyncio",
        "yfinance",
        "alpha-vantage",
        "aiohttp",
        "httpx",
    ],
    entry_points={
        "console_scripts": [
            "market-data-backend=app.main:app",
        ],
    },
)
