from ..models.state_models import SupervisorState
from ..agents.base import build_agent_state
from ..mcp.clients import init_clients

from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain.chat_models import init_chat_model

llm = init_chat_model("openai:gpt-4o-mini")

async def trade_executor_agent_node(state: SupervisorState) -> SupervisorState:
    """Run the trade executor agent with the current task and update state."""
    
    sysprompt_trade_executor = f"""
You are a professional cryptocurrency trading assistant.
Your goal is to evaluate the user's instructions to either BUY or SELL crypto assets,
and to execute trades only when clearly instructed by the supervisor or user.

You have access to specialized tools for buying and selling crypto assets.

Only use these tools if the user intends to take a real action (e.g. "buy", "sell").

User wallet address (dummy): 0x1234567890abcdef1234567890abcdef12345678

Context so far: {str(state.context)}

Guidelines:
- Carefully read the user’s task and analyze the context.
- Avoid duplicate or redundant trades.
- Use the appropriate tool: `buy_tool` or `sell_tool`.
- Do not explain — just call the tool with the correct parameters.
"""

    tools = await init_clients()
    trade_tools = tools["trade_exe_tools"]

    # Create the agent
    trade_agent = create_react_agent(
        llm.bind_tools(trade_tools, parallel_tool_calls=False),
        tools=trade_tools,
        prompt=sysprompt_trade_executor,
        name="trade_executor_agent",
    )

    if not state.current_task:
        return state  # no task assigned

    print("📦 [Trade Executor] Task:", state.current_task)
    print("🧠 [Trade Executor] Context:", state.context)

    input = {"messages": [{"role": "user", "content": state.current_task}]}
    
    result = await trade_agent.ainvoke(input=input)

    # Convert result into agent state
    agent_state = build_agent_state(result["messages"], agent_name="trade_executor_agent")

    # Add agent state to SupervisorState
    state.agent_states.setdefault("trade_executor_agent", []).append(agent_state)

    # Update context with agent output
    state.context[f"trade_executor_agent_step{len(state.agent_states['trade_executor_agent'])}"] = agent_state.agent_output

    # Clear current task
    state.current_task = None

    return state
