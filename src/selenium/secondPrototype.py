import time
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
import sys
from webInteractor import WebInteraction


def read_text_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

class AdvancedWebInteraction(WebInteraction):
    def check_and_interact_with_elements(self, retry_count=0):
        try:
            role = "user"
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            elements_text = ""

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
                self.process_ai_instructions(response, input_elements, buttons)

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
            return "", []

    def find_and_interact_with_buttons(self, xpath):
        buttons = self.driver.find_elements(By.XPATH, xpath)

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

                # Optionally add additional prompts or actions if needed
                action = read_text_from_file('../../prompts/button_prompt.txt')
                message_content += action
        else:
            message_content = "No buttons found."

        return message_content, buttons  # Ensure this is outside the 'else' clause

    def process_ai_instructions(self, response, input_elements, buttons):
        if "Compensation" in response:
            try:
                amount = re.sub("[^0-9]", "", response)
                if input_elements and amount:
                    input_elements[0].send_keys(amount)
                    print(f"Provided compensation amount: {amount}")
                    if buttons:
                        buttons[0].click()
                        print(
                            "Submitted compensation amount by pressing Button [1]")
                        # Re-fetch buttons as the page state may have changed
                        time.sleep(1)  # Small delay to allow page update
                        buttons = self.find_and_interact_with_buttons(
                            '//button | //input[@type="button"] | //input[@type="submit"]')
            except Exception as e:
                print(f"Error processing compensation input: {e}")

        if "Button" in response:
            try:
                button_index = int(re.sub("[^0-9]", "", response))
                # Adjust for zero-based index since user instructions assume a one-based index
                if buttons and 0 <= button_index - 1 < len(buttons):
                    buttons[button_index - 1].click()
                    print(f"Clicked Button [{button_index}] as instructed.")
                    # Re-fetch buttons again here if you expect more changes after this click
                    time.sleep(1)  # Small delay to allow page update
                    buttons = self.find_and_interact_with_buttons(
                        '//button | //input[@type="button"] | //input[@type="submit"]')
            except ValueError:
                print("Invalid button number received in AI response.")
            except Exception as e:
                print(f"Error processing button press instructions: {e}")



if __name__ == "__main__":
    driver_path = '/opt/homebrew/bin/chromedriver'

    if len(sys.argv) < 2:  # Check if the URL is provided as a command line argument
        print("Usage: python script_name.py <URL>")
        sys.exit(1)  # Exit the script if no URL is provided

    url = sys.argv[1]  # Get the URL from the first command line argument

    initial_prompt = read_text_from_file('../../prompts/initial_prompt.txt')

    web_interaction = WebInteraction(driver_path,
                                     initial_prompt=initial_prompt)
    web_interaction.continuously_check_elements(url)

