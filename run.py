#!/usr/bin/env python3
"""
EukExpress API Runner
Run with: python run.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    dotenv_path = backend_dir / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        print(f"✅ Loaded environment from: {dotenv_path}")
    else:
        print(f"⚠️  No .env file found at {dotenv_path}")
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env loading")

print(f"""
🚀 EUKEXPRESS GLOBAL LOGISTICS API
═══════════════════════════════════════════════════
📅 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🐍 Python {sys.version.split()[0]}
📁 Directory: {os.getcwd()}
🔧 Environment: {os.environ.get('APP_ENV', 'development')}
═══════════════════════════════════════════════════
""")

if __name__ == "__main__":
    try:
        import uvicorn
        
        # Set environment variables to suppress GLib warnings
        os.environ["GIO_USE_VFS"] = "local"
        os.environ["GIO_USE_VOLUME_MONITOR"] = "unix"
        
        # Try to import the app to verify it works
        try:
            print("🔄 Importing app...")
            from app.main import app
            print("✅ App imported successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("🔧 Trying alternative import...")
            # Try direct import from file
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "main", 
                str(backend_dir / "app" / "main.py")
            )
            if spec and spec.loader:
                main_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(main_module)
                app = main_module.app
                print("✅ App loaded via direct import")
            else:
                print("❌ Could not load app module")
                sys.exit(1)
        
        print("\n" + "="*60)
        print("🌐 Starting EukExpress API Server...")
        print("📚 Docs: http://localhost:8000/docs")
        print("="*60 + "\n")
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)