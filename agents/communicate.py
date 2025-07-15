import json
import subprocess
import threading
import time
from queue import Queue, Empty


class MCPClient:
    def __init__(self, server_script):
        self.server_script = server_script
        self.process = None
        self.request_id = 0
        self.response_queue = Queue()
        self.reader_thread = None
        self.running = False

    def start_server(self):
        """Start the MCP server process"""
        try:
            self.process = subprocess.Popen(
                ['fastmcp', 'run', self.server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )

            self.running = True

            self.reader_thread = threading.Thread(target=self._read_responses)
            self.reader_thread.daemon = True
            self.reader_thread.start()

            time.sleep(3)

            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read()
                raise Exception(f"Server process died: {stderr_output}")

        except Exception as e:
            print(f"Error starting server: {e}")
            raise

    def _read_responses(self):
        while self.running and self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    line = line.strip()
                    if line and line.startswith('{'):
                        try:
                            response = json.loads(line)
                            self.response_queue.put(response)
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}, line: {line}")
                            pass
            except Exception as e:
                print(f"Reader thread error: {e}")
                break

    def send_request(self, method, params=None):
        if not self.process or self.process.poll() is not None:
            raise Exception("Server process is not running")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        request_json = json.dumps(request) + '\n'

        try:
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
        except BrokenPipeError:
            stderr_output = self.process.stderr.read()
            raise Exception(f"Broken pipe - server may have crashed: {stderr_output}")

        timeout = 5
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = self.response_queue.get(timeout=0.1)
                if response.get('id') == self.request_id:
                    return response
                else:
                    # Put back if not matching ID
                    self.response_queue.put(response)
            except Empty:
                continue

        return None

    def send_notification(self, method, params=None):
        if not self.process or self.process.poll() is not None:
            raise Exception("Server process is not running")

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }

        notification_json = json.dumps(notification) + '\n'

        try:
            self.process.stdin.write(notification_json)
            self.process.stdin.flush()
        except BrokenPipeError:
            stderr_output = self.process.stderr.read()
            raise Exception(f"Broken pipe - server may have crashed: {stderr_output}")

    def initialize(self):
        init_response = self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })

        self.send_notification("agents/initialized")
        return init_response

    def list_tools(self):
        return self.send_request("tools/list")

    def call_tool(self, tool_name, arguments):
        return self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

    def close(self):
        self.running = False
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
                self.process.wait()

try:
    client = MCPClient('agents/server.py')
    client.start_server()

    print("Initializing...")
    init_response = client.initialize()
    print(f"Init response: {init_response}")

    print("\nListing tools...")
    tools_response = client.list_tools()
    print(f"Tools: {tools_response}")

    print("\nGetting weather for Berlin...")
    weather_response = client.call_tool("get_weather", {"city": "Berlin"})
    print(f"Weather response: {weather_response}")

    print("\nSetting weather for Paris...")
    set_response = client.call_tool("set_weather", {"city": "Paris", "temp": 22.5})
    print(f"Set response: {set_response}")

    print("\nGetting weather for Paris...")
    paris_weather = client.call_tool("get_weather", {"city": "Paris"})
    print(f"Paris weather: {paris_weather}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'client' in locals():
        client.close()
