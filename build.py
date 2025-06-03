import os
import subprocess
import sys

def build_exe():
    """Build the executable using PyInstaller."""
    try:
        # Install PyInstaller if not already installed
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
        # Build the executable
        subprocess.check_call([
            "pyinstaller",
            "--name=MasterCraft_Notification",
            "--onefile",
            "--console",
            "MasterCraft_Notification.py"
        ])
        
        print("Build completed successfully!")
        print("Executable created in the 'dist' folder.")
        print("\nIMPORTANT: Make sure to copy the 'mc.env' file to the same folder as the executable.")
    except Exception as e:
        print(f"Error during build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_exe() 