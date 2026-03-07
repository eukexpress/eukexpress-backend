# reset_admin_password_fixed.py
import os
import sys
import bcrypt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def hash_password(password):
    """Hash password using bcrypt directly"""
    # bcrypt expects bytes, and has a 72 byte limit
    password_bytes = password.encode('utf-8')[:72]  # Truncate to 72 bytes if needed
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def reset_admin_password():
    """Reset the admin password in the database"""
    
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        print("Please check your .env file")
        return False
    
    print(f"🔌 Connecting to database...")
    print(f"Database URL: {DATABASE_URL.replace(os.getenv('DATABASE_PASSWORD', ''), '****')}")
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        
        # New password (same as .env)
        new_password = "EukExpress@2024Admin"
        hashed_password = hash_password(new_password)
        
        print(f"🔑 Password hash generated successfully")
        
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
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection():
    """Test database connection without making changes"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Admin Password Reset Tool")
    print("=" * 50)
    
    # Test connection first
    print("\n📡 Testing database connection...")
    if not test_connection():
        print("\n❌ Cannot connect to database. Please check:")
        print("1. DATABASE_URL in .env file")
        print("2. Network connection to database")
        print("3. Database credentials")
        sys.exit(1)
    
    # Show current .env values
    env_user = os.getenv("ADMIN_USERNAME", "admin")
    env_pass = os.getenv("ADMIN_PASSWORD", "EukExpress@2024Admin")
    print(f"\n📝 .env expects: {env_user} / {env_pass}")
    
    confirm = input("\n⚠️  Reset admin password to match .env? (y/n): ")
    if confirm.lower() == 'y':
        success = reset_admin_password()
        if success:
            print("\n✅ Password reset complete! Try logging in now.")
            print("Run this command to test: .\\test-api-fixed.ps1")
        else:
            print("\n❌ Failed to reset password. Check error messages above.")
    else:
        print("❌ Operation cancelled")
