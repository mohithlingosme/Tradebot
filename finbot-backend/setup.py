from setuptools import setup, find_packages

setup(
    name="finbot-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pandas",
        "numpy",
        "scikit-learn",
        "sqlalchemy",
        "psutil",
        "pytest",
        "pytest-asyncio",
        "yfinance",
        "alpha-vantage",
        "websockets",
        "asyncio",
        "aiohttp",
        "httpx",
    ],
)
