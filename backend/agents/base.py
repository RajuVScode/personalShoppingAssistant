import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

def get_azure_config():
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
    api_key = os.getenv('AZURE_OPENAI_API_KEY', '')
    
    if endpoint.startswith('http') and api_key.startswith('http'):
        pass
    elif api_key.startswith('http') and not endpoint.startswith('http'):
        endpoint, api_key = api_key, endpoint
    
    if deployment.startswith('http'):
        endpoint, deployment = deployment, endpoint
    
    return endpoint, deployment, api_key

def get_llm():
    endpoint, deployment, api_key = get_azure_config()
    
    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment,
        api_version='2024-12-01-preview',
        api_key=api_key,
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
