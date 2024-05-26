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
        openai.api_key = self.load_api_key()
        if self.initial_prompt:
            self.send_message_to_llm(self.initial_prompt, "user", is_initial=True)

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
            print(f"LLM response: {response.choices[0].message.content.strip()}\n")
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
            # Retrieving the basic text from the page
            role = "user"
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            elements_text = ""  # Initialize an empty string to append additional elements' text

            # Finding and interacting with input fields
            input_fields_text, elements = self.find_and_interact_input_field('//input',
                                                                   'input field(s)')
            if input_fields_text:
                role = "user"
                elements_text += "\n" + input_fields_text

            # Finding and clicking the first button, also getting the text about the buttons
            # buttons_text = self.find_and_click_first_button()
            # if buttons_text:
            #     elements_text += "\n" + buttons_text  # Append buttons info if any

            # Combining the page text with elements text
            combined_text = f"Page text: {page_text}{elements_text}"
            # print(combined_text)  # Logging the combined text
            response = self.send_message_to_llm(combined_text, role)

            if response and "Compensation" in response and elements:
                try:
                    amount = re.sub("[^0-9]", "", response)
                    if elements and amount:
                        elements[0].send_keys(amount)
                        print(f"Provided compensation amount: {amount}")
                        self.find_and_click_nth_button(0)
                        self.find_and_click_nth_button(2)
                except Exception as e:
                    print(f"Error processing compensation amount: {e}")

            self.find_and_click_nth_button()



        except (StaleElementReferenceException, WebDriverException) as e:
            self.handle_exceptions(e, retry_count)

    def find_and_interact_input_field(self, xpath, element_type):
        elements = self.driver.find_elements(By.XPATH, xpath)
        if elements:
            message_content = f"Found {len(elements)} {element_type}(s):\n"
            for index, element in enumerate(elements, start=1):
                message_content += f"{index}. {element.get_attribute('type')} - {element.get_attribute('name')}\n"

            action = read_text_from_file('../prompts/input_prompt.txt')
            message_content += action

            return message_content, elements
        else:
            # Return an empty string and an empty list if no elements are found
            return "", []

    def find_and_click_nth_button(self, button_nr=0):
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
            buttons[button_nr].click()
            print("Clicked on the first button found.")
            return message_content + "Clicked on the first button found."


    def handle_exceptions(self, exception, retry_count, verbose=False):
        if verbose:
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
    url = input("Enter the URL to load: ")

    initial_prompt = read_text_from_file('../prompts/initial_prompt.txt')
    print(f"Initial prompt: {initial_prompt}")

    web_interaction = WebInteraction(driver_path, initial_prompt=initial_prompt)
    web_interaction.continuously_check_elements(url)
