#!/usr/bin/env python3
"""
Script to make a test account an admin for the Kyra analytics dashboard.
This script updates the user's is_admin field in the database.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.models import SessionLocal, User
from sqlalchemy import select, update

async def make_user_admin(email: str) -> bool:
    """
    Make a user an admin by setting is_admin = True
    
    Args:
        email (str): Email of the user to make admin
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        async with SessionLocal() as db:
            # First, check if user exists
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with email '{email}' not found!")
                return False
            
            # Check if user is already admin
            if user.is_admin:
                print(f"✅ User '{email}' is already an admin!")
                return True
            
            # Update user to admin
            await db.execute(
                update(User)
                .where(User.email == email)
                .values(is_admin=True)
            )
            await db.commit()
            
            print(f"✅ Successfully made user '{email}' an admin!")
            return True
            
    except Exception as e:
        print(f"❌ Error making user admin: {e}")
        return False

async def list_all_users():
    """List all users with their admin status"""
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(User.email, User.is_admin, User.created_at)
                .order_by(User.created_at.desc())
            )
            users = result.all()
            
            if not users:
                print("❌ No users found in database")
                return
            
            print("\n📋 All Users:")
            print("-" * 60)
            print(f"{'Email':<30} {'Admin':<8} {'Created':<20}")
            print("-" * 60)
            
            for email, is_admin, created_at in users:
                admin_status = "✅ Yes" if is_admin else "❌ No"
                print(f"{email:<30} {admin_status:<8} {created_at.strftime('%Y-%m-%d %H:%M')}")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")

async def main():
    """Main function"""
    print("🚀 Kyra Admin Management Script")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python make_admin.py <email>     - Make user admin")
        print("  python make_admin.py --list      - List all users")
        print("  python make_admin.py --help      - Show this help")
        return
    
    command = sys.argv[1]
    
    if command == "--help" or command == "-h":
        print("\nCommands:")
        print("  <email>     - Make the specified user an admin")
        print("  --list      - List all users and their admin status")
        print("  --help      - Show this help message")
        print("\nExamples:")
        print("  python make_admin.py test@example.com")
        print("  python make_admin.py --list")
        return
    
    elif command == "--list":
        await list_all_users()
        return
    
    else:
        # Assume it's an email
        email = command
        
        if not "@" in email:
            print("❌ Please provide a valid email address")
            return
        
        print(f"🔧 Making user '{email}' an admin...")
        success = await make_user_admin(email)
        
        if success:
            print("\n✅ User is now an admin!")
            print("   They can now access the analytics dashboard at:")
            print("   - Local: http://localhost:8501")
            print("   - Production: https://kyrahealth.ai (if configured)")
        else:
            print("\n❌ Failed to make user admin. Check the error above.")

if __name__ == "__main__":
    asyncio.run(main())
