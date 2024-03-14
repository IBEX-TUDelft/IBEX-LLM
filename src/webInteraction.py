import anthropic

def load_api_key():
    """
    Load the API key from an external file.
    """
    try:
        with open('../config/claude-token.txt',
                  'r') as file:  # Update the path to your actual file location
            return file.read().strip()
    except FileNotFoundError:
        print("API key file not found. Please check the file path.")
        exit()

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=load_api_key()
)

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "You are an intelligent agent participating in a simulation. Wait for instructions."
                }
            ]
        }
    ]
)

print(message.content)