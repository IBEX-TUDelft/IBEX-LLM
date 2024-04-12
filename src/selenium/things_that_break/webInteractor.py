import logging
import time
import openai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_text_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

class CustomLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = kwargs.get('role', 'user')  # Default role is 'user'

class CustomLogger(logging.getLoggerClass()):
    def makeRecord(self, *args, **kwargs):
        rv = CustomLogRecord(*args, **kwargs)
        return rv


class LLMLoggingHandler(logging.Handler):
    def __init__(self, web_interaction_instance):
        super().__init__()
        self.web_interaction_instance = web_interaction_instance

    def emit(self, record):
        log_entry = self.format(record)
        role = getattr(record, 'role', 'user')  # Fallback to 'user' if role isn't specified
        self.web_interaction_instance.send_message_to_llm({"role": role, "content": log_entry})



class WebInteraction:
    def __init__(self, driver_path, browser='chrome', initial_prompt=None):
        self.driver_path = driver_path
        self.driver = None
        self.browser = browser
        openai.api_key = self.load_api_key()
        self.initial_prompt = initial_prompt

        # Initialize logger for WebInteraction
        self.logger = logging.getLogger(__name__)
        llm_handler = LLMLoggingHandler(self)
        llm_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        llm_handler.setFormatter(formatter)
        self.logger.addHandler(llm_handler)
        self.logger.setLevel(logging.INFO)

        if initial_prompt:
            self.send_message_to_llm({"role": "user", "system": initial_prompt}, is_initial=True)



    def load_api_key(self):
        try:
            print("Loading API key...")
            with open('../../../config/token.txt',
                      'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print("API key file not found. Please check the file path.")
            exit()

    def setup_webdriver(self):
        if self.browser.lower() == 'chrome':
            service = Service(executable_path=self.driver_path)
            self.driver = webdriver.Chrome(service=service)
        # Add elif statements for other browsers if needed
        else:
            self.logger.error(f"Browser '{self.browser}' is not supported.")
            return

    def send_message_to_llm(self, message, is_initial=False):
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[message],
            )
            print(f"LLM response: {response.choices[0].message.content.strip()}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Failed to send message to LLM: {e}")

    def feed_context_to_llm(self, context):
        llm_input = {"role": "system", "content": context}
        # Simulate processing the context by the LLM
        print(f"Context fed to LLM: {llm_input}")
        # Simulated LLM response
        return llm_input

    def send_instruction_to_llm(self, instruction):
        llm_input = {"role": "user", "content": instruction}
        # Simulate processing the instruction by the LLM
        print(f"Instruction sent to LLM: {llm_input}")
        # Simulated LLM response to the instruction
        return llm_input


    def load_webpage(self, url):
        self.logger.info("Loading webpage...")
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Wait for the body to load
        page_title = self.driver.title
        self.logger.info(f"Webpage loaded. Title: '{page_title}'")

    def continuously_check_elements(self, url):
        self.setup_webdriver()
        self.load_webpage(url)

        try:
            while True:
                self.check_and_interact_with_elements()
                time.sleep(5)  # Wait for 5 seconds before checking again
        except KeyboardInterrupt:
            self.logger.info("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()

    def check_and_interact_with_elements(self, retry_count=0):
        try:
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            self.logger.info(f"Page text: {page_text}")
            self.find_and_log_elements('//input', 'input field(s)')
            self.find_and_click_first_button()
        except (StaleElementReferenceException, WebDriverException) as e:
            self.handle_exceptions(e, retry_count)

    def find_and_log_elements(self, xpath, element_type):
        elements = self.driver.find_elements(By.XPATH, xpath)
        if elements:
            self.logger.info(f"Found {len(elements)} {element_type}:")
            for element in elements:
                self.logger.info(f" - Type: {element.get_attribute('type')}, Name: {element.get_attribute('name')}")

    def find_and_click_first_button(self):
        buttons_xpath = '//button | //input[@type="button"] | //input[@type="submit"]'
        buttons = self.driver.find_elements(By.XPATH, buttons_xpath)
        if buttons:
            self.logger.info(f"Found {len(buttons)} button(s):")
            first_button = buttons[0]
            first_button.click()
            # self.logger.info("Action: Clicked on the first button found.")

    def handle_exceptions(self, exception, retry_count):
        logging.warning(f"{type(exception).__name__} caught: {exception}. Retrying...")
        if retry_count < 3:
            self.driver.refresh()
            self.check_and_interact_with_elements(retry_count + 1)

    def close_browser(self):
        self.logger.info("Closing the browser...")
        self.driver.quit()


if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = 'http://localhost:8080/voting/15/tvkjdsqk0wt7bp9oalfeg428f8s8gleujijaqjgjkee9i25nrdi06x66a1zw73m0'

    initial_prompt = read_text_from_file('../../../prompts/initial_prompt.txt')
    print(f"Initial prompt: {initial_prompt}")

    web_interaction = WebInteraction(driver_path, initial_prompt=initial_prompt)
    web_interaction.continuously_check_elements(url)

