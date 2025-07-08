"""
Launch script for the GenAI Document Assistant
"""
import subprocess
import sys
import os

def main():
    """Run the Streamlit application"""
    try:
        print("🚀 Starting GenAI Document Assistant...")
        print("📋 Make sure you have your OpenAI API key ready!")
        print("🌐 The app will open in your default browser...")
        print("\n" + "="*50)
        
        # Run the Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "false",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()