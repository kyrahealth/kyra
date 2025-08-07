import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    database_url = "postgresql+asyncpg://kyra_admin:Kyr4TechStack1!@kyra-test-db.chcwc66ku5f6.eu-west-1.rds.amazonaws.com:5432/kyra_test"
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
            tables = [row[0] for row in result.fetchall()]
            print("Tables in database:", tables)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 