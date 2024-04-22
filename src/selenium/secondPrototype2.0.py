import time
import openai
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException


"""
TODO:
- Adjust prompting so that it does not do anything with chat functionalities
- Overlays and Popups are a problem, the agent should be able to handle them
"""

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
            print(f"Failed to send message to LLM: {str(e)}")

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
                time.sleep(
                    5)  # Adjust timing as necessary based on the application's needs
        except KeyboardInterrupt:
            print("Program interrupted by user. Exiting...")
        finally:
            self.close_browser()

    def check_and_interact_with_elements(self, retry_count=0):
        try:
            role = "user"
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            elements_text = ""

            # self.handle_overlays()  # New function to handle overlays

            input_fields_text, input_elements = self.find_and_interact_input_field(
                '//input', 'input field(s)')
            if input_fields_text:
                elements_text += "\n" + input_fields_text

            buttons_text, buttons = self.find_and_interact_with_buttons(
                '//button | //input[@type="button"] | //input[@type="submit"]')
            if buttons_text:
                elements_text += "\n" + buttons_text

            combined_text = f"Page text: {page_text}{elements_text}"
            # print(combined_text)
            response = self.send_message_to_llm(combined_text, role)

            if response:
                extracted_compensation, extracted_buttons = self.extract_information_from_response(response)
                print(f"Extracted input elements: {extracted_compensation}")
                print(f"Extracted button instructions: {extracted_buttons}")
                self.process_ai_instructions(input_elements, buttons, extracted_compensation, extracted_buttons)

        except (StaleElementReferenceException, WebDriverException) as e:
            self.handle_exceptions(e, retry_count)

    def find_and_interact_input_field(self, xpath, element_type):
        elements = self.driver.find_elements(By.XPATH, xpath)
        if elements:
            message_content = f"Found {len(elements)} {element_type}(s):\n"
            for index, element in enumerate(elements, start=1):
                message_content += f"{index}. {element.get_attribute('type')} - {element.get_attribute('name')}\n"

            action = read_text_from_file('../../prompts/input_prompt.txt')
            message_content += action

            return message_content, elements
        else:
            # Return an empty string and an empty list if no elements are found
            return "", []

    def find_and_interact_with_buttons(self, xpath):
        buttons = self.driver.find_elements(By.XPATH, xpath)
        message_content = ""  # Initialize message content regardless of button count

        if buttons:
            if len(buttons) == 1:
                buttons[0].click()
                return "", []
            else:
                message_content = f"Found {len(buttons)} button(s):\n"
                for index, button in enumerate(buttons, start=1):
                    button_details = {
                        'type': button.get_attribute('type'),
                        'name': button.get_attribute('name'),
                        'value': button.get_attribute('value'),
                        'text': button.text or button.get_attribute(
                            'innerText')
                    }
                    message_content += f"{index}. Type: {button_details['type']}, Name: {button_details['name']}, Value: {button_details['value']}, Text: '{button_details['text']}'\n"
                print(message_content)
                # Optionally add additional prompts or actions if needed
                action = read_text_from_file('../../prompts/button_prompt.txt')
                message_content += action
        else:
            message_content = "No buttons found."

        return message_content, buttons  # Ensure this is outside the 'else' clause

    def process_ai_instructions(self, input_elements, buttons,
                                extracted_compensation, extracted_buttons):
        if extracted_compensation:
            try:
                amount = extracted_compensation.get('Compensation')
                if input_elements and amount:
                    input_elements[0].send_keys(amount)
                    print(f"Provided compensation amount: {amount}")
            except Exception as e:
                print(f"Error processing compensation input: {str(e)}")

        if extracted_buttons:
            for button_index in extracted_buttons:
                if buttons and 0 <= button_index - 1 < len(buttons):
                    try:
                        print(f"Trying to click Button [{button_index}]...")
                        buttons[button_index - 1].click()
                        print(
                            f"Clicked Button [{button_index}] as instructed.")
                        time.sleep(1)  # Pause for a second after clicking.
                    except Exception as e:
                        # Print just the error message without the stack trace.
                        print(
                            f"Error processing button press instructions: {str(e)}")
                        self.handle_overlays()
                        # TODO: retry_interaction() so that the agent tries the button that failed again

    def handle_overlays(self):
        """
        TODO: Check this thoroughly to make sure it works as expected
        Error processing button press instructions: Message: element click intercepted: Element <button type="button" class="btn mb-1 btn-primary btn-sm btn-block">..
        .</button> is not clickable at point (769, 140). Other element would receive the click: <div data-vm-wrapper-id="vm-8" tabindex="-1"
        role="dialog" aria-label="Check Your Messages" aria-modal="true" aria-describedby="vm-8-content" aria-labelledby="vm-8-title"
        class="vm-wrapper" style="z-index: 1051; cursor: pointer;">...</div>

        TODO: We should not close the overlay but again go through the buttons and click the correct one,
        TODO: So we want to loop through the buttons again and click the correct one
        Clicked on overlay: Check Your Messages
        message-empty-description"
        Ok
        Overlay closed.
        Trying to click Button [3]...
        Clicked Button [3] as instructed.
        """
        overlay_selectors = [
            ".submit-button",  # Submit buttons commonly used in modals
            "div[role='dialog']"  # Typical selector for modals
        ]
        for selector in overlay_selectors:
            overlays = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for overlay in overlays:
                try:
                    if overlay.is_displayed():
                        # we want to loop over all the button elements in the overlay
                        # and we want to press the button that makes sense
                        for button in overlay.find_elements(By.TAG_NAME, 'button'):
                            button.click()
                            print(f"Clicked on overlay: {overlay.get_attribute('aria-label')}")
                            print(f"Button text: {button.text}")
                except Exception as e:
                    print(f"Failed to close overlay: {str(e)}")

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


    def extract_information_from_response(self, response):
        """
        Parses the LLM response to extract compensation amounts and button pressing instructions.
        """
        input_elements = {}
        button_instructions = []

        # Extract compensation amount
        compensation_match = re.search(r"Compensation:\s*([\d,]+)", response)
        if compensation_match:
            compensation = compensation_match.group(1).replace(',', '').strip()
            input_elements['Compensation'] = compensation

        # Extract button press instructions
        button_matches = re.findall(r"Button \[([0-9, ]+)\]", response)
        for match in button_matches:
            buttons = [int(num.strip()) for num in match.split(',')]
            button_instructions.extend(buttons)

        return input_elements, button_instructions


if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'
    url = input("Enter the URL to load: ")
    initial_prompt = read_text_from_file('../../prompts/initial_prompt.txt')
    web_interaction = WebInteraction(driver_path, initial_prompt=initial_prompt)
    web_interaction.continuously_check_elements(url)

