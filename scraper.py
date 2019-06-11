"""
Selenium-based web scraper application to take grades from Moodle.

The browser uses Firefox to log into Moodle,
navigate to the grade report, then return the found grades.
Selenium is used as a backend for web scraping and web navigation.

Caleb Shilling
"""
import time
import platform
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException


class Gradescraper():
    """Selenium-based web scraper application to take grades from Moodle."""

    def __init__(self, headless=True):
        """Set if the web driver should be booted in headles mode."""
        # This is done to allow Grade_Scraper to be initalized
        # out of the Screen class.
        self.state = headless
        self.cell_name = 'grade-report-overview-303687_r'
        self.web_driver = None
        self.log_link = "log.txt"

    def start(self):
        """Init the webdriver in visible or headless mode."""
        if platform.system() == "Windows":
            # Use a local GeckoDriver on Windows
            ffo = Options()
            ffo.headless = self.state
            gecko = "dependencies/geckodriver.exe"
            full_gecko = os.path.abspath(gecko)
            self.web_driver = webdriver.Firefox(
                executable_path=full_gecko, options=ffo)
        else:
            # Use a remote server if testing on Travis
            username = os.environ["SAUCE_USERNAME"]
            access_key = os.environ["SAUCE_ACCESS_KEY"]
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
        self.web_driver.get("https://identity.linnbenton.edu")

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

        username_field.send_keys(username)
        password_field.send_keys(password)
        self.web_driver.find_element_by_name("loginform:loginBtn").click()

        self.web_driver.get("https://elearning.linnbenton.edu/login/index.php")
        target_url = "https://elearning.linnbenton.edu/my/"

        timeout = Timeout(10)
        while self.web_driver.current_url != target_url:
            if timeout.exceeded():
                return False

        return True

    def get_grades(self, test=None):
        """Navigates to the grade report and runs the grade scraper."""
        target_url = "https://elearning.linnbenton.edu\
/grade/report/overview/index.php?id=2721"

        if test is not None:
            target_url = test

        self.web_driver.get(target_url)
        self.write_log(f"Navigating to {target_url}")
        time.sleep(5)
        self.write_log("Scraping begun.")
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
