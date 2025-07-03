
# === Prompts creation ===
def create_prompt_without_answers(survey_questions, transcript):
    """
    Create the initial prompt for the first transcript.
    
    Args:
        survey_questions (str): Formatted survey questions
        transcript (str): Interview transcript
        
    Returns:
        str: Complete prompt
    """
    return f"""Based on the following interview transcript between one social worker and one youth participant interested in participating in leaving care program, please fill out this survey. For each question, provide:
1. Answer: Base the answer according to the guidance provided in the parentheses. For text questions, try to cover all the relavant information for this question.
2. Certainty (low, medium, high)
3. Text field: All single/multiple choice questions must have a concise text reasoning, but make sure you cover all the relevant information related to the question. If not choice-based, leave blank.

Notes:
Output only for the questions that are clearly addressed in the transcript. 
Do not make up information, follow the transcript.
Format your response as a JSON array, nothing else.

SURVEY QUESTIONS:
{survey_questions}

TRANSCRIPT:
{transcript}

output example:
[
  {{
    "question_id": "5",
    "answer": "yes",
    "certainty": "high",
    "text field": "support in finding an apartment is urgent. Prefer first-hand contract"
  }},
  {{
    "question_id": "10",
    "answer": "lonely and depressed, having trouble to sleep and hard to find time for friends",
    "certainty": "medium",
    "text field": ""
  }}
]
"""

def create_prompt_with_answers(survey_questions, previous_answers, transcript):
    """
    Create prompt for subsequent transcripts that includes previous answers.
    
    Args:
        survey_questions (str): Formatted survey questions
        previous_answers (str): Previous answers formatted as string
        transcript (str): New interview transcript
        
    Returns:
        str: Complete prompt
    """
    return f"""The following transcript is an interview between a social worker and a youth participant interested in participating in the leaving care program. You are provided with the survey (see SURVEY QUESTIONS) which have been partially answered before (see PREVIOUS ANSWERS) based on another transcript. You will update the answers to the survey based on the provided transcripts. 

Here is the structure to answer a question:
1. Answer: Base the answer according to the guidance provided in the parentheses. For text questions, try to cover all the relavant information for this question.
2. Certainty (low, medium, high)
3. Text field: All single/multiple choice questions must have a concise text reasoning, but make sure you cover all the relevant information related to the question. If not choice-based, leave blank.

First, you need to recheck the previous answers against the new transcript to detect any potential conflicts or new information.
- If the new transcript contains conflicting information, update the previous answer according to the current transcript. 
- If the new transcript contains additional/new information, update the previous answer by adding the new information while keeping the previous answer.
- If the new answer is similar to the previous answer, no need to update.

Second, find answers in the new transcript for questions not answered previously:
- Only fill out the answer if the transcript has clearly addressed the question.

important:
- Only answer the questions that are clearly addressed in the transcript.
- Output ONLY for the updated answers and newly answered questions. 
- Do not make up information, follow the transcript.
- Format your response as a JSON array, nothing else.

SURVEY QUESTIONS:
{survey_questions}

PREVIOUS ANSWERS:
{previous_answers}

NEW TRANSCRIPT:
{transcript}

output example:
[
  {{
    "question_id": "5",
    "answer": "yes",
    "certainty": "high",
    "text field": "support in finding an apartment is urgent. Prefer first-hand contract"
  }},
  {{
    "question_id": "10",
    "answer": "lonely and depressed, having trouble to sleep and hard to find time for friends",
    "certainty": "medium",
    "text field": ""
  }}
]
"""