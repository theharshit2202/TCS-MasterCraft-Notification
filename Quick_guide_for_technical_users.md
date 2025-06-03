# MasterCraft Notification System - Technical Guide

## Building from Source
1. Install Python 3.8 or later
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the build script:
   ```bash
   python build.py
   ```
4. The executable will be created in the `dist` folder

## Configuration Details
The `mc.env` file supports these settings:
```env
# Required Settings
BASE_URL=<your_mastercraft_url>
FALLBACK_URL=<your_fallback_url>
CURRENT_USER=<comma_separated_usernames>
TARGET_STATUSES=open,assigned
MASTERCRAFT_LOGIN_ID=<your_login_id>
MASTERCRAFT_PASSWORD=<your_password>

# Optional Settings (in seconds)
CHECK_INTERVAL_WITH_DEFECTS=180    # Check every 3 minutes when defects are found
CHECK_INTERVAL_NO_DEFECTS=60       # Check every 1 minute when no defects are found
PAUSE_DURATION=1800               # Pause duration (30 minutes)
```

## Technical Details
- The program uses Selenium WebDriver for automation
- Notifications are handled by win10toast
- Logging is implemented with Python's logging module
- Startup integration uses Windows startup folder
- The program creates a `first_run.txt` file to track first execution

## Development Information
- Source code is in `MasterCraft_Notification.py`
- Build script is in `build.py`
- Dependencies are listed in `requirements.txt`
- Logs are stored in `selenium_errors.log`

## Security Notes
- Credentials are stored in plain text in `mc.env`
- Consider implementing encryption for production use
- The program runs with user-level permissions
- No elevated privileges are required

## Common Issues and Solutions
1. WebDriver Issues:
   - Ensure Edge WebDriver is installed and in PATH
   - Check Edge browser version matches WebDriver version
   - Verify WebDriver permissions

2. Network Issues:
   - Check internet connectivity
   - Verify URLs in `mc.env`
   - Check firewall settings

3. Permission Issues:
   - Run as normal user (no admin required)
   - Check startup folder permissions
   - Verify file access permissions

4. Performance Issues:
   - Adjust check intervals in `mc.env`
   - Monitor system resources
   - Check log file for errors 