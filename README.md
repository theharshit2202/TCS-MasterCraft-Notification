# MasterCraft Notification System

A Windows-based notification system for monitoring defects in MasterCraft ALM. This application automatically checks for new defects and notifies users with interactive controls for pausing and resuming monitoring.

## Features

- Automated defect monitoring in MasterCraft ALM
- Interactive Windows notifications with pause/resume controls
- Automatic pause for 30 minutes when requested
- Console-based manual resume and stop options
- Automatic resume after pause period
- Configurable monitoring intervals
- Detailed logging system
- Environment-based configuration
- Automatic startup on system boot
- User-friendly console interface

## Technical Requirements

- Windows 10 or later
- Python 3.8 or later (for development)
- Microsoft Edge browser
- Edge WebDriver (compatible with your Edge version)

## Dependencies

The following Python packages are required:
```
selenium>=4.15.2      # Web automation
python-dotenv>=1.0.0  # Environment variable management
win10toast>=0.9      # Windows notifications
keyboard>=0.13.5     # Console input handling
plyer>=2.1.0         # System notifications
pywin32>=306         # Windows-specific functionality
pyinstaller>=6.0.0   # For building executable
```

## Installation

### For End Users
1. Download the latest release
2. Extract the files to a folder
3. Configure `mc.env` with your settings
4. Run `MasterCraft_Notification.exe`

### For Developers
1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download and install Edge WebDriver:
   - Visit: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
   - Download the version matching your Edge browser
   - Add the WebDriver to your system PATH

## Configuration

Create a `mc.env` file in the application directory with the following variables:

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
PAUSE_DURATION=1800               # Pause duration in seconds (30 minutes)
```

## Project Structure

```
MasterCraft_Notification/
├── MasterCraft_Notification.py  # Main application file
├── build.py                    # Build script for executable
├── requirements.txt            # Python dependencies
├── mc.env                      # Environment configuration
├── selenium_errors.log         # Application logs
├── QUICK_GUIDE.md             # User-friendly guide
└── README.md                   # This documentation
```

## Building the Executable

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Run the build script:
   ```bash
   python build.py
   ```

3. The executable will be created in the `dist` folder

## Logging

The application maintains detailed logs in `selenium_errors.log`:
- Each run is separated by timestamp markers
- Includes detailed error tracking
- Records all state changes and user interactions
- Maintains operation history

## Error Handling

The application implements comprehensive error handling:
- WebDriver exceptions
- Network connectivity issues
- Configuration errors
- Notification system failures
- Automatic recovery mechanisms

## Security Considerations

- Credentials are stored in environment variables
- No hardcoded sensitive information
- Secure session management
- Proper resource cleanup
- User-level permissions only

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 