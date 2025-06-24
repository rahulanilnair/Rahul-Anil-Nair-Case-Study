import asyncio
from pydantic import BaseModel,Field
from agents.intial_analyst import financial_agent_1,FinancialAnalysis
from agents.growth_analyst import growth_analyst
from agents.risk_analyst import risk_analyst
from agents.sentiment_analyst import sentiment_analyst
import json


########### REAL TEST DATA LOADING ########################################################################

with open("C:/Users/rahul/Downloads/Rahul-Anil-Nair-Case-Study/test_data/test_data.jsonl",'r') as file:
    test_articles = [json.loads(line) for line in file]

#############################################################################################################
#                           VALIDATION DATA LOADING(TO CHECK IF FRAMEWORK REALLY WORKS)                     #
#############################################################################################################  

import os
positive_folder_path = "C:/Users/rahul/Downloads/Rahul-Anil-Nair-Case-Study/Financial and Economic News_positive_20250209072617/Financial and Economic News_positive_20250209072617"
negative_folder_path = "C:/Users/rahul/Downloads/Rahul-Anil-Nair-Case-Study/Financial and Economic News_negative_20241223003542/Financial and Economic News_negative_20241223003542"
def file_extractor(folder_path):
    extracted_data=[]
    extracted_results=[]
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        extracted = {
                            "article_id": data.get("uuid"),
                            "headline": data.get("title"),
                            "content": data.get("text")
                        }
                        result = data.get("sentiment")
                        extracted_data.append(extracted)
                        extracted_results.append(result)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    return extracted_data,extracted_results

positive_data,positive_results=file_extractor(positive_folder_path)
negative_data,negative_results=file_extractor(negative_folder_path)

#############################################################################################################
#                        AGENTIC WORKFLOW                                                                   #
#############################################################################################################

class ConsensusAnalysis(BaseModel):
    final_analysis: FinancialAnalysis = Field(description="Final consensus analysis")
    discussion_summary: str = Field(description="Summary of the discussion process")
    rounds_to_consensus: int = Field(description="Number of discussion rounds needed")
    agreement_level: str = Field(description="Level of final agreement among agents")

class FinancialDiscussion:
    def __init__(self, headline: str, content: str):
        self.headline = headline
        self.content = content
        self.agents = [financial_agent_1()]
        self.discussion_agent_dict={"risk_analyst":risk_analyst(),"growth_analyst":growth_analyst(),"sentiment_analyst":sentiment_analyst()}
        self.discussion_history = []
        self.current_analysis=None
        self.max_rounds=5

    async def initial_analysis(self):
        """Get initial analysis from all agents"""
        tasks = [
            agent.run(f"""
Analyze this financial news and provide your initial assessment:

HEADLINE: {self.headline}

CONTENT: {self.content}

Provide a comprehensive analysis that will serve as the starting point for discussion.
""")
            for agent in self.agents
        ]
        
        results = await asyncio.gather(*tasks)
        self.current_analysis=results[0].data
        return self.current_analysis
    
    async def discussion_generation(self,round_num):
        if self.current_analysis is None:
            await self.initial_analysis()
        discussion_context = f"""
CURRENT ANALYSIS UNDER DISCUSSION:
Headline Summary: {self.current_analysis.headline_summary}
Key Content Highlights: {self.current_analysis.key_content_highlights}
Current Sentiment: {self.current_analysis.sentiment}
Current Confidence: {self.current_analysis.confidence}%
Current Impact: {self.current_analysis.impact_magnitude}
Current Rationale: {self.current_analysis.rationale}

ORIGINAL NEWS:
HEADLINE: {self.headline}
CONTENT: {self.content}

DISCUSSION ROUND {round_num}:
Review the current analysis and provide your assessment. Do you agree with the current sentiment, confidence, and impact ratings? What is your perspective?

RESPONSE FORMAT REQUIRED:
You must respond with exactly these fields:
- stance: "Agree", "Disagree", or "Partially Agree"
- proposed_sentiment: "Positive", "Negative", or "Neutral"
- proposed_confidence: integer between 0-100
- proposed_impact: "High", "Medium", or "Low"
- reasoning: your explanation
- key_points: your main supporting points

Use these exact field names and values. Do not deviate from this format.
"""
        if self.discussion_history:
            agent_names=list(self.discussion_agent_dict.keys())
            discussion_context+= f"\n\nPREVIOUS DISCUSSION POINTS:\n"
            for i,responses in enumerate(self.discussion_history):
                discussion_context += f"Round {i+1}:\n"
                for j in range(len(responses)):
                   discussion_context += f"- {agent_names[j]}: {responses[j].stance} -{responses[j].proposed_confidence} -{responses[j].proposed_sentiment} - {responses[j].reasoning}...\n"
        tasks = [agent.run(discussion_context) for agent in self.discussion_agent_dict.values()]
        results = await asyncio.gather(*tasks)
        responses=[result.output for result in results]
        self.discussion_history.append(responses)
        return responses 
    
    def check_consensus(self,responses):
        sentiment_count={}
        impact_count={}
        confidence_score=0
        for response in responses:
            sentiment=response.proposed_sentiment
            sentiment_count[sentiment]=sentiment_count.get(sentiment,0)+1
            impact=response.proposed_impact
            impact_count[impact]=impact_count.get(impact,0)+1
            confidence_score+=response.proposed_confidence
        max_sentiment=max(sentiment_count.values())
        max_impact=max(impact_count.values())
        majority_sentiment=None
        majority_impact=None
        if max_sentiment>=3:
            majority_sentiment=[k for k,v in sentiment_count.items() if v==max_sentiment][0]
        if max_impact>=3:
            majority_impact=[k for k,v in impact_count.items() if v==max_impact][0]

        avg_confidence = int(confidence_score / len(responses))
        consensus_bool=majority_impact is not None and majority_sentiment is not None
        consensus={
            'majority_sentiment': majority_sentiment,
            'majority_impact': majority_impact,
            'avg_confidence': avg_confidence,
            'sentiment_votes': sentiment_count,
            'impact_votes': impact_count,
            'agreement_count': max_sentiment
        }
        return consensus_bool,consensus

    def update_analysis(self,responses,consensus):
        majority_sentiment=consensus['majority_sentiment']
        key_insights = []
        agent_names = list(self.discussion_agent_dict.keys())
        for i, response in enumerate(responses):
            if response.proposed_sentiment == majority_sentiment:
                agent_name = agent_names[i] if i < len(agent_names) else f"Agent_{i}"
                key_insights.append(f"{agent_name}: {response.reasoning}")
        
        if not key_insights:
            for i, response in enumerate(responses):
                agent_name = agent_names[i] if i < len(agent_names) else f"Agent_{i}"
                key_insights.append(f"{agent_name}: {response.reasoning}")
    
        combined_rationale = " ".join(key_insights)
        self.current_analysis.sentiment = consensus['majority_sentiment']
        self.current_analysis.confidence = consensus['avg_confidence']
        self.current_analysis.impact_magnitude = consensus['majority_impact']
        self.current_analysis.rationale = combined_rationale
    
    async def full_discussion(self):
        initial_analysis=await self.initial_analysis()
        consensus_bool=False
        final_info=None
        agent_names = list(self.discussion_agent_dict.keys())
        for i in range(self.max_rounds):
            responses=await self.discussion_generation(i)
            consensus_bool,consensus=self.check_consensus(responses)
            if consensus_bool:
                self.update_analysis(responses,consensus)
                final_info=consensus
                break
            else:
                print(f"   No consensus yet. Sentiment votes: {consensus['sentiment_votes']}")
        if not consensus_bool:
            print(f"\nNo consensus reached after {self.max_rounds} rounds. Using majority vote from final round.")
            final_info = consensus
            self.update_analysis(responses,consensus)
        discussion_summary = f"Discussion involved {len(self.discussion_history)} rounds. "
        if consensus_bool:
            discussion_summary += f"Consensus reached with {final_info['agreement_count']}/3 agents agreeing on {final_info['majority_sentiment']} sentiment."
        else:
            discussion_summary += f"No full consensus reached. Final decision based on majority vote: {final_info['sentiment_votes']}"
        
        agreement_level = "Strong" if final_info['agreement_count'] == 3 else "Majority" if final_info['agreement_count'] == 2 else "Weak"
        
        return ConsensusAnalysis(
            final_analysis=self.current_analysis,
            discussion_summary=discussion_summary,
            rounds_to_consensus=len(self.discussion_history),
            agreement_level=agreement_level
        )

            

def save_analysis_results(consensus_result, article_id, output_dir="test_analysis_results_1_3"):
    """Save consensus analysis results to a file"""
    import os
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create analysis summary
    analysis_content = f"""
{"="*60}
📊 FINAL CONSENSUS ANALYSIS - Article {article_id}
{"="*60}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Headline Summary: {consensus_result.final_analysis.headline_summary}
Key Highlights: {consensus_result.final_analysis.key_content_highlights}
Final Sentiment: {consensus_result.final_analysis.sentiment}
Confidence: {consensus_result.final_analysis.confidence}%
Impact Magnitude: {consensus_result.final_analysis.impact_magnitude}
Agreement Level: {consensus_result.agreement_level}
Rounds to Consensus: {consensus_result.rounds_to_consensus}

Rationale: {consensus_result.final_analysis.rationale}

Discussion Summary: {consensus_result.discussion_summary}
{"="*60}
"""
    
    # Save analysis results
    analysis_filename = os.path.join(output_dir, f"analysis_article_{article_id}.txt")
    with open(analysis_filename, 'w', encoding='utf-8') as f:
        f.write(analysis_content)
    
    return analysis_filename

def save_discussion_history(financial_discussion, article_id, output_dir="test_discussion_history_1_3"):
    """Save detailed discussion history to a file"""
    import os
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create discussion history content
    history_content = f"""
{"="*60}
💬 DISCUSSION HISTORY - Article {article_id}
{"="*60}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Original Headline: {financial_discussion.headline}
Original Content: {financial_discussion.content[:500]}...

INITIAL ANALYSIS:
- Headline Summary: {financial_discussion.current_analysis.headline_summary}
- Key Content Highlights: {financial_discussion.current_analysis.key_content_highlights}
- Initial Sentiment: {financial_discussion.current_analysis.sentiment}
- Initial Confidence: {financial_discussion.current_analysis.confidence}%
- Initial Impact: {financial_discussion.current_analysis.impact_magnitude}
- Initial Rationale: {financial_discussion.current_analysis.rationale}

DISCUSSION ROUNDS:
"""
    
    agent_names = list(financial_discussion.discussion_agent_dict.keys())
    
    for round_num, responses in enumerate(financial_discussion.discussion_history, 1):
        history_content += f"\n--- ROUND {round_num} ---\n"
        for i, response in enumerate(responses):
            agent_name = agent_names[i] if i < len(agent_names) else f"Agent_{i}"
            history_content += f"""
{agent_name.upper()}:
  Stance: {response.stance}
  Proposed Sentiment: {response.proposed_sentiment}
  Proposed Confidence: {response.proposed_confidence}%
  Proposed Impact: {response.proposed_impact}
  Reasoning: {response.reasoning}
  Key Points: {response.key_points}
"""
    
    history_content += f"\n{'='*60}\n"
    
    # Save discussion history
    history_filename = os.path.join(output_dir, f"discussion_history_article_{article_id}.txt")
    with open(history_filename, 'w', encoding='utf-8') as f:
        f.write(history_content)
    
    return history_filename

def save_summary_json(results_summary, output_dir="test_analysis_results_1_3"):
    """Save a JSON summary of all analyses"""
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    summary_filename = os.path.join(output_dir, "analysis_summary.json")
    
    with open(summary_filename, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    return summary_filename

async def main():
    try:
        results_summary = []
        
        for i in range(0,len(test_articles)):
            content = test_articles[i]['content']
            headline = test_articles[i]['headline']
            article_id = test_articles[i].get('article_id', f'article_{i}')
            
            print(f"\n🔄 Processing article {i+1}/{len(test_articles)}: {headline[:100]}...")
            
            financial_discussion = FinancialDiscussion(headline, content)
            
            try:
                consensus_result = await financial_discussion.full_discussion()
                
                # Print to console (shortened version)
                print(f"✅ Article {i+1} completed - Sentiment: {consensus_result.final_analysis.sentiment}, "
                      f"Confidence: {consensus_result.final_analysis.confidence}%, "
                      f"Agreement: {consensus_result.agreement_level}")
                
                # Save detailed analysis results to file
                analysis_file = save_analysis_results(consensus_result, i+1)
                print(f"📄 Analysis saved to: {analysis_file}")
                
                # Save discussion history to file
                history_file = save_discussion_history(financial_discussion, i+1)
                print(f"💬 Discussion history saved to: {history_file}")
                
                # Add to summary
                summary_entry = {
                    "article_id": i+1,
                    "original_article_id": article_id,
                    "headline": headline,
                    "final_sentiment": consensus_result.final_analysis.sentiment,
                    "confidence": consensus_result.final_analysis.confidence,
                    "impact_magnitude": consensus_result.final_analysis.impact_magnitude,
                    "agreement_level": consensus_result.agreement_level,
                    "rounds_to_consensus": consensus_result.rounds_to_consensus,
                    "analysis_file": analysis_file,
                    "history_file": history_file
                }
                results_summary.append(summary_entry)
                
            except Exception as e:
                print(f"❌ Error during discussion for article {i+1}: {e}")
                error_entry = {
                    "article_id": i+1,
                    "original_article_id": article_id,
                    "headline": headline,
                    "error": str(e),
                    "status": "failed"
                }
                results_summary.append(error_entry)
                continue
        
        # Save overall summary
        summary_file = save_summary_json(results_summary)
        print(f"\n📊 Overall summary saved to: {summary_file}")
        print(f"\n🎉 Processing complete! Analyzed {len([r for r in results_summary if 'error' not in r])} articles successfully.")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())



    

