import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    database_url = "postgresql+asyncpg://kyra_admin:Kyr4TechStack1!@kyra-test-db.chcwc66ku5f6.eu-west-1.rds.amazonaws.com:5432/kyra_test"
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Change date_of_birth from DATE to VARCHAR
            await conn.execute(text("ALTER TABLE users ALTER COLUMN date_of_birth TYPE VARCHAR(50);"))
            print("✅ Fixed date_of_birth column type")
            
            # Check the table structure
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """))
            
            columns = [(row[0], row[1]) for row in result.fetchall()]
            print("📋 Users table structure:")
            for col_name, data_type in columns:
                print(f"  {col_name}: {data_type}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 