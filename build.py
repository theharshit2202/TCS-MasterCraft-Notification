import os
import subprocess
import sys

def build_exe():
    """Build the executable using PyInstaller inside the virtual environment."""
    try:
        # Change directory to the project folder
        os.chdir(r"users\2810740\mc")
        # Prepare the command to activate the virtual environment and run all build steps
        command = (
            r".\Mc_Notification\scripts\activate && "
            f"{sys.executable} -m pip install pyinstaller && "
            "pyinstaller --name=MasterCraft_Notification --onefile --console MasterCraft_Notification.py"
        )
        subprocess.check_call(["cmd.exe", "/c", command])
        print("Build completed successfully!")
        print("Executable created in the 'dist' folder.")
        print("\nIMPORTANT: Make sure to copy the 'mc.env' file to the same folder as the executable.")
    except Exception as e:
        print(f"Error during build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_exe() 