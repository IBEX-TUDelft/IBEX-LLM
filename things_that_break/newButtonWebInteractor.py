import time
import openai
import re

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
        self.buttons = []
        self.input_elements = []
        self.response = None

        openai.api_key = self.load_api_key()
        self.setup_webdriver()
        if self.initial_prompt:
            self.send_message_to_llm(self.initial_prompt, "system", is_initial=True)


    def check_and_interact_with_elements(self):
        try:
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            elements_text = f"Page text: {page_text}\n"

            self.find_and_interact_input_field('//input', 'input field(s)')
            button_action = self.find_buttons()

            if button_action != "Only one button found and clicked.":
                # Compose message for LLM based on elements found
                elements_text += self.compose_elements_text()
                print(elements_text)  # Logging
                self.send_message_to_llm(elements_text, "user")  # Execution now waits for LLM response

        except (StaleElementReferenceException, WebDriverException) as e:
            # print(f"Exception encountered: {e}")
            pass

    def compose_elements_text(self):
        elements_text = "Action Required:"

        # Include details about input fields
        if self.input_elements:
            elements_text += "\nFound input fields:\n"
            for index, element in enumerate(self.input_elements, start=1):
                element_type = element.get_attribute('type')
                element_name = element.get_attribute('name')
                elements_text += f"{index}. Type: {element_type}, Name: {element_name}\n"

        # Include details about buttons
        if self.buttons:
            elements_text += "\nFound buttons:\n"
            for index, button in enumerate(self.buttons, start=1):
                button_text = button.text or button.get_attribute(
                    'innerText') or "No text"
                elements_text += f"{index}. '{button_text}'\n"

        return elements_text

    def find_and_interact_input_field(self, xpath, element_type):
        # Find elements based on the provided xpath and update the class attribute
        self.input_elements = self.driver.find_elements(By.XPATH, xpath)
        if self.input_elements:
            message_content = f"Found {len(self.input_elements)} {element_type}(s):\n"
            for index, element in enumerate(self.input_elements, start=1):
                message_content += f"{index}. Type: {element.get_attribute('type')}, Name: {element.get_attribute('name')}\n"
            return message_content
        else:
            return "No input fields found."

    def find_buttons(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH,
                                                 '//button | //input[@type="button"] | //input[@type="submit"]')))
        self.buttons = self.driver.find_elements(By.XPATH,
                                                 '//button | //input[@type="button"] | //input[@type="submit"]')
        if len(self.buttons) == 1:
            # If only one button is found, click it and skip LLM messaging
            self.buttons[0].click()
            print("Only one button found and clicked: ",
                  self.buttons[0].get_attribute('innerText') or "No text")
            return "Only one button found and clicked."
        elif len(self.buttons) > 1:
            # If more than one button is found, prepare the message for LLM decision
            message_content = f"Found {len(self.buttons)} button(s):\n"
            for index, button in enumerate(self.buttons, start=1):
                button_details = {
                    'type': button.get_attribute('type'),
                    'name': button.get_attribute('name'),
                    'value': button.get_attribute('value'),
                    'text': button.text or button.get_attribute(
                        'innerText') or "No text"
                }
                message_content += f"{index}. Type: {button_details['type']}, Name: {button_details['name']}, Value: {button_details['value']}, Text: '{button_details['text']}'\n"
            print(message_content)
            return message_content
        else:
            # If no buttons are found, log this status
            print("No buttons found.")
            return "No buttons found."

    def execute_llm_decisions(self):
        # Assuming self.response contains the LLM's response
        if not self.response:
            print("No response from LLM to execute.")
            return

        # Parse the response to find actions. This is simplified; you might need a more robust parser.
        lines = self.response.split('\n')
        for line in lines:
            if line.startswith("Button:"):
                button_index = int(line.split(':')[
                                       1].strip()) - 1  # Adjusting for zero-based indexing
                if 0 <= button_index < len(self.buttons):
                    self.buttons[button_index].click()
                    print(f"Clicked on button number {button_index + 1}.")
                else:
                    print(f"Button index {button_index + 1} out of range.")

            elif line.startswith("Input:"):
                parts = line.split(',')
                input_index = int(parts[0].split(':')[1].strip()) - 1
                value = parts[1].split(':')[1].strip()
                if 0 <= input_index < len(self.input_elements):
                    self.input_elements[input_index].send_keys(value)
                    print(
                        f"Filled input number {input_index + 1} with value '{value}'.")
                else:
                    print(f"Input index {input_index + 1} out of range.")

            elif line.startswith("Compensation:"):
                # Assuming there's a specific input field for compensation you want to target
                compensation_value = line.split(':')[1].strip()
                # This is an example; you'd need to know which input is for compensation.
                for input_element in self.input_elements:
                    if 'compensation' in input_element.get_attribute(
                            'name').lower():
                        input_element.send_keys(compensation_value)
                        print(f"Set compensation to {compensation_value}.")
                        break
                else:
                    print("No compensation input field found.")


    def load_api_key(self):
        try:
            with open('../config/token.txt', 'r') as file:
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
            self.response = response.choices[0].message.content.strip()
            print(f"LLM response: {self.response}\n")

            self.execute_llm_decisions()
        except Exception as e:
            print(f"Failed to send message to LLM: {e}")

    def continuously_check_elements(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        try:
            while True:
                self.check_and_interact_with_elements()
                time.sleep(5)  # Adjust timing based on page state and LLM response time
        except KeyboardInterrupt:
            print("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()





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
    # url = 'http://localhost:8080/voting/5/7ftois3yqvp7kojcx2oflvzoqdigksnhnin5mtfkw48u48yt2n5bw49v6p1rhak0'
    url = input("Enter the URL to load: ")
    initial_prompt = read_text_from_file('../prompts/initial_prompt.txt')
    print(f"Initial prompt: {initial_prompt}")

    web_interaction = WebInteraction(driver_path, initial_prompt=initial_prompt)
    web_interaction.continuously_check_elements(url)
