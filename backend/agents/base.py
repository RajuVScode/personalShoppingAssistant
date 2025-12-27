import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

def get_llm():
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
        temperature=0.7
    )

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = get_llm()
    
    def invoke(self, user_message: str, context: dict = None) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message)
        ]
        if context:
            context_str = f"\nContext: {context}"
            messages[0] = SystemMessage(content=self.system_prompt + context_str)
        
        response = self.llm.invoke(messages)
        return response.content
