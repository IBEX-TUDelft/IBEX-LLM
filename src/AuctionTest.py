from GameHandlerAuction_Beta import GameHandler
import time

# Initialize the GameHandler
handler = GameHandler(game_id=308, verbose=True)

# Define the example messages
messages = [
    '{"type":"event","eventType":"player-joined","data":{"authority":"admin","number":0,"shares":1,"cash":100,"wallet":{"balance":100,"shares":1},"gameId":305,"role":0}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":1,"sender":1,"price":5,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":2,"sender":1,"price":5,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":1,"price":5,"buyerFee":0,"sellerFee":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":2,"type":"bid"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":3,"sender":2,"price":3,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":2,"price":3,"buyerFee":0,"sellerFee":0,"median":4}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":3,"type":"bid"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":4,"sender":1,"price":4,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":2,"price":5,"buyerFee":0,"sellerFee":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":1,"type":"ask"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":1,"price":4,"buyerFee":0,"sellerFee":0,"median":4.5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":4,"type":"bid"}}}'
]

# Feed the messages to the GameHandler
for message in messages:
    handler.receive_message(message)
    time.sleep(1)  # Simulate some delay between receiving messages

# Allow enough time for the dispatch to occur
time.sleep(10)

# Stop the dispatcher after testing
handler.stop_dispatcher()