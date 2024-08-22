from GameHandlerAuction_Beta2 import GameHandler
import time

# Initialize the GameHandler
handler = GameHandler(game_id=308, verbose=True)

# Define the extended set of example messages
messages = [
    # Player joins
    '{"type":"event","eventType":"player-joined","data":{"authority":"admin","number":0,"shares":1,"cash":100,"wallet":{"balance":100,"shares":1},"gameId":308,"role":0}}',

    # Basic add-order events
    '{"type":"event","eventType":"add-order","data":{"order":{"id":1,"sender":0,"price":10,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":2,"sender":1,"price":10,"quantity":1,"type":"bid"}}}',

    # Contract fulfillment event
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":10,"buyerFee":0.5,"sellerFee":0.5,"median":10}}',

    # Test partial order fulfillment
    '{"type":"event","eventType":"add-order","data":{"order":{"id":3,"sender":1,"price":8,"quantity":2,"type":"bid"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":4,"sender":0,"price":8,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":8,"buyerFee":0.4,"sellerFee":0.4,"median":8}}',

    # Cancel unfulfilled orders
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":3,"type":"bid"}}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":4,"type":"ask"}}}',

    # Test a mismatch in order types and ensure no contract is fulfilled
    '{"type":"event","eventType":"add-order","data":{"order":{"id":5,"sender":0,"price":15,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":6,"sender":1,"price":14,"quantity":1,"type":"bid"}}}',

    # Test a higher bid than ask and ensure correct fulfillment
    '{"type":"event","eventType":"add-order","data":{"order":{"id":7,"sender":1,"price":16,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":0,"to":1,"price":15,"buyerFee":0.3,"sellerFee":0.3,"median":14.5}}',

    # Test multiple order types simultaneously
    '{"type":"event","eventType":"add-order","data":{"order":{"id":8,"sender":0,"price":12,"quantity":2,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":9,"sender":1,"price":12,"quantity":2,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":12,"buyerFee":0.6,"sellerFee":0.6,"median":12}}',

    # Add order with the same price as fulfilled one
    '{"type":"event","eventType":"add-order","data":{"order":{"id":10,"sender":0,"price":12,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":11,"sender":1,"price":12,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":12,"buyerFee":0.6,"sellerFee":0.6,"median":12}}',

    # Test order cancellation just before fulfillment
    '{"type":"event","eventType":"add-order","data":{"order":{"id":12,"sender":0,"price":9,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":13,"sender":1,"price":9,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":12,"type":"ask"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":9,"buyerFee":0.45,"sellerFee":0.45,"median":9}}',

    # Test complex order interactions
    '{"type":"event","eventType":"add-order","data":{"order":{"id":14,"sender":0,"price":7,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":15,"sender":1,"price":7,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":16,"sender":0,"price":6,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":7,"buyerFee":0.35,"sellerFee":0.35,"median":7}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":6,"buyerFee":0.3,"sellerFee":0.3,"median":6.5}}',

    # Test extreme edge cases (e.g., very high or low prices)
    '{"type":"event","eventType":"add-order","data":{"order":{"id":17,"sender":0,"price":1000,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":18,"sender":1,"price":1000,"quantity":1,"type":"bid"}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":1,"to":0,"price":1000,"buyerFee":50,"sellerFee":50,"median":1000}}',

    # Handling of invalid or malformed messages (should be ignored or logged as errors)
    '{"type":"event","eventType":"add-order","data":{"order":{"id":19,"sender":null,"price":null,"quantity":1,"type":"ask"}}}',
    '{"type":"event","eventType":"invalid-event-type","data":{"some_invalid_data":"value"}}'
]

# Feed the messages to the GameHandler
for message in messages:
    handler.receive_message(message)
    time.sleep(1)  # Simulate some delay between receiving messages

# Allow enough time for the dispatch to occur
time.sleep(10)

# Stop the dispatcher after testing
handler.stop_dispatcher()
