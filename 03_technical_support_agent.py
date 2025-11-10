import os
import random
import json
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

# --- 1. Define our actual Python functions (The "Tools") ---

# A simple mock database for our knowledge base
KNOWLEDGE_BASE = {
    "login issue": {
        "article_id": "KB-001",
        "title": "How to reset your password",
        "solution": "You can reset your password by clicking 'Forgot Password' on the login page."
    },
    "slow connection": {
        "article_id": "KB-002",
        "title": "Troubleshooting slow connection",
        "solution": "Try restarting your router and clearing your browser cache."
    }
}

def check_system_status():
    """
    Checks the overall status of all systems.
    Has a 30% chance of reporting a critical outage.
    """
    print("--- TOOL CALLED: check_system_status() ---")
    probability = random.random()

    if probability < 0.3:  # 30% chance of being "down"
        status = "Critical Outage: All login servers are down."
    else:  # 70% chance of being "up"
        status = "All systems operational."

    return json.dumps({"status": status})


def search_knowledge_base(query_string):
    """Searches the knowledge base for articles matching the query."""
    print(f"--- TOOL CALLED: search_knowledge_base(query_string='{query_string}') ---")

    # Simple keyword search
    results = []
    for key, article in KNOWLEDGE_BASE.items():
        if key in query_string.lower():
            results.append(article)

    return json.dumps(results)


def create_support_ticket(user_name, problem_description):
    """Creates a new support ticket in the system."""
    print(f"--- TOOL CALLED: create_support_ticket(user_name='{user_name}', problem_description='{problem_description}') ---")

    # In a real app, this would write to a database
    ticket_id = f"TICKET-{hash(user_name + problem_description) & 0xffff}"
    print(f"--- New ticket created: {ticket_id} ---")

    return json.dumps({
        "ticket_id": ticket_id,
        "user_name": user_name,
        "problem": problem_description,
        "status": "Open"
    })


# --- 2. Define the "Tool Menu" for the LLM ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "check_system_status",
            "description": "Checks the live status of all production systems."
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches the company knowledge base for solutions to common problems.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_string": {"type": "string", "description": "The user's problem, e.g., 'cannot log in'"},
                },
                "required": ["query_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Creates a new support ticket when a problem cannot be solved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_name": {"type": "string", "description": "The user's full name"},
                    "problem_description": {"type": "string", "description": "A detailed description of the problem"},
                },
                "required": ["user_name", "problem_description"],
            },
        },
    }
]

# --- 3. The Agent's "Memory" ---
messages = [
    {
        "role": "system",
        "content": "You are a 'Tier 1' technical support agent. Your name is 'SupportBot'. "
                   "First, *always* check 'check_system_status' when a user reports a new problem. "
                   "If the system is down, inform the user. Do not try to solve it. "
                   "If the system is operational, *then* 'search_knowledge_base' for a solution. "
                   "If you find a relevant article, provide it. "
                   "If you cannot find a solution, *then* 'create_support_ticket'. "
                   "You must ask for the user's name *before* creating a ticket. "
                   "Be polite and helpful."
    }
]

print("--- SupportBot is ready. Type 'quit' to exit. ---")
print("SupportBot: Hello! I'm SupportBot. How can I help you today?")

# --- 4. The Agent's "Perceive-Think-Act" Loop ---
while True:
    # PERCEIVE: Get input from the user
    user_input = input("You: ")
    if user_input.lower() == 'quit':
        break

    messages.append({"role": "user", "content": user_input})

    # THINK: Call the LLM to decide what to do
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        messages.append(response_message)  # Add assistant's "thinking" to memory

        # ACT: Check if the LLM decided to use a tool
        if response_message.tool_calls:
            print("--- LLM decided to use a tool ---")

            tool_call_results = []

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"--- Calling: {function_name}({function_args}) ---")

                # Call the correct Python function
                if function_name == "check_system_status":
                    function_response = check_system_status()
                elif function_name == "search_knowledge_base":
                    function_response = search_knowledge_base(
                        query_string=function_args.get("query_string")
                    )
                elif function_name == "create_support_ticket":
                    function_response = create_support_ticket(
                        user_name=function_args.get("user_name"),
                        problem_description=function_args.get("problem_description")
                    )
                else:
                    print(f"Error: Unknown function {function_name}")
                    function_response = json.dumps({"error": "Unknown function"})

                # Store the result to send back to the LLM
                tool_call_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response,
                })

            # Add all tool call results to the message history
            messages.extend(tool_call_results)

            # THINK (Round 2): Call the LLM *again* with the tool results
            print("--- Sending tool results back to LLM... ---")
            second_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )

            final_answer = second_response.choices[0].message
            print(f"SupportBot: {final_answer.content}")
            messages.append(final_answer)  # Add final answer to memory

        else:
            # ACT: If no tool was called, just print the chat response
            print(f"SupportBot: {response_message.content}")

    except Exception as e:
        print(f"An error occurred: {e}")
        break