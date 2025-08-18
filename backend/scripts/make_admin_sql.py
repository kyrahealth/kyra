#!/usr/bin/env python3
"""
Simple SQL-based script to make a user admin.
This script uses raw SQL if there are issues with the ORM approach.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.models import SessionLocal

async def make_user_admin_sql(email: str) -> bool:
    """
    Make a user admin using raw SQL
    
    Args:
        email (str): Email of the user to make admin
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        async with SessionLocal() as db:
            # Check if user exists
            result = await db.execute(
                "SELECT id, email, is_admin FROM users WHERE email = :email",
                {"email": email}
            )
            user = result.fetchone()
            
            if not user:
                print(f"❌ User with email '{email}' not found!")
                return False
            
            user_id, user_email, is_admin = user
            
            # Check if user is already admin
            if is_admin:
                print(f"✅ User '{email}' is already an admin!")
                return True
            
            # Update user to admin
            await db.execute(
                "UPDATE users SET is_admin = TRUE WHERE email = :email",
                {"email": email}
            )
            await db.commit()
            
            print(f"✅ Successfully made user '{email}' an admin!")
            print(f"   User ID: {user_id}")
            return True
            
    except Exception as e:
        print(f"❌ Error making user admin: {e}")
        return False

async def list_users_sql():
    """List all users with their admin status using SQL"""
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                "SELECT email, is_admin, created_at FROM users ORDER BY created_at DESC"
            )
            users = result.fetchall()
            
            if not users:
                print("❌ No users found in database")
                return
            
            print("\n📋 All Users:")
            print("-" * 60)
            print(f"{'Email':<30} {'Admin':<8} {'Created':<20}")
            print("-" * 60)
            
            for email, is_admin, created_at in users:
                admin_status = "✅ Yes" if is_admin else "❌ No"
                created_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at else 'Unknown'
                print(f"{email:<30} {admin_status:<8} {created_str}")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")

async def main():
    """Main function"""
    print("🚀 Kyra Admin Management Script (SQL Version)")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python make_admin_sql.py <email>     - Make user admin")
        print("  python make_admin_sql.py --list      - List all users")
        print("  python make_admin_sql.py --help      - Show this help")
        return
    
    command = sys.argv[1]
    
    if command == "--help" or command == "-h":
        print("\nCommands:")
        print("  <email>     - Make the specified user an admin")
        print("  --list      - List all users and their admin status")
        print("  --help      - Show this help message")
        print("\nExamples:")
        print("  python make_admin_sql.py test@example.com")
        print("  python make_admin_sql.py --list")
        return
    
    elif command == "--list":
        await list_users_sql()
        return
    
    else:
        # Assume it's an email
        email = command
        
        if not "@" in email:
            print("❌ Please provide a valid email address")
            return
        
        print(f"🔧 Making user '{email}' an admin...")
        success = await make_user_admin_sql(email)
        
        if success:
            print("\n✅ User is now an admin!")
            print("   They can now access the analytics dashboard!")
        else:
            print("\n❌ Failed to make user admin. Check the error above.")

if __name__ == "__main__":
    asyncio.run(main())
