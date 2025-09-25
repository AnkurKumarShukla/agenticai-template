from ..models.state_models import SupervisorState
from ..agents.base import build_agent_state
# from ..tools.tool_wrappers import invoke_agent
from ..mcp.clients import init_clients

from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


from langchain.chat_models import init_chat_model

llm=init_chat_model("openai:gpt-4o-mini")

async def financial_agent_node(state: SupervisorState) -> SupervisorState:
    """Run the financial agent with the current task and update state."""
    sysprompt_fin_agent = f"""
You are an advanced technical analysis AI assistant equipped with specialized tools 
to detect candlestick patterns and calculate support/resistance levels. 
Your primary function is to help users analyze both **stocks and cryptocurrencies** 
using price action and chart-based signals.

You are a trading assistant. You can call tools to answer user questions.  

If the user asks for candlestick patterns, support/resistance levels, or short-term market signals, 
use the appropriate tool.  

Tools you have:  
    three_white_soldiers,  
    morningstar,  
    bullish_engulfing,  
    rising_three_methods,  
    pivotpoints  

Context so far is: {str(state.context)}  

- For **stocks in India**, append '.NS' for NSE or '.BO' for BSE when calling tools.  
- For **cryptocurrencies**, use trading pairs (e.g., `BTC/USDT`, `ETH/USDT`).  
- Before making a decision, carefully review context and past decisions to avoid redundant calls.  
- Always maintain a professional, concise, and objective tone in responses.  
- Your goal is to provide accurate, actionable technical insights that help traders 
  make better entry/exit decisions.  

Always respond with:  
1. Which tool you are calling  
2. The result from that tool  

Only use the tools you have — do not hallucinate.  

"""
    tools = await init_clients()
    finance_tools=  tools["financial_tools"]
    finance_agent = create_react_agent(
        llm.bind_tools(finance_tools ,parallel_tool_calls=False),
        tools=finance_tools,
        prompt=sysprompt_fin_agent,
        name="finance_agent",
    )
    if not state.current_task:
        return state  # no task assigned, nothing to do

    # Run the financial agent on the supervisor's current task
    # Ensure your agent is the ReAct agent you created earlier
    input = {"messages": [{"role": "user", "content": state.current_task}]}
    print("this is context ",state.context)
    result = await finance_agent.ainvoke(input=input)
    
    # Convert the messages from the agent into AgentState
    agent_state = build_agent_state(result["messages"], agent_name="finance_agent")

    # Include agent name
    # agent_state.agent_name = "FinanceAgent"

    # Add agent state to SupervisorState
    state.agent_states.setdefault("FinanceAgent", []).append(agent_state)

    # Update context for downstream use
    state.context[f"FinanceAgent_step{len(state.agent_states['FinanceAgent'])}"] = agent_state.agent_output

    # Clear current_task (supervisor will decide next)
    state.current_task = None

    return state


# state = SupervisorState(user_query="Check stock info")
# state.current_task = "what is TCS stock price"

# # Run financial agent node
# updated_state = financial_agent_node(state)

# # Show result
# # print(updated_state.dump_json(indent=2))