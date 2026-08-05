"""Database setup utility script"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.seed import seed_database, clear_database


def print_usage():
    """Print usage instructions"""
    print("\n📚 SmartReco Database Setup Utility\n")
    print("Usage:")
    print("  python scripts/setup_db.py seed    - Seed database with initial data")
    print("  python scripts/setup_db.py clear   - Clear all data from database")
    print("  python scripts/setup_db.py reset   - Clear and reseed database")
    print("\nBefore running, ensure:")
    print("  1. PostgreSQL is running")
    print("  2. Database URL is configured in .env")
    print("  3. Run 'alembic upgrade head' to create tables\n")


async def reset_database():
    """Clear and reseed the database"""
    print("🔄 Resetting database...\n")
    await clear_database()
    print()
    await seed_database()


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "seed":
        print("🌱 Seeding database...\n")
        await seed_database()
    elif command == "clear":
        print("⚠️  Clearing database...\n")
        response = input("Are you sure you want to clear all data? (yes/no): ")
        if response.lower() == "yes":
            await clear_database()
        else:
            print("❌ Operation cancelled")
    elif command == "reset":
        print("🔄 Resetting database...\n")
        response = input("Are you sure you want to reset all data? (yes/no): ")
        if response.lower() == "yes":
            await reset_database()
        else:
            print("❌ Operation cancelled")
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    asyncio.run(main())
