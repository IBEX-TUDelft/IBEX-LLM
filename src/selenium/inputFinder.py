from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class InputFieldFinder:
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

    def find_input_fields(self, field_criteria):
        wait = WebDriverWait(self.driver, 2)
        print("Looking for input fields...")
        try:
            # Building the XPath based on the provided criteria
            field_xpath = "//input"
            if field_criteria:
                for key, value in field_criteria.items():
                    field_xpath += f"[@{key}='{value}']"
            input_fields = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, field_xpath)))

            if input_fields:
                print(f"Found {len(input_fields)} input field(s).")
                for field in input_fields:
                    print(
                        f"Field Type: {field.get_attribute('type')}, Field Name: {field.get_attribute('name')}")
            else:
                print("No input fields found.")
        except Exception as e:
            print("An error occurred while trying to find input fields:", e)

    def close_browser(self):
        print("Closing the browser...")
        # self.driver.quit()


# Usage
if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = 'http://localhost:8080/voting/15/buoj08db3mhgq6c8n4uyjeq3unydo7zrtw1kdamb3dp0caylh11lg8d72s6l9dl0'
    # Example criteria: Find all text input fields
    field_criteria = {"type": "text"}

    input_field_finder = InputFieldFinder(driver_path)
    input_field_finder.setup_webdriver()
    input_field_finder.load_webpage(url)
    input_field_finder.find_input_fields(field_criteria)
    input_field_finder.close_browser()
