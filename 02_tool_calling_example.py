import os
import json
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city and state, e.g. San Francisco, CA"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        }
    }
]

# we will keep track of messages in a list
messages = [
    {"role": "system", "content": "You are a helpful assistant that provides weather information."},
    {"role": "user", "content": "What's the weather like in Jakarta?"}
]

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

response_message = response.choices[0].message
messages.append(response_message)  # Add the assistant's response to the history

# We check if the LLM's response contains 'tool_calls'
if response_message.tool_calls:
    print("\nSuccess! The LLM wants to call a tool.")
    print(f"Tool calls: \n")

    # The 'tool_calls' is a list, as it could ask to call multiple tools
    for tool_call in response_message.tool_calls:
        print(f"  Tool Name: {tool_call.function.name}")
        print(f"  Arguments: {tool_call.function.arguments}")

        # The arguments are a JSON *string*, so we parse them
        parsed_arguments = json.loads(tool_call.function.arguments)
        print(f"  Parsed Location: {parsed_arguments.get('location')}")
        print(f"  Parsed Unit: {parsed_arguments.get('unit')}")

else:
    # If it didn't call a tool, just print its text response
    print("\nThe LLM did not call a tool, it just replied:")
    print(response_message.content)