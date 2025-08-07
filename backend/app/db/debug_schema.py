import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    database_url = "postgresql+asyncpg://kyra_admin:Kyr4TechStack1!@kyra-test-db.chcwc66ku5f6.eu-west-1.rds.amazonaws.com:5432/kyra_test"
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Check current database
            result = await conn.execute(text("SELECT current_database();"))
            db_name = result.scalar()
            print(f"Current database: {db_name}")
            
            # Check current schema
            result = await conn.execute(text("SELECT current_schema();"))
            schema = result.scalar()
            print(f"Current schema: {schema}")
            
            # List all schemas
            result = await conn.execute(text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;"))
            schemas = [row[0] for row in result.fetchall()]
            print(f"All schemas: {schemas}")
            
            # Check tables in public schema
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables in public schema: {tables}")
            
            # Check tables in all schemas
            result = await conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog') ORDER BY table_schema, table_name;"))
            all_tables = [(row[0], row[1]) for row in result.fetchall()]
            print(f"All tables (excluding system schemas): {all_tables}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 