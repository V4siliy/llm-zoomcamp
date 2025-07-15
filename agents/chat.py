import asyncio
import json
import os

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP, Client
from openai import OpenAI

load_dotenv()

OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

mcp = FastMCP("Weather Server 🌤️")


@mcp.tool
def get_current_weather(city: str) -> dict:
    if not OPEN_WEATHER_API_KEY:
        return {
            "error": "OPEN_WEATHER_API_KEY is not set in environment variables.",
            "message": "Please set your OpenWeatherMap API key in the .env file or environment variables."
        }

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPEN_WEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        data = response.json()

        if response.status_code != 200:
            message = data.get("message", "Unknown error retrieving weather.")
            return {
                "error": f"OpenWeatherMap API error: {message}",
                "city": city,
                "status_code": response.status_code
            }

        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature_celsius": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "weather": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data.get("wind", {}).get("speed", "N/A")
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Network error: {str(e)}",
            "city": city
        }
    except Exception as e:
        return {
            "error": f"Error retrieving weather: {str(e)}",
            "city": city
        }


def serialize_tool_calls(tool_calls):
    if not tool_calls:
        return None

    serialized = []
    for tool_call in tool_calls:
        serialized.append({
            "id": tool_call.id,
            "type": tool_call.type,
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }
        })
    return serialized


class MCPWeatherAssistant:
    def __init__(self, mcp_server, system_prompt=None):
        self.mcp_server = mcp_server
        self.system_prompt = system_prompt or "You are a helpful weather assistant with access to real-time weather data."
        self.conversation_history = []

    async def get_available_tools(self):
        """Get list of available tools from MCP server"""
        async with Client(self.mcp_server) as mcp_client:
            tools = await mcp_client.list_tools()
            return self.convert_mcp_tools_to_openai_format(tools)

    def convert_mcp_tools_to_openai_format(self, mcp_tools):
        openai_tools = []

        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            openai_tools.append(openai_tool)

        return openai_tools

    async def call_tool(self, function_name, arguments):
        async with Client(self.mcp_server) as mcp_client:
            result = await mcp_client.call_tool(function_name, arguments)
            return result

    async def process_message(self, user_message, openai_client):
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        tools = await self.get_available_tools()

        messages = [
                       {"role": "system", "content": self.system_prompt}
                   ] + self.conversation_history

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            self.conversation_history.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": serialize_tool_calls(response_message.tool_calls)
            })

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                tool_result = await self.call_tool(function_name, function_args)

                if isinstance(tool_result, dict):
                    tool_result_str = json.dumps(tool_result)
                else:
                    tool_result_str = str(tool_result)

                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_str
                })

            final_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                             {"role": "system", "content": self.system_prompt}
                         ] + self.conversation_history
            )

            final_message = final_response.choices[0].message.content

        else:
            final_message = response_message.content

        self.conversation_history.append({
            "role": "assistant",
            "content": final_message
        })

        return final_message

    async def run_chat(self, openai_client):
        print("🌤️ Weather Assistant started! Type 'quit' to exit.")
        print("Ask me about the weather in any city around the world!")

        if not OPEN_WEATHER_API_KEY:
            print("\n⚠️  WARNING: OPEN_WEATHER_API_KEY is not set!")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break

            if not user_input:
                continue

            try:
                response = await self.process_message(user_input, openai_client)
                print(f"Assistant: {response}\n")
            except Exception as e:
                print(f"Error: {e}\n")


async def main():
    openai_client = OpenAI()

    weather_system_prompt = """
    You are a helpful weather assistant with access to real-time weather data from OpenWeatherMap.

    You can get current weather information for any city in the world using the get_current_weather tool.

    When users ask about weather:
    1. Always use the get_current_weather tool to get accurate, up-to-date information
    2. Present the information in a friendly, conversational way
    3. Include temperature, weather conditions, humidity, and pressure when available
    4. If there's an error in the tool response (like API key not set), explain the issue clearly and provide helpful guidance
    5. Format temperatures with appropriate units (Celsius)

    Be conversational and helpful in your responses. Handle errors gracefully and provide useful suggestions.
    """

    chat_assistant = MCPWeatherAssistant(
        mcp_server=mcp,
        system_prompt=weather_system_prompt
    )

    await chat_assistant.run_chat(openai_client)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        mcp.run()
    else:
        asyncio.run(main())
