from datetime import datetime
import os
import asyncio
import sys
from pydantic import BaseModel,Field
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now import from agents
try:
    from agents.llm_judge import judge_agent
except ImportError:
    print("Error: Could not import judge_agent from agents module")
    print(f"Current directory: {current_dir}")
    print(f"Parent directory: {parent_dir}")
    print(f"Looking for: {os.path.join(parent_dir, 'agents', '__init__.py')}")
    print(f"Agents folder exists: {os.path.exists(os.path.join(parent_dir, 'agents'))}")
    sys.exit(1)
import json
import re
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

def extract_rationale_from_analysis(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            analysis_text = f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None
  
    sentiment_match = re.search(r'Final Sentiment: (\w+)', analysis_text)
    sentiment = sentiment_match.group(1) if sentiment_match else None
    
    confidence_match = re.search(r'Confidence: (\d+)%', analysis_text)
    confidence = int(confidence_match.group(1)) if confidence_match else None
    
    impact_match = re.search(r'Impact Magnitude: (\w+)', analysis_text)
    impact = impact_match.group(1) if impact_match else None
 
    rationale_match = re.search(r'Rationale: (.+?)Discussion Summary:', analysis_text, re.DOTALL)
    rationale = rationale_match.group(1).strip() if rationale_match else None
  
    article_match = re.search(r'Article (\d+)', analysis_text)
    article_id = article_match.group(1) if article_match else "unknown"
    
    return {
        'article_id': article_id,
        'sentiment': sentiment,
        'confidence': confidence,
        'impact_magnitude': impact,
        'rationale': rationale
    }

async def run_judge_evaluation(analysis_file_path: str, output_folder: str = "test_judge_evaluations_1_3"):
    """
    Run judge evaluation on analysis file and save results
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Extract rationale and analysis details from file
    analysis_data = extract_rationale_from_analysis(analysis_file_path)
    
    if not analysis_data:
        print(f"Failed to extract analysis data from {analysis_file_path}")
        return None
    
    try:
        # Initialize judge agent with extracted data
        judge = judge_agent(
            sentiment=analysis_data['sentiment'],
            confidence=analysis_data['confidence'],
            impact=analysis_data['impact_magnitude'],
            rationale=analysis_data['rationale']
        )
        
        # Run the judge evaluation
        print(f"Evaluating Article {analysis_data['article_id']}...")
        result = await judge.run("Please evaluate this financial sentiment analysis rationale.")
        
        # Prepare output data
        evaluation_result = {
            'article_id': analysis_data['article_id'],
            'original_analysis': {
                'sentiment': analysis_data['sentiment'],
                'confidence': analysis_data['confidence'],
                'impact_magnitude': analysis_data['impact_magnitude'],
                'rationale': analysis_data['rationale']
            },
            'judge_evaluation': {
                'overall_quality_score': result.data.overall_quality_score,
                'coherence_score': result.data.coherence_score,
                'evidence_score': result.data.evidence_score,
                'completeness_score': result.data.completeness_score,
                'consistency_score': result.data.consistency_score,
                'strengths': result.data.strengths,
                'weaknesses': result.data.weaknesses,
                'recommendations': result.data.recommendations,
                'summary': result.data.summary
            },
            'evaluation_timestamp': datetime.now().isoformat(),
            'source_file': analysis_file_path
        }
        
        # Save evaluation result
        output_filename = f"judge_evaluation_article_{analysis_data['article_id']}.json"
        output_path = os.path.join(output_folder, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, indent=2, ensure_ascii=False)
        
        print(f"Judge evaluation saved to: {output_path}")
        print(f"Overall Quality Score: {result.data.overall_quality_score}/10")
        print(f"Summary: {result.data.summary}")
        
        return evaluation_result
        
    except Exception as e:
        print(f"Error during judge evaluation: {e}")
        return None

async def batch_judge_evaluation(analysis_folder_path: str, output_folder: str = "test_judge_evaluations_1_3"):
    """
    Run judge evaluation on all analysis files in a folder
    """
    if not os.path.exists(analysis_folder_path):
        print(f"Analysis folder not found: {analysis_folder_path}")
        return
    
    analysis_files = [f for f in os.listdir(analysis_folder_path) if f.endswith('.txt')]
    
    if not analysis_files:
        print("No analysis files found in the specified folder")
        return
    
    print(f"Found {len(analysis_files)} analysis files to evaluate")
    
    results = []
    for filename in analysis_files[:50]:
        file_path = os.path.join(analysis_folder_path, filename)
        print(f"\nProcessing: {filename}")
        
        result = await run_judge_evaluation(file_path, output_folder)
        if result:
            results.append(result)

        await asyncio.sleep(1)
    
    # Save batch summary
    batch_summary = {
        'total_files_processed': len(analysis_files),
        'successful_evaluations': len(results),
        'batch_timestamp': datetime.now().isoformat(),
        'average_scores': calculate_average_scores(results) if results else None
    }
    
    summary_path = os.path.join(output_folder, "batch_evaluation_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(batch_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nBatch evaluation completed. Summary saved to: {summary_path}")
    print(f"Successfully evaluated {len(results)} out of {len(analysis_files)} files")

def calculate_average_scores(results):
    """Calculate average scores across all evaluations"""
    if not results:
        return None
    total_scores = {
        'overall_quality': 0,
        'coherence': 0,
        'evidence': 0,
        'completeness': 0,
        'consistency': 0,
    }
    for result in results:
        eval_data = result['judge_evaluation']
        total_scores['overall_quality'] += eval_data['overall_quality_score']
        total_scores['coherence'] += eval_data['coherence_score']
        total_scores['evidence'] += eval_data['evidence_score']
        total_scores['completeness'] += eval_data['completeness_score']
        total_scores['consistency'] += eval_data['consistency_score']
    
    count = len(results)
    return {
        'average_overall_quality': round(total_scores['overall_quality'] / count, 2),
        'average_coherence': round(total_scores['coherence'] / count, 2),
        'average_evidence': round(total_scores['evidence'] / count, 2),
        'average_completeness': round(total_scores['completeness'] / count, 2),
        'average_consistency': round(total_scores['consistency'] / count, 2),
    }

# Example usage
async def main():
    analysis_folder = "C:/Users/rahul/Downloads/Rahul-Anil-Nair-Case-Study/test_analysis_results_1_3"  
    await batch_judge_evaluation(analysis_folder)

# Run the evaluation
if __name__ == "__main__":
    asyncio.run(main())