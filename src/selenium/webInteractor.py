import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By

class WebInteraction:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.driver = None

    def setup_webdriver(self):
        service = Service(executable_path=self.driver_path)
        self.driver = webdriver.Chrome(service=service)

    def load_webpage(self, url):
        print("Loading webpage...")
        self.driver.get(url)
        # Fetch and print the page title
        page_title = self.driver.title
        print(f"Webpage loaded. Title: '{page_title}'")

    def continuously_check_elements(self, url):
        self.setup_webdriver()
        self.load_webpage(url)

        try:
            while True:
                self.check_and_interact_with_elements()
                time.sleep(5)  # Wait for 5 seconds before checking again
        except KeyboardInterrupt:
            print("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()

    def check_and_interact_with_elements(self, retry_count=0):
        try:
            # Fetch and print page text
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            print(f"Page text: {page_text}")

            # Check for input fields and print their details
            input_fields = self.driver.find_elements(By.XPATH, '//input')
            if input_fields:
                print(f"Found {len(input_fields)} input field(s):")
                for field in input_fields:
                    print(f" - Type: {field.get_attribute('type')}, Name: {field.get_attribute('name')}")

            # Check for buttons, print their details, and click the first one found
            buttons = self.driver.find_elements(By.XPATH, '//button | //input[@type="button"] | //input[@type="submit"]')
            if buttons:
                print(f"Found {len(buttons)} button(s):")
                for button in buttons:
                    button_text = button.text or button.get_attribute('value')
                    button_id = button.get_attribute('id')
                    button_class = button.get_attribute('class')
                    print(f" - Text: {button_text}, ID: {button_id}, Class: {button_class}")
                buttons[0].click()
                print("Action: Clicked on the first button found.")
        except StaleElementReferenceException:
            print("StaleElementReferenceException caught, retrying...")
            if retry_count < 3:  # Limit retries to avoid infinite recursion
                self.driver.refresh()  # Refresh the page to reset state
                self.check_and_interact_with_elements(retry_count + 1)
        except WebDriverException as e:
            print(f"WebDriverException caught: {e}. Retrying...")
            if retry_count < 3:  # Limit retries to avoid infinite recursion
                self.driver.refresh()  # Refresh the page to reset state
                self.check_and_interact_with_elements(retry_count + 1)

    def close_browser(self):
        print("Closing the browser...")
        self.driver.quit()


# Usage
if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = 'http://localhost:8080/voting/15/xladn5qiu3k3yzz2reqehvj2e7x6beg3hr6ssra87zu6721jvrff00v224qiieq0'

    web_interaction = WebInteraction(driver_path)
    web_interaction.continuously_check_elements(url)
