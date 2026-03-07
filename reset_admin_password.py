# reset_admin_password.py
import os
import sys
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_admin_password():
    """Reset the admin password in the database"""
    
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Try common local database URLs
        DATABASE_URL = os.getenv("POSTGRESQL_URL")
        if not DATABASE_URL:
            DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/eukexpress"
    
    print(f"🔌 Connecting to database...")
    print(f"Database URL: {DATABASE_URL}")
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        
        # New password (same as .env)
        new_password = "EukExpress@2024Admin"
        hashed_password = pwd_context.hash(new_password)
        
        print(f"🔑 New password hash generated")
        
        # Update admin user
        with engine.connect() as conn:
            # First, check if admin exists
            result = conn.execute(
                text("SELECT id, username FROM admin WHERE username = 'admin'")
            )
            admin = result.first()
            
            if admin:
                print(f"✅ Found admin user: {admin.username}")
                
                # Update password
                conn.execute(
                    text("UPDATE admin SET password_hash = :hash WHERE username = 'admin'"),
                    {"hash": hashed_password}
                )
                conn.commit()
                print(f"✅ Admin password reset successfully to: {new_password}")
            else:
                print("❌ Admin user not found. Creating new admin...")
                # Create new admin if doesn't exist
                conn.execute(
                    text("""
                        INSERT INTO admin (id, username, email, password_hash, created_at)
                        VALUES (gen_random_uuid(), 'admin', 'admin@eukexpress.com', :hash, NOW())
                    """),
                    {"hash": hashed_password}
                )
                conn.commit()
                print(f"✅ Admin user created with password: {new_password}")
        
        # Verify the update
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT username, email FROM admin WHERE username = 'admin'")
            )
            updated = result.first()
            if updated:
                print(f"✅ Verified: admin user exists with email: {updated.email}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Admin Password Reset Tool")
    print("=" * 50)
    
    # Show current .env values
    env_user = os.getenv("ADMIN_USERNAME", "admin")
    env_pass = os.getenv("ADMIN_PASSWORD", "EukExpress@2024Admin")
    print(f"📝 .env expects: {env_user} / {env_pass}")
    
    confirm = input("\n⚠️  Reset admin password to match .env? (y/n): ")
    if confirm.lower() == 'y':
        success = reset_admin_password()
        if success:
            print("\n✅ Password reset complete! Try logging in now.")
            print("Run this command to test: .\\test-api-fixed.ps1")
        else:
            print("\n❌ Failed to reset password. Check database connection.")
    else:
        print("❌ Operation cancelled")
