graph TD
    InstructionHandler[Instruction Handler] -->|Parses documents| SocketHandler(Socket Handler)
    SocketHandler -->|Manages connections & decisions| SimulationServer[Simulation Server]
    SimulationServer -->|Exchanges JSON messages| SocketHandler
    SocketHandler -->|Interacts with| LLMAgent[LLM Agent]
    LLMAgent -->|Communicates in JSON| SocketHandler

    subgraph SB["Socket Handler & LLM Agent"]
    InstructionHandler
    SocketHandler
    LLMAgent
    end

    subgraph SE["Simulation Environment"]
    SimulationServer --> Simulations
    end

    subgraph Simulations["Simulations"]
    Harberger[Harberger]
    Futarchy[Futarchy]
    Voting[Voting]
    Market[Market]
    end

    SimulationServer -->|Oversees| Simulations
    Simulations -->|Supported| Harberger
    Simulations -->|Supported| Futarchy
    Simulations -->|Supported| Voting
    Simulations -->|Supported| Market
    Simulations -->|Feedback to| SimulationServer
