from GameHandlerHarberger import GameHandler  # Adjust the import as necessary
import time

# Initialize the GameHandler
handler = GameHandler(game_id=308, verbose=True)

# Define the example messages
messages = [
    '{"type":"event","eventType":"assign-name","data":{"name":"Tan","number":1,"ruleset":"Harberger"}}',
    '{"type":"event","eventType":"phase-instructions","data":{}}',
    '{"type":"info","message":"Player 1 rejoined the game"}',
    '{"type":"event","eventType":"ready-received","data":{}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723797949162}}',
    '{"type":"event","eventType":"assign-role","data":{"role":3,"wallet":[{"balance":60000,"shares":6,"cashForSniping":250000},{"balance":60000,"shares":6,"cashForSniping":250000},{"balance":60000,"shares":6,"cashForSniping":250000}],"property":{"id":1,"owner":1,"name":"Mathematical Antlion Lot","v":[468000,164000,150000]},"boundaries":{"developer":{"noProject":{"low":200000,"high":500000},"projectA":{"low":500000,"high":2750000}},"owner":{"noProject":{"low":350000,"high":600000},"projectA":{"low":150000,"high":350000}}},"taxRate":1,"initialTaxRate":1,"finalTaxRate":33,"conditions":[{"name":"No Project","id":0,"parameter":"no_project","key":"noProject"},{"name":"Project","id":1,"parameter":"project_a","key":"projectA"}]}}',
    '{"type":"event","eventType":"players-known","data":{"players":[{"number":1,"role":3,"tag":"Owner 1"},{"number":2,"role":2,"tag":"Developer"},{"number":3,"role":1,"tag":"Speculator 1"},{"number":4,"role":1,"tag":"Speculator 2"}]}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":1}}',
    '{"type":"notice","message":"Phase 1 has begun."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723797964178}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":2}}',
    '{"type":"notice","message":"Phase 2 has begun."}',
    '{"type":"info","message":"Player Gray submitted a declaration of values."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723797979192}}',
    '{"type":"event","eventType":"declarations-published","data":{"declarations":[{"id":1,"name":"Mathematical Antlion Lot","owner":"Tan","role":3,"number":1,"d":[350000,150000],"available":[true,true,true]},{"id":2,"name":"Mechanical Mite Lot","owner":"Gray","role":2,"number":2,"d":[3,4,0],"available":[true,true,true]}],"winningCondition":0}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":3}}',
    '{"type":"notice","message":"Phase 3 has begun."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723797994209}}',
    '{"type":"info","message":"Reconciliation in progress ..."}',
    '{"type":"event","eventType":"profit","data":{"round":0,"phase":4,"property":1,"condition":0,"value":468000,"declaration":350000,"sniped":false,"speculator":null,"snipeProfit":0,"taxes":3500,"owner":1,"role":3,"total":464500}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":4}}',
    '{"type":"notice","message":"Phase 4 has begun."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"first-snipes","data":{"snipes":[]}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723798009221}}',
    '{"type":"event","eventType":"value-signals","data":{"signals":[8623,6734,0],"publicSignal":[1155.0099,0,0],"condition":0,"taxRate":33}}',
    '{"type":"info","message":"Prepare for the trading phase"}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":5}}',
    '{"type":"notice","message":"Phase 5 has begun."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723798039236}}',
    '{"type":"info","message":"The trading phase has started"}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":6}}',
    '{"type":"notice","message":"Phase 6 has begun."}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":1,"sender":2,"price":5,"quantity":1,"type":"ask","condition":0}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":2,"sender":2,"price":5,"quantity":1,"type":"bid","condition":0}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":4,"to":2,"price":5,"condition":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":2,"type":"bid","condition":0}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":4,"price":5,"condition":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":1,"type":"ask","condition":0}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":3,"sender":3,"price":5,"quantity":1,"type":"ask","condition":0}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":4,"sender":3,"price":5,"quantity":1,"type":"bid","condition":0}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":3,"to":2,"price":5,"condition":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":3,"type":"ask","condition":0}}}',
    '{"type":"event","eventType":"contract-fulfilled","data":{"from":2,"to":3,"price":5,"condition":0,"median":5}}',
    '{"type":"event","eventType":"delete-order","data":{"order":{"id":4,"type":"bid","condition":0}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":5,"sender":3,"price":5,"quantity":1,"type":"ask","condition":0}}}',
    '{"type":"event","eventType":"add-order","data":{"order":{"id":6,"sender":4,"price":5,"quantity":1,"type":"ask","condition":0}}}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723798054252}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":7}}',
    '{"type":"notice","message":"Phase 7 has begun."}',
    '{"type":"info","message":"Player Gray submitted a declaration of values."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723798069269}}',
    '{"type":"event","eventType":"declarations-published","data":{"declarations":[{"id":1,"name":"Mathematical Antlion Lot","owner":"Tan","role":3,"number":1,"d":[350000,150000],"available":[true,false,false]},{"id":2,"name":"Mechanical Mite Lot","owner":"Gray","role":2,"number":2,"d":[3,0,0],"available":[true,false,false]}],"winningCondition":0}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":8}}',
    '{"type":"notice","message":"Phase 8 has begun."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"info","message":"Final phase. Tax rate: 33"}',
    '{"type":"event","eventType":"profit","data":{"round":0,"phase":9,"property":1,"condition":0,"value":468000,"declaration":350000,"sniped":true,"speculator":[4],"snipeProfit":59000,"taxes":115500,"owner":1,"role":3,"total":293500}}',
    '{"type":"event","eventType":"final-price","data":{"price":1155.0099,"winningCondition":0}}',
    '{"type":"event","eventType":"tax-income","data":{"amount":6930,"condition":0}}',
    '{"type":"event","eventType":"profit","data":{"round":0,"phase":9,"condition":0,"owner":1,"role":3,"taxes":0,"snipeProfit":0,"total":6930}}',
    '{"type":"event","eventType":"total-profit","data":{"amount":764930}}',
    '{"type":"event","eventType":"second-snipes","data":{"snipes":[{"player":{"number":4,"role":1},"target":{"number":1,"role":3},"profit":59000}]}}',
    '{"type":"event","eventType":"set-timer","data":{"end":1723798080864}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":0,"phase":9}}',
    '{"type":"notice","message":"Phase 9 has begun."}',
    '{"type":"event","eventType":"reset-timer","data":{}}',
    '{"type":"event","eventType":"round-end","data":{"round":0}}',
    '{"type":"event","eventType":"round-summary","data":{"round":0,"condition":0,"value":468000,"firstDeclaration":350000,"firstTaxes":3500,"firstRepurchase":0,"snipes":[{"player":{"number":4,"role":1},"target":{"number":1,"role":3},"profit":59000}],"market":{"balance":60000,"shares":6,"price":1155.0099},"secondDeclaration":350000,"secondTaxes":115500,"secondRepurchase":-59000}}',
    '{"type":"event","eventType":"phase-transition","data":{"round":1,"phase":0}}'
]

# Feed the messages to the GameHandler
for message in messages:
    handler.receive_message(message)
    time.sleep(1)  # Simulate some delay between receiving messages

# Allow enough time for the dispatch to occur
time.sleep(10)

# Stop the dispatcher after testing
handler.stop_dispatcher()
