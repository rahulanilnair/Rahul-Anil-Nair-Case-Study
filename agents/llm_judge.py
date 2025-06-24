import re
import asyncio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Agent
from datetime import datetime
import os
from typing import Dict, Any
from pydantic import BaseModel, Field
provider = OpenAIProvider(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  
)

model = OpenAIModel(model_name="qwen2.5:7b-instruct", provider=provider)
class RationaleQualityAssessment(BaseModel):
    """Model for rationale quality assessment"""
    overall_quality_score: int = Field(description="Overall quality score 1-10")
    coherence_score: int = Field(description="Logical coherence score 1-10")
    evidence_score: int = Field(description="Evidence quality score 1-10")
    completeness_score: int = Field(description="Completeness score 1-10")
    consistency_score: int = Field(description="Cross-agent consistency score 1-10")
    
    strengths: str = Field(description="Key strengths of the rationale")
    weaknesses: str = Field(description="Areas for improvement")
    recommendations: str = Field(description="Specific recommendations")
    
    summary: str = Field(description="Brief summary of quality assessment")

def judge_agent(sentiment,confidence,impact,rationale):
    return Agent(
        model=model,
        retries=5,
        output_type=RationaleQualityAssessment,
        system_prompt=f"""
You are an expert financial analysis quality assessor. Evaluate the following rationale from a multi-agent financial sentiment analysis system.

ANALYSIS DETAILS:
Final Sentiment: {sentiment}
Confidence: {confidence}%
Impact Magnitude: {impact}

RATIONALE TO ASSESS:
{rationale}

Please provide a comprehensive quality assessment covering:

1. OVERALL QUALITY (1-10): How well does the rationale support the final decision?
2. COHERENCE (1-10): Is the reasoning logical and well-structured?
3. EVIDENCE (1-10): How well does it use evidence from the original content?
4. COMPLETENESS (1-10): Does it address all relevant aspects?
5. CONSISTENCY (1-10): Are the different agent perspectives consistent and complementary?

Also provide:
- Key strengths of this rationale
- Areas that need improvement
- Specific recommendations for better analysis
- A brief summary of your assessment

Be thorough but concise in your evaluation.
"""
    )
    

