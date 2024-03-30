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
            self.send_message_to_llm(self.initial_prompt, "system", is_initial=True)

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
            # response = openai.chat.completions.create(
            #     model="gpt-3.5-turbo",
            #     messages=[message],
            # )
            # print(f"LLM response: {response.choices[0].message.content.strip()}\n")
            # return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Failed to send message to LLM: {e}")

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
            self.send_message_to_llm(page_text, "system")
            self.find_and_interact_input_field('//input', 'input field(s)')
            self.find_and_click_first_button()
        except (StaleElementReferenceException, WebDriverException) as e:
            self.handle_exceptions(e, retry_count)

    def find_and_interact_input_field(self, xpath, element_type):
        elements = self.driver.find_elements(By.XPATH, xpath)
        if elements:
            message_content = f"Found {len(elements)} {element_type}(s):\n"
            for index, element in enumerate(elements, start=1):
                message_content += f"{index}. {element.get_attribute('type')} - {element.get_attribute('name')}\n"

            action = ("Whenever you encounter an input field related to compensation requests (e.g., 'player_compensation_1'), you should provide a reasonable compensation amount. Given the context of the game and the information available, such as project impacts and value ranges, determine a suitable compensation figure."
                      "For providing a compensation figure, format your response as 'Compensation: [Amount]', where [Amount] is the figure you suggest based on the economic conditions and strategic objectives outlined. Remember, the compensation should reflect the value impacts and ranges discussed.)"
                      "If the action involves other types of input fields not related to compensation, specify the appropriate action based on the field's purpose.")
            message_content += action
            # Log the compiled message
            print(message_content)
            # Send the compiled message to the LLM in a single action
            response = self.send_message_to_llm(message_content, "user")

            # if response has a digit, then it is a compensation amount
            # remove all the non-digit characters from the response and just want to pass it to the input field that we encountered




    def find_and_click_first_button(self):
        buttons_xpath = '//button | //input[@type="button"] | //input[@type="submit"]'
        buttons = self.driver.find_elements(By.XPATH, buttons_xpath)
        if buttons:
            message_content = f"Found {len(buttons)} button(s):\n"
            # Collect details of all buttons found for the message
            for index, button in enumerate(buttons, start=1):
                button_details = {
                    'type': button.get_attribute('type'),
                    'name': button.get_attribute('name'),
                    'value': button.get_attribute('value'),
                    'text': button.text or button.get_attribute('innerText')
                }
                message_content += f"{index}. Type: {button_details['type']}, Name: {button_details['name']}, Value: {button_details['value']}, Text: '{button_details['text']}'\n"

            # Log the compiled message about buttons
            print(message_content[
                  :-1])  # Remove the last newline for cleaner logging
            # No need to send to LLM here since we're directly interacting rather than logging

            # Clicking on the first button
            buttons[0].click()
            print("Clicked on the first button found.")

    def handle_exceptions(self, exception, retry_count):
        # print(f"Exception encountered: {exception}. Retry count: {retry_count}")
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
    url = 'http://localhost:8080/voting/4/x349oh5lz9wbukg04lx8hnkwzj7r7ez27v1v4bmysdm89xwym6ynmw26bakmk7m0'

    initial_prompt = read_text_from_file('../../config/initial_prompt.txt')
    print(f"Initial prompt: {initial_prompt}")

    web_interaction = WebInteraction(driver_path, initial_prompt=initial_prompt)
    web_interaction.continuously_check_elements(url)
