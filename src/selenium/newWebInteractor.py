import time
import openai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

def read_text_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

class WebInteraction:
    def __init__(self, driver_path, browser='chrome', initial_prompt=None):
        self.driver_path = driver_path
        self.browser = browser
        self.initial_prompt = initial_prompt
        openai.api_key = self.load_api_key()
        if self.initial_prompt:
            self.send_message_to_llm(self.initial_prompt, "user", is_initial=True)

    def load_api_key(self):
        try:
            with open('../../config/token.txt', 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print("API key file not found. Please check the file path.")
            exit()

    def setup_webdriver(self):
        if self.browser.lower() == 'chrome':
            service = Service(executable_path=self.driver_path)
            self.driver = webdriver.Chrome(service=service)
        else:
            print(f"Browser '{self.browser}' is not supported.")
            return

    def send_message_to_llm(self, content, role, is_initial=False):
        try:
            message = {
                "role": role,
                "content": content,
            }
            print(f"Sending message to LLM: {message}")
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[message],
            )
            print(f"LLM response: {response.choices[0].message.content.strip()}\n")
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Failed to send message to LLM: {e}")

    def feed_context_to_llm(self, context):
        self.send_message_to_llm(context, "system")

    def send_instruction_to_llm(self, instruction):
        self.send_message_to_llm(instruction, "user")

    def load_webpage(self, url):
        print("Loading webpage...")
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        page_title = self.driver.title
        print(f"Webpage loaded. Title: '{page_title}'")

    def continuously_check_elements(self, url):
        self.setup_webdriver()
        self.load_webpage(url)
        try:
            while True:
                self.check_and_interact_with_elements()
                time.sleep(5)
        except KeyboardInterrupt:
            print("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()

    def check_and_interact_with_elements(self, retry_count=0):
        try:
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            print(f"Page text: {page_text}")
            self.find_and_log_elements('//input', 'input field(s)')
            self.find_and_click_first_button()
        except (StaleElementReferenceException, WebDriverException) as e:
            self.handle_exceptions(e, retry_count)

    def find_and_log_elements(self, xpath, element_type):
        elements = self.driver.find_elements(By.XPATH, xpath)
        if elements:
            print(f"Found {len(elements)} {element_type}:")
            for element in elements:
                print(f" - Type: {element.get_attribute('type')}, Name: {element.get_attribute('name')}")

    def find_and_click_first_button(self):
        buttons_xpath = '//button | //input[@type="button"] | //input[@type="submit"]'
        buttons = self.driver.find_elements(By.XPATH, buttons_xpath)
        if buttons:
            print(f"Found {len(buttons)} button(s):")
            first_button = buttons[0]
            first_button.click()
            print("Clicked on the first button found.")

    def handle_exceptions(self, exception, retry_count):
        print(f"Exception encountered: {exception}. Retry count: {retry_count}")
        if retry_count < 3:
            print("Retrying...")
            time.sleep(2)
            self.check_and_interact_with_elements(retry_count + 1)
        else:
            print("Maximum retries reached. Moving on.")

    def close_browser(self):
        print("Closing the browser...")
        self.driver.quit()

if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = 'http://localhost:8080/voting/2/j8hr8z9hxu27f1p3wb63nqkzl8eifvmivu4p9apnxfdp4gkasvxjngp1q16lpyx0'

    initial_prompt = read_text_from_file('../../config/initial_prompt.txt')
    print(f"Initial prompt: {initial_prompt}")

    web_interaction = WebInteraction(driver_path, initial_prompt=initial_prompt)
    web_interaction.continuously_check_elements(url)
