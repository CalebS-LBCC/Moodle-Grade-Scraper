"""
Main application which runs a Kivy interface.

The Kivy interface uses a custom grade scraping application
as well as multithreading code for running the scraping in
a seperate thread.

Caleb Shilling
"""

import threading
import time

from kivy.app import App
from kivy.config import Config
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from scraper import Gradescraper

Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', '200')
Config.set('graphics', 'height', '200')


class Screen(GridLayout):
    """Main class that manages Kivy UI and scraping thread."""

    def __init__(self, gr_scraper=Gradescraper(), test_mode=False, **kwargs):
        """Init the code scraping thread and make all UI wigets."""
        super(Screen, self).__init__(**kwargs)

        if not test_mode:
            self.set_background()

        self.grade_scraper = gr_scraper
        self.classes = [None, None, None, None, None]
        self.classes[0] = Label(text="No Class", x=0, y=100)
        self.classes[1] = Label(text="No Class", x=0, y=75)
        self.classes[2] = Label(text="No Class", x=0, y=50)
        self.classes[3] = Label(text="No Class", x=0, y=25)
        self.classes[4] = Label(text="No Class", x=0, y=0)
        self.add_widget(self.classes[0])
        self.add_widget(self.classes[1])
        self.add_widget(self.classes[2])
        self.add_widget(self.classes[3])
        self.add_widget(self.classes[4])

        self.grades = [None, None, None, None, None]
        self.grades[0] = Label(text="No Grade", x=100, y=100)
        self.grades[1] = Label(text="No Grade", x=100, y=75)
        self.grades[2] = Label(text="No Grade", x=100, y=50)
        self.grades[3] = Label(text="No Grade", x=100, y=25)
        self.grades[4] = Label(text="No Grade", x=100, y=0)
        self.add_widget(self.grades[0])
        self.add_widget(self.grades[1])
        self.add_widget(self.grades[2])
        self.add_widget(self.grades[3])
        self.add_widget(self.grades[4])

        if not test_mode:
            self.thread = threading.Thread(target=self.worker)
            self.thread.setDaemon(True)
            self.thread.start()

    def set_background(self, config=None):
        """Set the application background."""
        if config is None:
            img_src = pull_data()["app_background"]
        else:
            img_src = pull_data(file_=config)["app_background"]

        try:
            with open(img_src, "r") as _:
                pass
            back = Image(source=img_src, width=200, height=300, y=-50)
            self.add_widget(back)
            print("Background added successfully.")
        except FileNotFoundError:
            print("Background link incorrect. Not using a background.")

    def worker(self):
        """Worker thread used to run update every 10 minutes."""
        self.grade_scraper.start()
        username = pull_data()["moodle_username"]
        password = pull_data()["moodle_password"]
        logged_in = self.grade_scraper.login(username, password)

        if logged_in:
            self.grade_scraper.write_log("Logged in successfully to Moodle.")
            while True:
                self.update()
                time.sleep(600)
        if not logged_in:
            self.grade_scraper.write_log("Moodle login unsuccessful.")

    def update(self):
        """Update widgets after new data comes from the web scraper."""
        set_ = 0
        grades = self.grade_scraper.get_grades()
        if grades == "E":
            print("Error: Unable to scrape data.")
            return

        for combo in grades:
            try:
                if combo[0] != "" and combo[1] != "":
                    self.classes[set_].text = combo[0]
                    self.grades[set_].text = combo[1]
                    set_ += 1
            except IndexError:
                self.classes[set_].text = ""
                self.grades[set_].text = ""


def pull_data(file_=None):
    """Pull all entires from a configuration file."""
    values = {}
    if file_ is None:
        with open("config.cfg", "r") as config:
            for line in config.read().splitlines():
                data = line.split("=")
                config_line = {data[0]: data[1]}
                values.update(config_line)
    else:
        for line in file_.read().splitlines():
            data = line.split("=")
            config_line = {data[0]: data[1]}
            values.update(config_line)

    return values


class KivyApp(App):
    """Build a Kivy application framework."""

    def __init__(self):
        """Init classes and variables."""
        super(KivyApp, self).__init__()
        self.grade_scraper = Gradescraper()
        self.screen = Screen(gr_scraper=self.grade_scraper)

    def build(self):
        """Create the grade scraper and Screen objects."""
        return self.screen

    def close(self):
        """Close the grade scraper object."""
        self.grade_scraper.end_session()


if __name__ == '__main__':
    APP = KivyApp()
    APP.run()
    APP.close()
