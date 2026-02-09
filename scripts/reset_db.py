#!/usr/bin/env python3
"""
Database Reset Script.

Usage: python scripts/reset_db.py

This will DROP ALL TABLES and recreate them.
USE WITH CAUTION.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.db.database import reset_db, DB_PATH


def main():
    print("=" * 50)
    print("DATABASE RESET SCRIPT")
    print("=" * 50)
    print(f"\nDatabase path: {DB_PATH}")
    print("\nWARNING: This will DELETE ALL DATA!")
    
    confirm = input("\nType 'RESET' to confirm: ")
    
    if confirm != "RESET":
        print("Cancelled.")
        return
    
    print("\nResetting database...")
    reset_db()
    print("Done! Database has been reset.")
    print(f"New database file: {DB_PATH}")


if __name__ == "__main__":
    main()
