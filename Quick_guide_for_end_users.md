# MasterCraft Notification System - User Guide

## For Non-Technical Users

## First Time Setup
1. Create a folder named "MasterCraft Notification" on your desktop
2. Copy these files into the folder:
   - `MasterCraft_Notification.exe` (the program)
   - `mc.env` (the settings file)
3. Open `mc.env` with Notepad and update these settings:
   - `BASE_URL`: Your MasterCraft website address
   - `FALLBACK_URL`: Your backup website address (if you have one)
   - `CURRENT_USER`: Your username (or multiple usernames separated by commas)
   - `MASTERCRAFT_LOGIN_ID`: Your login ID
   - `MASTERCRAFT_PASSWORD`: Your password

## Running the Program
1. Double-click `MasterCraft_Notification.exe`
2. A black window will open - this is normal, don't close it
3. The program will automatically:
   - Log into MasterCraft
   - Start monitoring for defects
   - Show notifications when defects are found
   - Add itself to startup (so it runs when you turn on your computer)

## Using the Program
- When defects are found, you'll see a Windows notification
- Click "Stop" in the notification to pause monitoring for 30 minutes
- To resume monitoring:
  - Type 'resume' in the black window and press Enter
  - Or wait for automatic resume after 30 minutes
- To stop the program completely:
  - Type 'stop' in the black window and press Enter

## Important Notes
- Keep the black window open while using the program
- Don't delete the `mc.env` file
- The program will create a log file (`selenium_errors.log`) - you can ignore this
- If you need to change settings, edit `mc.env` and restart the program

## Troubleshooting
1. If the program doesn't start:
   - Make sure both `.exe` and `mc.env` are in the same folder
   - Check that your settings in `mc.env` are correct
   - Try running the program again

2. If you don't see notifications:
   - Check Windows notification settings
   - Make sure you're using Windows 10 or later

3. If you need to stop the program:
   - Type 'stop' in the black window and press Enter
   - The window will close automatically

4. If the program doesn't start on boot:
   - Check if the program is in the startup folder
   - Try running it manually first
   - Check the log file for any errors 