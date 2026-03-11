#start.py
"""
EukExpress Production Startup Script
Run with: python start.py
"""

import os
import sys
import warnings
from pathlib import Path
from datetime import datetime

# Suppress all warnings and GLib messages
warnings.filterwarnings("ignore")
os.environ["GIO_USE_VFS"] = "local"
os.environ["GIO_USE_VOLUME_MONITOR"] = "local"
os.environ["G_MESSAGES_DEBUG"] = "none"
os.environ["NO_AT_BRIDGE"] = "1"
os.environ["PYTHONWARNINGS"] = "ignore"

# Redirect stderr to suppress GLib warnings
import contextlib
import sys

@contextlib.contextmanager
def suppress_stderr():
    """Suppress stderr output"""
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr

# Add the backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    dotenv_path = backend_dir / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
except ImportError:
    pass

# Print clean startup banner
print(f"""
╔════════════════════════════════════════════════════════════╗
║            EUKEXPRESS GLOBAL LOGISTICS API                ║
╠════════════════════════════════════════════════════════════╣
║  Status: 🟢 RUNNING                                        ║
║  Environment: {os.environ.get('APP_ENV', 'development').upper():<20}           ║
║  Python: {sys.version.split()[0]:<20}                     ║
║  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<20}          ║
╚════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    try:
        import uvicorn
        
        # Import app with suppressed stderr
        with suppress_stderr():
            from app.main import app
        
        print("📡 Server listening on:")
        print(f"   • Local:   http://localhost:8000")
        print(f"   • Docs:    http://localhost:8000/docs")
        print(f"   • Health:  http://localhost:8000/health")
        print("\n" + "─" * 50)
        
        # Run with clean output
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="warning",
            access_log=False
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)