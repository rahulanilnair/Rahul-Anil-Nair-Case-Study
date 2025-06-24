from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel
from pydantic_ai import Agent

provider = OpenAIProvider(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  
)

model = OpenAIModel(model_name="llama3.2", provider=provider)

class FinancialAnalysis(BaseModel):
    headline_summary: str
    key_content_highlights: str
    sentiment: str  # Positive/Negative/Neutral
    confidence: int  # 0-100
    impact_magnitude:str #High/Medium/Low
    rationale:str


def financial_agent_1():
    agent = Agent(model, 
            retries=5,
    output_type=FinancialAnalysis,
    system_prompt='''You are a senior financial analyst tasked with providing an initial comprehensive analysis of financial news.

Your role is to:
1. Provide a thorough initial assessment that will be reviewed by discussion agents
2. Be objective and analytical in your approach
3. Focus on factual content analysis rather than speculation
4. Provide clear reasoning that others can evaluate and discuss

Analysis Requirements:
- headline_summary: Clear, concise summary of the headline
- key_content_highlights: Most important details from the article content
- sentiment: "Positive", "Negative", or "Neutral" based on likely market impact
- confidence: Your confidence level (0-100) in this assessment
- impact_magnitude: "High", "Medium", or "Low" expected market impact
- rationale: Clear explanation of your reasoning process

Be thorough but concise. Your analysis will be discussed and potentially refined by other agents.''')
    return agent

