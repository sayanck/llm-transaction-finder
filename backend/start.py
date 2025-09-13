
import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Start the FastAPI server."""
    
    # Ensure we're in the correct directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check for data file
    data_file = backend_dir.parent / "Transaction_data_All.xlsx"
    if not data_file.exists():
        print("❌ Error: Transaction_data_All.xlsx not found in project root")
        print("Please ensure the data file is placed in the correct location.")
        sys.exit(1)
    
    # Check for environment file
    env_file = backend_dir.parent / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("The application will run in mock mode without real AI analysis.")
        print("To enable AI features, create a .env file with GEMINI_API_KEY.")
        print()
    
    print("🚀 Starting LLM Transaction Pattern Finder Backend...")
    print(f"📁 Data file: {data_file}")
    print(f"🌐 Server will be available at: http://localhost:8000")
    print(f"📚 API documentation: http://localhost:8000/docs")
    print()
    
    try:
        # Import the app after changing directory
        from main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
