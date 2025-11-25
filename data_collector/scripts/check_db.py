import aiosqlite
import asyncio

async def check_db():
    async with aiosqlite.connect('market_data.db') as conn:
        cursor = await conn.execute('SELECT COUNT(*) FROM candles')
        count = await cursor.fetchone()
        print(f'Total candles in DB: {count[0]}')

        cursor = await conn.execute('SELECT symbol, ts_utc, open, high, low, close, volume, provider FROM candles LIMIT 5')
        rows = await cursor.fetchall()
        print('Sample candles:')
        for row in rows:
            print(row)

asyncio.run(check_db())
