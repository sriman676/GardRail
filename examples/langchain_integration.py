"""
LangChain Integration Example with GuardRail

This example demonstrates how to integrate GuardRail's real-time shield
into a LangChain LLMChain or Agent Executor loop.
"""
import asyncio
from dotenv import load_dotenv

# Import the GuardRail shield
from agent.guardrail_wrapper import GuardRail

load_dotenv()

# Suppose you have a LangChain run method or customized chain executor
class MyLangChainAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    def invoke(self, inputs: dict) -> dict:
        """
        Simulated LangChain invocation loop.
        """
        task = inputs.get("task")
        _content = inputs.get("content")
        
        # In a real LangChain setup:
        # prompt = PromptTemplate.from_template("...")
        # chain = prompt | ChatOpenAI()
        # return chain.invoke({"task": task, "content": content})
        
        return {
            "text": f"LangChain Agent completed task '{task}' successfully."
        }


async def main():
    # Instantiate GuardRail
    guard = GuardRail(decision_mode="cli")
    
    # Instantiate LangChain Agent
    langchain_agent = MyLangChainAgent()

    # We wrap the LangChain call using guard.run()
    # By passing the custom callable directly, we secure the LangChain pipeline!
    task = "Summarize the key objectives"
    clean_content = "Objective 1: Accelerate growth. Objective 2: Optimize operations."

    print("\n--- Securing LangChain with GuardRail ---")
    
    # Custom agent callable to match GuardRail's expected (task, content) signature
    def run_agent(t, c):
        res = langchain_agent.invoke({"task": t, "content": c})
        return res["text"]

    result = await guard.run(
        task=task,
        input_content=clean_content,
        agent_callable=run_agent
    )

    print(f"Status:       {result['status']}")
    print(f"Scan Threat:  {result.get('scan_threat_level')}")
    print(f"Agent Output: {result.get('output')}")


if __name__ == "__main__":
    asyncio.run(main())
