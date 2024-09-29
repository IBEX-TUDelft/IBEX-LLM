import re
import websocket
from WebSocketClient import WebSocketClient



def parse_url(url):
    """
    Parse the URL to extract the hostname, gameId and recovery token.
    :param url: The URL to parse.
    :return: A tuple containing the hostname, gameId and recovery token.
    """
    # Regex to accommodate both http and https and multiple endpoint segments
    match = re.search(r'https?://([^/]+)/(\w+)/(\d+)/([\w-]+)', url)
    if match:
        hostname = match.group(1)
        endpoint = match.group(2)
        game_id = int(match.group(3))
        recovery = match.group(4)
        return hostname, endpoint, game_id, recovery
    else:
        raise ValueError("URL format is incorrect. Expected format: http://<hostname>/<endpoint>/<gameId>/<recovery>")

if __name__ == "__main__":
    websocket.enableTrace(False)
    url_input = input("Enter the URL: ")
    try:
        hostname, endpoint, game_id, recovery = parse_url(url_input)
        # Replace the existing port number with 3088
        hostname = re.sub(r':\d+', '', hostname)
        client = WebSocketClient(f"ws://{hostname}:3088/{endpoint}", game_id, recovery)
        client.run_forever()
    except ValueError as e:
        print(e)
