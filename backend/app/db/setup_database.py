import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    database_url = "postgresql+asyncpg://kyra_admin:Kyr4TechStack1!@kyra-test-db.chcwc66ku5f6.eu-west-1.rds.amazonaws.com:5432/kyra_test"
    engine = create_async_engine(database_url)
    
    # SQL to create the main tables
    create_tables_sql = """
    -- Create users table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_pw VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        full_name VARCHAR(255),
        date_of_birth DATE,
        gender VARCHAR(50),
        sex VARCHAR(50),
        country VARCHAR(100),
        address TEXT,
        ethnic_group VARCHAR(100),
        long_term_conditions TEXT,
        medications TEXT,
        consent_to_data_storage BOOLEAN DEFAULT FALSE,
        is_admin BOOLEAN DEFAULT FALSE
    );

    -- Create messages table
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255),
        user_id INTEGER REFERENCES users(id),
        content TEXT NOT NULL,
        role VARCHAR(50) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        category VARCHAR(100),
        sources TEXT,
        confidence_score FLOAT,
        user_question TEXT
    );

    -- Create unanswered_queries table
    CREATE TABLE IF NOT EXISTS unanswered_queries (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255),
        query TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        category VARCHAR(100),
        sources TEXT,
        reason TEXT,
        score FLOAT
    );
    """
    
    try:
        async with engine.begin() as conn:
            # Split and execute each statement
            statements = create_tables_sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    await conn.execute(text(statement))
            print("✅ Database tables created successfully!")
            
            # Check what tables exist now
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
            tables = [row[0] for row in result.fetchall()]
            print("📋 Tables in database:", tables)
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 