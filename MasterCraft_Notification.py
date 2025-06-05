import os
import sys
import time
import logging
import threading
import winreg
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv
# from win32com.client import Dispatch
from winotify import Notification
import http.server
import socketserver

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    SessionNotCreatedException
)
import keyboard
from urllib3.exceptions import ReadTimeoutError

# Custom exceptions
class MasterCraftError(Exception):
    """Base exception for MasterCraft application."""
    pass

class ConfigurationError(MasterCraftError):
    """Raised when there's an error in configuration."""
    pass

class WebDriverError(MasterCraftError):
    """Raised when there's an error with WebDriver operations."""
    pass

class NotificationError(MasterCraftError):
    """Raised when there's an error with system notifications."""
    pass

@dataclass
class Config:
    """Configuration settings for the application."""
    base_url: str
    fallback_url: str
    current_users: List[str]
    target_statuses: List[str]
    login_id: str
    password: str
    implicit_wait_timeout: int = 50
    explicit_wait_timeout: int = 100
    log_file: str = "selenium_errors.log"
    pause_duration: int = 1800  # 30 minutes in seconds
    check_interval_with_defects: int = 180  # 3 minutes when defects are found
    check_interval_no_defects: int = 60  # 1 minute when no defects are found
    session_restart_interval: int = 1800  # Default 30 minutes
    chrome_headless: bool = False
    retain_existing_filters: bool = False

    @classmethod
    def from_env(cls) -> 'Config':
        """Create Config instance from environment variables."""
        return cls(
            base_url=os.getenv("BASE_URL", ""),
            fallback_url=os.getenv("FALLBACK_URL", ""),
            current_users=[x.strip() for x in os.getenv("CURRENT_USER", "").split(',')],
            target_statuses=[status.strip().lower() for status in os.getenv("TARGET_STATUSES", "open").split(',')],
            login_id=os.getenv("MASTERCRAFT_LOGIN_ID", ""),
            password=os.getenv("MASTERCRAFT_PASSWORD", ""),
            check_interval_with_defects=int(os.getenv("CHECK_INTERVAL_WITH_DEFECTS", "180")),
            check_interval_no_defects=int(os.getenv("CHECK_INTERVAL_NO_DEFECTS", "60")),
            pause_duration=int(os.getenv("PAUSE_DURATION", "1800")),
            session_restart_interval=int(os.getenv("SESSION_RESTART_INTERVAL", "1800")),
            chrome_headless=os.getenv("CHROME_HEADLESS", "false").lower() == "true",
            retain_existing_filters=os.getenv("RETAIN_EXISTING_FILTERS", "false").lower() == "true"
        )


class ResourceManager:
    """Manages resource paths and environment setup."""
    
    @staticmethod
    def get_resource_path(relative_path: str = "") -> Path:
        """Gets the absolute path to a resource."""
        try:
            base_path = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
            return base_path / relative_path if relative_path else base_path
        except Exception as e:
            raise ConfigurationError(f"Failed to get resource path: {e}")

    @staticmethod
    def ensure_log_directory(log_file: str) -> None:
        """Ensures the log directory exists and creates it if necessary."""
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create log file if it doesn't exist
            if not log_path.exists():
                log_path.touch()
                logging.info(f"Created new log file at: {log_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to create log directory/file: {e}")

    @staticmethod
    def setup_logging(log_file: str) -> None:
        """Sets up logging configuration with enhanced formatting."""
        try:
            # Ensure log directory and file exist
            ResourceManager.ensure_log_directory(log_file)
            
            # Add separator for new run
            with open(log_file, 'a') as f:
                f.write(f"\n{'#'*50}\nNew Run Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'#'*50}\n")
            
            # Configure logging
            logging.basicConfig(
                filename=log_file,
                level=logging.DEBUG,
                format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            
            # Add console handler for immediate feedback
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(console_formatter)
            logging.getLogger().addHandler(console_handler)
            
            logging.info("Logging system initialized successfully")
        except Exception as e:
            raise ConfigurationError(f"Failed to setup logging: {e}")

    @staticmethod
    def load_config() -> Config:
        """Loads configuration from environment variables."""
        try:
            env_path = ResourceManager.get_resource_path("mc.env")
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
            else:
                logging.warning(f"Environment file not found at: {env_path}")
                # Create a default .env file if it doesn't exist
                default_env_content = """# MasterCraft URLs
                                    BASE_URL=https://your-mastercraft-instance.com
                                    FALLBACK_URL=https://your-fallback-url.com

                                    # User Configuration
                                    CURRENT_USER=user1,user2,user3
                                    TARGET_STATUSES=open,assigned

                                    # Login Credentials
                                    MASTERCRAFT_LOGIN_ID=your_login_id
                                    MASTERCRAFT_PASSWORD=your_password

                                    # Timing Configuration (in seconds)
                                    CHECK_INTERVAL_WITH_DEFECTS=180    # Check every 3 minutes when defects are found
                                    CHECK_INTERVAL_NO_DEFECTS=60       # Check every 1 minute when no defects are found
                                    PAUSE_DURATION=1800               # Pause duration (30 minutes)
                                    SESSION_RESTART_INTERVAL=1800     # Session restart interval (30 minutes)
                                    """
                with open(env_path, 'w') as f:
                    f.write(default_env_content)
                logging.info(f"Created default .env file at: {env_path}")

            # Validate required environment variables
            required_vars = ["BASE_URL", "FALLBACK_URL", "CURRENT_USER", "MASTERCRAFT_LOGIN_ID", "MASTERCRAFT_PASSWORD"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                raise ConfigurationError(f"Missing required environment variables: {', '.join(missing_vars)}")

            return Config.from_env()
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")


class PauseManager:
    """Manages the pause/resume functionality of the application."""
    
    def __init__(self, pause_duration=1800):
        self._is_paused = False
        self._pause_until = None
        self._pause_lock = threading.Lock()
        self._console_thread = None
        self._stop_console_thread = False
        self._should_stop = False
        self._pause_duration = pause_duration
        self._http_server_thread = threading.Thread(target=self._start_http_server, daemon=True)
        self._http_server_thread.start()

    def _start_http_server(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(inner_self):
                if inner_self.path == '/pause':
                    self.pause(self._pause_duration)
                    inner_self.send_response(200)
                    inner_self.send_header('Content-type', 'text/html')
                    inner_self.end_headers()
                    inner_self.wfile.write(b'Paused')
                elif inner_self.path == '/resume':
                    self.resume()
                    inner_self.send_response(200)
                    inner_self.send_header('Content-type', 'text/html')
                    inner_self.end_headers()
                    inner_self.wfile.write(b'Resumed')
                else:
                    inner_self.send_response(404)
                    inner_self.end_headers()
        with socketserver.TCPServer(("", 5000), Handler) as httpd:
            httpd.serve_forever()

    def is_paused(self) -> bool:
        """Check if the application is currently paused."""
        with self._pause_lock:
            if self._is_paused and self._pause_until:
                if datetime.now() >= self._pause_until:
                    self._is_paused = False
                    self._pause_until = None
                    logging.info("Pause period completed, resuming automatically")
                    self._show_resume_notification()
            return self._is_paused

    def pause(self, duration_seconds: int = 1800) -> None:
        """Pause the application for the specified duration."""
        with self._pause_lock:
            self._is_paused = True
            self._pause_until = datetime.now() + timedelta(seconds=duration_seconds)
            logging.info(f"Application paused until {self._pause_until}")
            print("\nApplication is paused. Type 'resume' to continue immediately or wait for automatic resume.")
            self._show_pause_notification()

    def resume(self) -> None:
        """Resume the application immediately."""
        with self._pause_lock:
            self._is_paused = False
            self._pause_until = None
            logging.info("Application resumed")
            self._show_resume_notification()

    def _show_pause_notification(self) -> None:
        """Show notification that the application is paused."""
        try:
            toast = Notification(
                app_id="MasterCraft ALM",
                title="MasterCraft ALM",
                msg="Application is paused for 30 minutes. Click 'Resume' to continue immediately.",
                duration="short"
            )
            toast.add_actions(label="Resume", launch="http://localhost:5000/resume")
            toast.show()
        except Exception as e:
            logging.error(f"Failed to show pause notification: {e}")

    def _show_resume_notification(self) -> None:
        """Show notification that the application has resumed."""
        try:
            toast = Notification(
                app_id="MasterCraft ALM",
                title="MasterCraft ALM",
                msg="Application has resumed monitoring.",
                duration="short"
            )
            toast.show()
        except Exception as e:
            logging.error(f"Failed to show resume notification: {e}")

    def start_console_listener(self) -> None:
        """Start the console input listener thread."""
        self._stop_console_thread = False
        self._console_thread = threading.Thread(target=self._console_listener, daemon=True)
        self._console_thread.start()

    def stop_console_listener(self) -> None:
        """Stop the console input listener thread."""
        self._stop_console_thread = True
        if self._console_thread:
            self._console_thread.join(timeout=1.0)

    def stop(self) -> None:
        """Stop the application."""
        self._should_stop = True
        self._stop_console_thread = True
        logging.info("Application stop requested")

    def should_stop(self) -> bool:
        """Check if the application should stop."""
        return self._should_stop

    def _console_listener(self) -> None:
        """Listen for console input to resume the application or stop it."""
        while not self._stop_console_thread:
            # Check if paused and print message
            is_currently_paused = self.is_paused()
            if is_currently_paused:
                print("\nApplication is paused. Type 'resume' to continue immediately or wait for automatic resume.")
            # Always show the main prompt, but input() will wait
            print("\nType 'stop' to exit the program, 'resume' if paused, or 'pause' to pause the program.")
            try:
                # Wait for user input
                input_text = input().strip().lower()

                if input_text == 'resume' and is_currently_paused:
                    self.resume()
                    print("Application resumed.")
                elif input_text == 'pause' and not is_currently_paused:
                    self.pause(self._pause_duration)
                    print(f"Application paused for {self._pause_duration // 60} minutes.")
                elif input_text == 'stop':
                    self.stop()
                    print("Stopping application...")
                    return # Exit the thread
                else:
                    # Optional: provide feedback for invalid commands
                    if input_text not in ('resume', 'stop', 'pause'):
                        print(f"Unknown command: '{input_text}'. Please type 'resume', 'pause', or 'stop'.")

            except EOFError:
                 # Handle cases where input stream is closed (e.g., script run without interactive console)
                 logging.warning("EOF encountered in console listener. Exiting listener.")
                 self.stop()
                 return
            except Exception as e:
                logging.error(f"Error in console listener: {e}")

            # Add a small sleep when not paused to reduce CPU usage, though input() blocks
            # This sleep is mainly for when the loop might somehow continue without blocking on input()
            # or if the stop flag is set externally.
            if not is_currently_paused and not self.should_stop():
                 time.sleep(1) # Check stop flag periodically


class WebDriverManager:
    """Manages Selenium WebDriver operations."""
    
    def __init__(self, config: Config, pause_manager: PauseManager):
        self.config = config
        self.pause_manager = pause_manager
        self.driver = None
        self.original_window = None

    def initialize_driver(self) -> None:
        """Initializes the WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--allow-insecure-localhost")
            chrome_options.add_argument("--log-level=3")
            if self.config.chrome_headless:
                chrome_options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.config.implicit_wait_timeout)
            self.driver.maximize_window()
            self.original_window = self.driver.current_window_handle
            logging.info("WebDriver initialized successfully")
        except SessionNotCreatedException as e:
            logging.error("Failed to create WebDriver session. Please check Chrome WebDriver installation.")
            raise WebDriverError(f"Session creation failed: {e}")
        except WebDriverException as e:
            logging.error("Failed to initialize WebDriver")
            raise WebDriverError(f"WebDriver initialization failed: {e}")

    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> webdriver.remote.webelement.WebElement:
        """Waits for an element to be visible."""
        timeout = timeout or self.config.explicit_wait_timeout
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
        except TimeoutException:
            logging.error(f"Timeout waiting for element: {by}={value}")
            raise WebDriverError(f"Element not found after {timeout} seconds: {by}={value}")
        except StaleElementReferenceException:
            logging.error(f"Stale element reference: {by}={value}")
            raise WebDriverError(f"Element became stale: {by}={value}")

    def click_element(self, by: By, value: str) -> webdriver.remote.webelement.WebElement:
        """Clicks an element after waiting for it to be visible."""
        try:
            element = self.wait_for_element(by, value)
            element.click()
            return element
        except ElementClickInterceptedException:
            logging.error(f"Element click intercepted: {by}={value}")
            raise WebDriverError(f"Could not click element: {by}={value}")
        except ElementNotInteractableException:
            logging.error(f"Element not interactable: {by}={value}")
            raise WebDriverError(f"Element not clickable: {by}={value}")

    def enter_text(self, by: By, value: str, text: str) -> webdriver.remote.webelement.WebElement:
        """Enters text into an element after waiting for it to be visible."""
        try:
            element = self.wait_for_element(by, value)
            element.clear()
            element.send_keys(text)
            return element
        except ElementNotInteractableException:
            logging.error(f"Element not interactable for text entry: {by}={value}")
            raise WebDriverError(f"Could not enter text in element: {by}={value}")

    def login(self) -> None:
        """Performs login operation with robust handling for slow page loads."""
        try:
            logging.info("Attempting login")
            self.enter_text(By.ID, "userId", self.config.login_id)
            self.enter_text(By.ID, "password", self.config.password)
            self.click_element(By.XPATH, "//*[@id='loginTableId']/tbody/tr/td[3]/div/table/tbody/tr[8]/td/input[7]")

            # Wait up to 100 seconds for any <img> elements to appear (indicating loading)
            logging.info("Checking for <img> elements after login submit (up to 100 seconds)...")
            try:
                WebDriverWait(self.driver, 100).until(lambda d: len(d.find_elements(By.TAG_NAME, "img")) > 0)
                logging.info("<img> elements detected. Waiting indefinitely for the next required element (defMenuBtnId-btnInnerEl)...")
                # Wait indefinitely for the next required element
                self.wait_for_element(By.ID, "defMenuBtnId-btnInnerEl", timeout=None)
            except TimeoutException:
                logging.info("No <img> elements detected within 100 seconds. Proceeding to wait for the next required element with default timeout.")
                # self.wait_for_element(By.ID, "defMenuBtnId-btnInnerEl")

            logging.info("Login successful")
        except WebDriverError as e:
            logging.error("Login failed")
            raise WebDriverError(f"Login operation failed: {e}")

    def navigate_to_defects(self) -> None:
        """Navigates to the defects section."""
        try:
            logging.info("Navigating to Defect section...")
            self.click_element(By.ID, "defMenuBtnId-btnInnerEl")
            logging.info("Clicked on Defects")
            if self.config.retain_existing_filters:
                logging.info("RETAIN_EXISTING_FILTERS is true: Skipping filter funnel and filter removal.")
                return
            logging.info("Clicking on Filter Funnel")
            self.click_element(By.XPATH, "//span[contains(@class, 'filter')]")
            # Remove existing filter conditions
            try:
                red_cross_elements = self.driver.find_elements(By.XPATH, "//span[contains(@class, 'remove-filter-condition')]")
                if red_cross_elements:
                    red_cross_elements[0].click()
                    logging.info("Removed existing filter conditions")
            except NoSuchElementException:
                logging.info("No existing filter conditions found")
        except WebDriverError as e:
            logging.error("Failed to navigate to defects section")
            raise WebDriverError(f"Navigation failed: {e}")

    def enter_owner_details(self) -> None:
        """Enters owner details in the filter."""
        if self.config.retain_existing_filters:
            logging.info("RETAIN_EXISTING_FILTERS is true: Skipping entering owner details.")
            return
        try:
            self.click_element(By.XPATH, "(//span[contains(text(), 'Add')][1])")
            time.sleep(0.2)
            
            # Enter first owner
            self.driver.switch_to.active_element.send_keys("Current Owner", Keys.ENTER, Keys.TAB)
            time.sleep(0.5)
            self.driver.switch_to.active_element.send_keys(Keys.ENTER, Keys.TAB)
            time.sleep(1)
            self.driver.switch_to.active_element.send_keys(self.config.current_users[0])
            self.driver.switch_to.active_element.send_keys(Keys.ENTER, Keys.TAB)
            time.sleep(0.5)
            
            # Enter remaining owners
            for owner in self.config.current_users[1:]:
                logging.info(f"Adding owner: {owner}")
                self.click_element(By.XPATH, "(//span[contains(text(), 'Or')][last()])")
                time.sleep(0.2)
                self.driver.switch_to.active_element.send_keys("Current Owner", Keys.ENTER, Keys.TAB)
                time.sleep(0.2)
                self.driver.switch_to.active_element.send_keys(Keys.ENTER, Keys.TAB)
                time.sleep(0.2)
                self.driver.switch_to.active_element.send_keys(owner)
                self.driver.switch_to.active_element.send_keys(Keys.ENTER, Keys.TAB)
                time.sleep(0.2)
            
            # Apply and close
            self.click_element(By.XPATH, "(//span[contains(text(), 'Apply')][last()])")
            time.sleep(2)
            self.click_element(By.XPATH, "(//span[contains(text(), 'Close')][last()])")
            logging.info("Owner details entered successfully")
        except WebDriverError as e:
            logging.error("Failed to enter owner details")
            raise WebDriverError(f"Owner details entry failed: {e}")

    def check_new_defects(self) -> int:
        """Checks for new defects and returns the wait time for next check."""
        try:
            self.click_element(By.XPATH, "//span[contains(@class, 'loading')]")
            time.sleep(2)
            
            nodes = self.driver.find_elements(By.CSS_SELECTOR, "td > div.x-grid-cell-inner")
            logging.info(f"Number of elements found: {len(nodes)}")
            
            defect_count = sum(1 for node in nodes if node.text.strip().lower() in self.config.target_statuses)
            logging.info(f"Defects count: {defect_count}")
            
            if defect_count > 0:
                try:
                    toast = Notification(
                        app_id="MasterCraft ALM",
                        title="New Defects Found",
                        msg=f"You have {defect_count} defects pending. Please check. Click 'Pause' to pause monitoring for {self.config.pause_duration//60} minutes.",
                        duration="short"
                    )
                    toast.add_actions(label="Pause", launch="http://localhost:5000/pause")
                    toast.show()
                    logging.info(f"Notification sent for {defect_count} defects")
                except Exception as e:
                    logging.error(f"Failed to send notification: {e}")
                    raise NotificationError(f"Notification failed: {e}")
                return self.config.check_interval_with_defects
            
            return self.config.check_interval_no_defects
        except WebDriverError as e:
            logging.error("Failed to check for new defects")
            return self.config.check_interval_no_defects  # Default to no defects interval on error

    def cleanup(self) -> None:
        """Cleans up WebDriver resources."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver resources cleaned up successfully")
            except Exception as e:
                logging.error(f"Error during driver cleanup: {e}")


class MasterCraftNotifier:
    """Main class for the MasterCraft notification system."""
    
    def __init__(self):
        try:
            self.config = ResourceManager.load_config()
            self.pause_manager = PauseManager(pause_duration=self.config.pause_duration)
            self.web_driver = WebDriverManager(self.config, self.pause_manager)
            logging.info("MasterCraftNotifier initialized successfully")
        except ConfigurationError as e:
            logging.error(f"Failed to initialize MasterCraftNotifier: {e}")
            raise

    def run(self) -> None:
        """Main execution method."""
        try:
            self.web_driver.initialize_driver()
            self.pause_manager.start_console_listener()
            # Try primary URL, fall back to secondary if needed
            try:
                self.web_driver.driver.get(self.config.base_url)
                logging.info(f"Successfully loaded primary URL: {self.config.base_url}")
            except (ReadTimeoutError, WebDriverError, ConnectionResetError, ConnectionError, OSError, Exception) as e:
                logging.error(f"Network or WebDriver error loading primary URL: {e}. Trying fallback URL...")
                try:
                    if self.config.fallback_url:
                        self.web_driver.driver.get(self.config.fallback_url)
                        logging.info(f"Successfully loaded fallback URL: {self.config.fallback_url}")
                    else:
                        logging.error("No fallback URL available. Exiting...")
                        return
                except (ReadTimeoutError, WebDriverError, ConnectionResetError, ConnectionError, OSError, Exception) as e:
                    logging.error(f"Failed to load fallback URL: {e}")
                    logging.error("Both URLs failed. Exiting...")
                    return
            # Switch to new window if needed
            self.web_driver.driver.switch_to.window(self.web_driver.driver.window_handles[-1])
            if self.web_driver.original_window != self.web_driver.driver.current_window_handle:
                self.web_driver.driver.maximize_window()
                logging.info("Switched to new window and maximized")
            # Perform login and setup
            self.web_driver.login()
            self.web_driver.navigate_to_defects()
            self.web_driver.enter_owner_details()
            
            # Main monitoring loop
            session_start_time = time.time()
            while not self.pause_manager.should_stop():
                # Check if 30 minutes have passed since last browser session start
                need_restart = False
                if time.time() - session_start_time >= self.config.session_restart_interval:
                    logging.info(f"Session restart interval ({self.config.session_restart_interval} seconds) reached, restarting browser session to maintain continuity.")
                    need_restart = True
                try:
                    if not self.pause_manager.is_paused() and not need_restart:
                        seconds = self.web_driver.check_new_defects()
                        time.sleep(seconds)
                    elif not need_restart:
                        time.sleep(10)  # Check pause status every 10 seconds
                except WebDriverError as e:
                    error_message = str(e).lower()
                    if 'invalid session id' in error_message or 'browser has closed the connection' in error_message:
                        logging.info("Session error detected, restarting browser session to maintain continuity.")
                        need_restart = True
                    else:
                        logging.error(f"Error in monitoring loop: {e}")
                        time.sleep(60)  # Wait a minute before retrying
                if need_restart:
                    self.web_driver.cleanup()
                    # Re-initialize browser session
                    self.web_driver.initialize_driver()
                    try:
                        self.web_driver.driver.get(self.config.base_url)
                        logging.info(f"Successfully loaded primary URL: {self.config.base_url}")
                    except WebDriverError as e:
                        logging.error(f"Failed to load primary URL: {e}")
                        try:
                            self.web_driver.driver.get(self.config.fallback_url)
                            logging.info(f"Successfully loaded fallback URL: {self.config.fallback_url}")
                        except WebDriverError as e:
                            logging.error(f"Failed to load fallback URL: {e}")
                            break
                    self.web_driver.driver.switch_to.window(self.web_driver.driver.window_handles[-1])
                    if self.web_driver.original_window != self.web_driver.driver.current_window_handle:
                        self.web_driver.driver.maximize_window()
                        logging.info("Switched to new window and maximized")
                    self.web_driver.login()
                    self.web_driver.navigate_to_defects()
                    self.web_driver.enter_owner_details()
                    session_start_time = time.time()
        except Exception as e:
            logging.exception("An error occurred during execution")
        finally:
            self.pause_manager.stop_console_listener()
            self.web_driver.cleanup()
            logging.info("Program completed")


def add_to_startup() -> None:
    """Add the program to Windows startup."""
    try:
        # Get the path of the executable
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(__file__)
        
        # Create a shortcut in the startup folder
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
        )
        
        # Create a .bat file to run the program
        bat_path = os.path.join(startup_folder, 'MasterCraft_Notification.bat')
        with open(bat_path, 'w') as f:
            f.write(f'@echo off\nstart "" "{exe_path}"\n')
        
        logging.info(f"Added program to startup at: {bat_path}")
    except Exception as e:
        logging.error(f"Failed to add program to startup: {e}")


def main():
    """Entry point for the application."""
    try:
        # Check if this is the first run
        first_run_file = Path("first_run.txt")
        if not first_run_file.exists():
            add_to_startup()
            first_run_file.touch()
            logging.info("First run detected, added to startup")
        
        config = ResourceManager.load_config()
        ResourceManager.setup_logging(config.log_file)
        notifier = MasterCraftNotifier()
        notifier.run()
    except Exception as e:
        logging.exception("Fatal error in main execution")
        sys.exit(1)


if __name__ == "__main__":
    main()