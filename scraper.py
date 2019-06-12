"""
Selenium-based web scraper application to take grades from Moodle.

The browser uses Firefox to log into Moodle,
navigate to the grade report, then return the found grades.
Selenium is used as a backend for web scraping and web navigation.
In a Linux distro (Xenial @ Travis CI), the scraping program will
use an external SauceLabs server for Selenium.

Caleb Shilling
"""
import time
import platform
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import InvalidArgumentException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException


class Gradescraper():
    """Selenium-based web scraper application to take grades from Moodle."""

    def __init__(self, headless=True):
        """Set if the web driver should be booted in headless mode."""
        self.state = headless
        self.cell_name = 'grade-report-overview-303687_r'
        self.web_driver = None
        self.log_link = "log.txt"
        self.login_link = "https://identity.linnbenton.edu"
        self.login_confirm = "https://elearning.linnbenton.edu/login/index.php"
        self.redirect = "https://elearning.linnbenton.edu/my/"

    def start(self):
        """Init the webdriver in visible or headless mode."""
        if platform.system() == "Windows":
            # Use a local GeckoDriver (Firefox) on Windows.
            fox_options = Options()
            fox_options.headless = self.state
            gecko = "dependencies/geckodriver.exe"
            full_gecko = os.path.abspath(gecko)
            self.web_driver = webdriver.Firefox(
                executable_path=full_gecko, options=fox_options)
        else:
            # Use a remote server if testing on Travis.
            # Obtain remote access key and user name from enviroment veriables.
            username = os.environ["SAUCE_USERNAME"]
            access_key = os.environ["SAUCE_ACCESS_KEY"]
            # Setup the remote Selenium instance.
            capabilities = {}
            capabilities["tunnel-identifier"] = os.environ["TRAVIS_JOB_NUMBER"]
            capabilities['version'] = "45.0"
            capabilities['browserName'] = "firefox"
            hub_url = "%s:%s@localhost:4445" % (username, access_key)
            self.web_driver = webdriver.Remote(
                desired_capabilities=capabilities,
                command_executor="http://%s/wd/hub" % hub_url)

    def login(self, username, password):
        """Log into Moodle using an x number and password."""
        self.web_driver.get(self.login_link)

        timeout = Timeout(10)
        while True:
            try:
                username_field = \
                    self.web_driver.find_element_by_id("j_username")
                password_field = \
                    self.web_driver.find_element_by_id("j_password")
                break
            except NoSuchElementException:
                pass

            if timeout.exceeded():
                return False

        # Type in username and password, then click the sign in button.
        username_field.send_keys(username)
        password_field.send_keys(password)
        self.web_driver.find_element_by_name("loginform:loginBtn").click()
        self.web_driver.get(self.login_confirm)

        timeout = Timeout(10)
        while self.web_driver.current_url != self.redirect:
            if timeout.exceeded():
                return False

        return True

    def get_grades(self, test_url=None):
        """Navigates to the grade report and runs the grade scraper."""
        # If in test mode, navigate to the set test page.
        try:
            if test_url is not None:
                self.web_driver.get(test_url)
                self.write_log(f"Navigating to {test_url}")
            else:
                grade_report = "https://elearning.linnbenton.edu\
/grade/report/overview/index.php?id=2721"
                self.web_driver.get(grade_report)
                self.write_log(f"Navigating to {grade_report}")

            time.sleep(5)
            cell_test_text = f"{self.cell_name}{0}_c0"
            out = self.web_driver.find_element_by_id(cell_test_text).text
        except NoSuchElementException:
            self.write_log("Unable to scrape.")
            return "E"

        except InvalidArgumentException:
            self.write_log("Unable to scrape: Bad Link.")
            return "E"

        except WebDriverException:
            self.write_log("Unable to scrape: Bad Link.")
            return "E"

        self.write_log(f"Scraping begun. Class ID = {out}")
        return self.scrape_grades()

    def scrape_grades(self, cycle=0):
        """Return a class + its grade. Recursive."""
        cell_1_text = f"{self.cell_name}{cycle}_c0"
        cell_2_text = f"{self.cell_name}{cycle}_c1"
        cell_1 = self.web_driver.find_element_by_id(cell_1_text).text
        cell_2 = self.web_driver.find_element_by_id(cell_2_text).text

        if cell_1 == "":
            return ""

        class_name = ""
        for char in cell_1:
            if char == " " or len(class_name) > 9:
                break
            else:
                class_name += char

        grade = ""
        for char in cell_2:
            if char.isdigit() or char == ".":
                grade += char

        grades = self.scrape_grades(cycle=cycle+1)
        new_grade = [class_name, grade]

        if grades == "":
            return [new_grade]

        self.write_log(f"Class: {class_name} Grade: {grade}")
        grades.append(new_grade)
        return grades

    def end_session(self):
        """Close and stops the web driver."""
        self.web_driver.quit()
        self.write_log("Web driver ended.")

    def write_log(self, log_output):
        """Print to a log file."""
        with open(self.log_link, "a") as log_file:
            log_file.writelines(log_output + "\n")


class Timeout():
    """Instantiates a timeout timer."""

    def __init__(self, length):
        """Init a timeout timer which can be checked periodically."""
        self.length = length
        self.start_time = int(time.time())

    def exceeded(self):
        """Check if the timeout has exceeded its length."""
        return int(time.time()) - self.start_time >= self.length

    def time_left(self):
        """Return the time left in the timeout."""
        return 10 - (int(time.time()) - self.start_time)
