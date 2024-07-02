import re
import websocket
from WebSocketClient import WebSocketClient

def parse_url(url):
    """
    Parse the URL to extract the hostname, gameId and recovery token.
    :param url: The URL to parse.
    :return: A tuple containing the hostname, gameId and recovery token.
    """
    # Regex to work for different simulations like voting, market, etc.
    match = re.search(r'http://(.+?)/voting/(\d+)/([\w-]+)', url)
    if match:
        hostname = match.group(1)
        game_id = int(match.group(2))
        recovery = match.group(3)
        return hostname, game_id, recovery
    else:
        raise ValueError("URL format is incorrect. Expected format: http://<hostname>/<endpoint>/<gameId>/<recovery>")

if __name__ == "__main__":
    websocket.enableTrace(False)
    url_input = input("Enter the URL: ")
    try:
        hostname, game_id, recovery = parse_url(url_input)
        hostname = re.sub(r':\d+', ':3088', hostname)
        client = WebSocketClient(f"ws://{hostname}", game_id, recovery)
        client.run_forever()
    except ValueError as e:
        print(e)
