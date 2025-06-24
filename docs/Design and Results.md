Multi- Agent System for Financial News Impact Analyzer

System Architecture
- The system architecture involves a total of five agents:-

Risk Analyst: Specializes in risk analysis of the content
Sentiment Analyst: Specializes in sentiment analysis of the content, whether its positive, negative or neutral.
Growth Analyst: Specializes in growth analysis, like the impact the content can have.
Initial Analyst: Gives the initial analysis of the content, which is to be discussed and updated, if needed
LLM-Judge- To judge the quality of the rationale of the agent and the content, along five metrics.

Communication Patterns
Hierarchical Coordination
        ┌─────────────────┐
        │ Initial Analysis│
        |    Agent        │
        └─────────┬───────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌────▼────┐    ┌───▼───┐
│  RA   │    │   GA    │    │  SA   │
└───────┘    └─────────┘    └───────┘
Peer-to-Peer Collaboration
┌─────────┐ ◄──── Discussion Rounds ────► ┌─────────┐
│ RA      │                               │   GA    │
└─────┬───┘                               └───┬─────┘
      │                                       │
      └────────► ┌─────────┐ ◄─────────-------┘       
                 │  SA     │
                 └─────────┘

The initial analysis done by the first agent is stored and passed as part of the propmt for the three agents partaking in the discussion, the risk analyst, followed by the growth analyst and finally the sentiment analyst. Two cases were experimented with:-
- All agents need to agree for there to be a consensus, if not possible in 5 rounds, a majority decision will be taken.
- Majority of the agents need to be in agreement for there to be a consensus, which will then terminate the discussion.

Discussion results from each round was stored in discussion history and then passed as the next round's prompt to the agents. So the changes in decisions at each round will be reflected in the discussion history files of each test case. Inter-agent communcation during the rounds is still something I am planning on working on, which wasn't possible due to time constraints and generating validation results from other financial news data to evaluate the agent framework. For evaluating those results, replace the file name in the evaluation script and run it. However, it will take a lot of time to generate.

Design Decision and Rationale:-
The motivation behind this design was to have a better quality of assessment for financial news. Taking inspiration from a multi-agent framework that deals with triage responses in healthcare ( assigning priority to emergency cases), this system was developed. A part of the limitation lied in the usage of open source models, since results aren't generated in a uniform format.

2-3 prompt iterations showing improvement
EARLIER PROMPT:-
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
"""

LIMITATIONS:-
- Did not follow the output format despite it being stated in the system prompt.
- Led to fewer results being generated and more errors.

CURRENT PROMPT:-
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

STRENGTHS:-
- Solved the errors caused due to mismatch in output format.

Most of the system prompts were already optimized by giving a single line prompt and having Claude 3.7 Sonnet generate an optimized version, which was then screened by me.

EXAMPLES OF INTERESTING TEST CASE BEHAVIOURS(NOT MANY EXAMPLES IN THIS CATEGORY)

- Not much discussion rounds happen in the second case where a majority of the agents are required to reach a consensus. Usually terminates in round 1 and the updated sentiment is usually the same as the initial.
- Discussion rounds go beyond the first round more often in the first case since all agents have to reach a consensus. However, there would be very few times when the updated sentiment is different from the initial, in the test cases. It happens a bit more often when I deal with other sources of data , while validating the system.

PERFORMANCE OF THE SYSTEM
-LLM-Judge--{1}
- Results are in the evaluation folder for all different test cases.
-Likert like scale of coherence,evidence, completeness and consistency
-Pretty good scores on rationale quality as well in the analysis results---{2}

-Consistency of the system---{3}
-Both cases were run 2-3 times and evaluated. Results are pretty consistent across all iterations with slight variance.

-Accuracy(to be implemented)
- Was unable to implement for validation data due to the sheer amount of time required for generation. Will be improved in the future.

All discussion history for the test cases have been stored in the test discussion history folder.