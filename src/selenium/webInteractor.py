import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebInteraction:
    def __init__(self, driver_path, browser='chrome'):
        self.driver_path = driver_path
        self.driver = None
        self.browser = browser

    def setup_webdriver(self):
        if self.browser.lower() == 'chrome':
            service = Service(executable_path=self.driver_path)
            self.driver = webdriver.Chrome(service=service)
        # Add elif statements for other browsers if needed
        else:
            logging.error(f"Browser '{self.browser}' is not supported.")
            return

    def load_webpage(self, url):
        logging.info("Loading webpage...")
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Wait for the body to load
        page_title = self.driver.title
        logging.info(f"Webpage loaded. Title: '{page_title}'")

    def continuously_check_elements(self, url):
        self.setup_webdriver()
        self.load_webpage(url)

        try:
            while True:
                self.check_and_interact_with_elements()
                time.sleep(5)  # Wait for 5 seconds before checking again
        except KeyboardInterrupt:
            logging.info("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()

    def check_and_interact_with_elements(self, retry_count=0):
        try:
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            logging.info(f"Page text: {page_text}")
            self.find_and_log_elements('//input', 'input field(s)')
            self.find_and_click_first_button()
        except (StaleElementReferenceException, WebDriverException) as e:
            self.handle_exceptions(e, retry_count)

    def find_and_log_elements(self, xpath, element_type):
        elements = self.driver.find_elements(By.XPATH, xpath)
        if elements:
            logging.info(f"Found {len(elements)} {element_type}:")
            for element in elements:
                logging.info(f" - Type: {element.get_attribute('type')}, Name: {element.get_attribute('name')}")

    def find_and_click_first_button(self):
        buttons_xpath = '//button | //input[@type="button"] | //input[@type="submit"]'
        buttons = self.driver.find_elements(By.XPATH, buttons_xpath)
        if buttons:
            logging.info(f"Found {len(buttons)} button(s):")
            first_button = buttons[0]
            first_button.click()
            logging.info("Action: Clicked on the first button found.")

    def handle_exceptions(self, exception, retry_count):
        logging.warning(f"{type(exception).__name__} caught: {exception}. Retrying...")
        if retry_count < 3:
            self.driver.refresh()
            self.check_and_interact_with_elements(retry_count + 1)

    def close_browser(self):
        logging.info("Closing the browser...")
        self.driver.quit()

# Usage
if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = 'http://localhost:8080/voting/15/xladn5qiu3k3yzz2reqehvj2e7x6beg3hr6ssra87zu6721jvrff00v224qiieq0'

    web_interaction = WebInteraction(driver_path)
    web_interaction.continuously_check_elements(url)
