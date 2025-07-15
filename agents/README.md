# Homework: Agents and FastMCP

This folder contains the solutions and code for the "Agents" homework

## Introduction

[Tasks](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/cohorts/2025/0a-agents/homework.md)
[Webinar](https://www.youtube.com/watch?v=GH3lrOsU3AU)

## Project Structure

```
.
├── [README.md](README.md)
├── [agents.ipynb](agents.ipynb)            # The notebook with homework
├── [communicate.py](communicate.py)        # Custom MCP client for demonstration
└── [server.py](server.py)                  # Simple FastMCP server for weather tools
└── [chat.py](chat.py)                      # Simple FastMCP server with Open Weather API integration
```

## Key Concepts Covered

### Function Calling

The ability of an LLM to identify when an external tool or API should be called and to output the arguments needed to call that tool. We start by defining descriptions for our `get_weather` and `set_weather` tools in a format suitable for function calling.

### Model-Context Protocol (MCP)

An evolution of function calling where tools export their functionalities, and agents can communicate with these tools by linking to an MCP server. This allows for a more standardized and scalable way for LLMs to use various services.

### FastMCP

A Python library that facilitates the creation of MCP servers and clients, streamlining the process of exposing and consuming tools for LLM agents.

## Setup and Installation

To run the code in this repository, you'll need Python 3.8+ and the following packages:

1.  **Install FastMCP:**
    ```bash
    uv add fastmcp
    ```

### Tools

We implement two core tools for our agent:
-   `get_weather(city: str)`: Retrieves simulated weather data for a given city.
-   `set_weather(city: str, temp: float)`: Adds or updates weather data for a city.

### Q1. Define Function Description

We define the necessary structure for `get_weather` as a tool, adhering to a standard function calling schema (e.g., OpenAI's function tool description).

*   **Key Learnings:** Understanding the components of a function tool description: `name`, `description`, `parameters` (including `type`, `properties`, `required`, and `additionalProperties`).

### Q2. Adding Another Tool

Similarly, we define the tool description for `set_weather`, expanding our agent's capabilities.

*   **Key Learnings:** Applying the same principles for defining tool descriptions to new functions, including handling multiple parameters (`city`, `temp`).

## FastMCP Server

This section covers the implementation and interaction with our FastMCP server.

### Q3. Install FastMCP

*(This step is largely for verification within the homework; refer to "Setup and Installation" above for execution.)*

### Q4. Simple MCP Server (`server.py`)

We transform our `get_weather` and `set_weather` functions into discoverable tools by wrapping them in a `FastMCP` server.

*   **File:** [server.py](server.py)
*   **Key Learnings:**
    *   Using `@mcp.tool` decorator to register functions as MCP tools.
    *   The importance of docstrings for automatic tool description generation by FastMCP.
    *   Understanding the server's output and its communication transport (e.g., `stdio`).
*   **To run the server:**
    ```bash
    python weather_server.py
    ```

### Q5. Protocol - Interacting with the Server

We explore the low-level communication protocol (JSON-RPC) used by MCP. This involves sending initialization requests, acknowledging, and then formally listing and calling tools via `stdin`/`stdout`.

*   **Key Learnings:**
    *   The `initialize`, `notifications/initialized`, `tools/list`, and `tools/call` JSON-RPC methods.
    *   The structure of requests and responses to interact directly with an MCP server's I/O stream.

## FastMCP Client

This section focuses on using the FastMCP client to programmatically interact with our server.

### Q6. Client

We implement a client using `FastMCP.Client` to interact with our [communicate.py](communicate.py) file, demonstrating how to list available tools.

*   **Key Learnings:**
    *   Programmatically retrieving `tools/list` information from the server.

### Using Tools from the MCP Server (Optional)

Chat Assistant Implementation with FastMCP - [chat.py](chat.py)
With OpenAI and Open Weather APIs assistant leverages OpenAI's function calling capabilities by dynamically providing the `get_current_weather` tool's definition to the LLM. 
When the LLM decides to use this tool, the assistant intercepts the tool_calls request, dispatches it to our local FastMCP server using the fastmcp.
Client, and then feeds the real-time weather results back into the conversation. 
This seamless integration allows the LLM to access and present up-to-date weather information.

```
You: And what about Novi Sad?
Assistant: In Novi Sad, Serbia, the current weather is lovely. The temperature is 29.64°C with broken clouds. It feels like 29.28°C outside. The humidity is at 40%, and the atmospheric pressure is 1012 hPa. The wind is blowing at 3.66 m/s. Enjoy the pleasant weather in Novi Sad!
```