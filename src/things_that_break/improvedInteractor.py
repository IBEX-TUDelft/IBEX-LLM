import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException

class WebInteraction:
    """Class for interacting with webpages using Selenium WebDriver."""

    def __init__(self, driver_path: str):
        """Initialize the WebInteraction object with the path to the ChromeDriver."""
        self.driver_path = driver_path
        self.driver = None

    def setup_webdriver(self):
        """Sets up the Chrome WebDriver."""
        service = Service(executable_path=self.driver_path)
        self.driver = webdriver.Chrome(service=service)

    def load_webpage(self, url: str):
        """Loads a webpage and prints its title."""
        print("Loading webpage...")
        self.driver.get(url)
        page_title = self.driver.title
        print(f"Webpage loaded. Title: '{page_title}'")

    def interact_with_webpage_elements(self):
        """Checks and interacts with elements on the webpage."""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            print(f"Page text: {page_text}")

            input_fields = self.driver.find_elements(By.XPATH, '//input')
            print(f"Found {len(input_fields)} input field(s).")
            for field in input_fields:
                print(f" - Type: {field.get_attribute('type')}, Name: {field.get_attribute('name')}")

            buttons = self.driver.find_elements(By.XPATH, '//button | //input[@type="button"] | //input[@type="submit"]')
            print(f"Found {len(buttons)} button(s).")
            for button in buttons:
                button_text = button.text or button.get_attribute('value')
                print(f" - Text: {button_text}, ID: {button.get_attribute('id')}, Class: {button.get_attribute('class')}")
            buttons[0].click()
            print("Clicked on the first button found.")
        except StaleElementReferenceException:
            print("StaleElementReferenceException caught, retrying...")
            self.interact_with_webpage_elements()

    def continuously_check_elements(self, url: str):
        """Continuously checks and interacts with elements on the webpage."""
        self.setup_webdriver()
        self.load_webpage(url)

        try:
            while True:
                self.interact_with_webpage_elements()
                time.sleep(5)
        except KeyboardInterrupt:
            print("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()

    def close_browser(self):
        """Closes the browser."""
        print("Closing the browser...")
        self.driver.quit()

if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = 'http://localhost:8080/voting/15/chw0dfiy4dk6dkhanwu2pmk1o8pfho7nugyljkw765he5kn3i3gkp6nm4kgfl6g0'
    web_interaction = WebInteraction(driver_path)
    web_interaction.continuously_check_elements(url)
