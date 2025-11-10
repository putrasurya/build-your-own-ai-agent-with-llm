import os
import json
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_current_weather(location, unit):
    """A mock function to get weather data."""
    print(f"--- ---- -- Python function 'get_current_weather' was called with {location}, {unit} ---")
    weather_info = {
        "location": location,
        "temperature": "30",
        "unit": unit,
        "forecast": "sunny",
    }
    return json.dumps(weather_info)

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
    {"role": "user", "content": "What's the weather like in Boston?"}
]

print("--- Step 1: Calling GPT-4o with the user's request ---")
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

response_message = response.choices[0].message
messages.append(response_message)  # Add the assistant's response to the history

if response_message.tool_calls:
    print("--- Step 2: LLM wants to call a tool ---")

    # The 'tool_calls' is a list, as it could ask to call multiple tools
    for tool_call in response_message.tool_calls:
        print(f"--- ---- -- Tool call detected: {tool_call.function.name} with arguments {tool_call.function.arguments}")

        # The arguments are a JSON *string*, so we parse them
        parsed_arguments = json.loads(tool_call.function.arguments)

        # --- THIS IS THE KEY PART ---
        # Call the actual Python function with the arguments from the LLM
        if tool_call.function.name == "get_current_weather":
            function_response = get_current_weather(
                location=parsed_arguments.get("location"),
                unit=parsed_arguments.get("unit"),
            )
            print(f"--- Step 3: Sending tool result back to LLM ---")
            print(f"--- ---- -- Result being sent: {function_response}")

            # We create a new message with `role: "tool"`
            # We must include the `tool_call_id` to link the request and response
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": function_response,  # The JSON string from our function
                }
            )

    # Make the *second* API call, this time with the tool's result
    second_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,  # Send the *entire* conversation history
    )

    final_answer = second_response.choices[0].message.content
    print(f"--- Step 4: Final answer from LLM ---")
    print(f"--- ---- -- Assistant: {final_answer}")

else:
    # If it didn't call a tool, just print its text response
    print("\nThe LLM did not call a tool, it just replied:")
    print(response_message.content)