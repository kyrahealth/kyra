import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    database_url = "postgresql+asyncpg://kyra_admin:Kyr4TechStack1!@kyra-test-db.chcwc66ku5f6.eu-west-1.rds.amazonaws.com:5432/kyra_test"
    engine = create_async_engine(database_url)
    
    # SQL to create all tables with correct structure
    create_tables_sql = """
    -- Drop existing tables if they exist
    DROP TABLE IF EXISTS messages CASCADE;
    DROP TABLE IF EXISTS unanswered_queries CASCADE;
    DROP TABLE IF EXISTS chat_sessions CASCADE;
    DROP TABLE IF EXISTS users CASCADE;
    
    -- Create users table
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_pw VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        full_name VARCHAR(255),
        date_of_birth VARCHAR(50),
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

    -- Create chat_sessions table
    CREATE TABLE chat_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        location VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create messages table
    CREATE TABLE messages (
        id SERIAL PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES chat_sessions(id),
        role VARCHAR(10) NOT NULL,
        content TEXT NOT NULL,
        confidence_score FLOAT,
        sources JSON,
        category VARCHAR(50),
        user_question TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create unanswered_queries table
    CREATE TABLE unanswered_queries (
        id SERIAL PRIMARY KEY,
        text TEXT NOT NULL,
        location VARCHAR(255),
        reason VARCHAR(255),
        score FLOAT,
        category VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        session_id INTEGER REFERENCES chat_sessions(id),
        sources JSON
    );
    
    -- Create indexes
    CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
    """
    
    try:
        async with engine.begin() as conn:
            # Split and execute each statement
            statements = create_tables_sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    await conn.execute(text(statement))
            print("✅ All database tables created successfully!")
            
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