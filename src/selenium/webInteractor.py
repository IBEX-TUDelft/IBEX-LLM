import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        print("Webpage loaded.")

    def continuously_check_elements(self, url):
        self.setup_webdriver()
        self.load_webpage(url)

        try:
            while True:
                # Check for input fields
                input_fields = self.driver.find_elements(By.XPATH, '//input')
                if input_fields:
                    print(f"Found {len(input_fields)} input field(s):")
                    for field in input_fields:
                        print(f" - Type: {field.get_attribute('type')}, Name: {field.get_attribute('name')}")
                else:
                    print("No input fields found.")

                # Check for buttons and print them
                buttons = self.driver.find_elements(By.XPATH, '//button | //input[@type="button"] | //input[@type="submit"]')
                if buttons:
                    print(f"Found {len(buttons)} button(s):")
                    for button in buttons:
                        button_text = button.text or button.get_attribute('value')  # Button text or value for input buttons
                        button_id = button.get_attribute('id')
                        button_class = button.get_attribute('class')
                        print(f" - Text: {button_text}, ID: {button_id}, Class: {button_class}")
                    buttons[0].click()
                    print("Clicked on the first button found.")
                else:
                    print("No buttons found.")

                time.sleep(5)  # Wait for 5 seconds before checking again
        except KeyboardInterrupt:
            print("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()

    def close_browser(self):
        print("Closing the browser...")
        self.driver.quit()

# Usage
if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = 'http://localhost:8080/voting/15/dug7bufakcv93o3l62tyqiyd7afkq8uow9vplcijk3regt6nqg60ox7lpv09dht0'

    web_interaction = WebInteraction(driver_path)
    web_interaction.continuously_check_elements(url)
