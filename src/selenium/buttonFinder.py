from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ButtonFinder:
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

    def find_and_click_button(self, button_xpath):
        wait = WebDriverWait(self.driver, 10)
        print("Looking for the button...")
        try:
            button = wait.until(EC.element_to_be_clickable((By.XPATH, button_xpath)))
            if button:
                print("Button found: " + button.text)
                button.click()  # Uncomment to click the button
            else:
                print("Button not found.")
        except Exception as e:
            print("An error occurred while trying to find the button:", e)

    def close_browser(self):
        print("Closing the browser...")
        self.driver.quit()

# Usage
if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    button_xpath = "//button[contains(@class, 'btn') and contains(@class, 'btn-primary') and contains(@class, 'btn-lg')]"
    url = 'http://localhost:8080/voting/15/ncbvu5s8jleb6owei29f09qwor3f55nn0tbegoiuqhop5s9ie23pn9q3oagjkbr0'

    button_finder = ButtonFinder(driver_path)
    button_finder.setup_webdriver()
    button_finder.load_webpage(url)
    button_finder.find_and_click_button(button_xpath)
    # button_finder.close_browser()
