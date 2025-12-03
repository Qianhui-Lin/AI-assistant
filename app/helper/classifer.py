from openai import OpenAI
client = OpenAI()

def classify_category(question: str) -> str:
    """
    Return one of:
      - "handbook"
      - "academic_integrity"
      - "other"
    """
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a classification system for Lancaster University postgraduate research student queries.\n\n"
                    
                    "Classify questions into ONE category:\n\n"
                    
                    "Category: 'handbook'\n"
                    "Topics include:\n"
                    "- Research degree requirements (PhD, MPhil, Masters by Research criteria)\n"
                    "- Registration periods, progression requirements, confirmation of PhD status\n"
                    "- Thesis submission procedures, formats, and deadlines\n"
                    "- Examination procedures (viva voce, examiners, outcomes)\n"
                    "- Resubmission processes and disagreements between examiners\n"
                    "- Supervisor responsibilities, Schedule of Work\n"
                    "- Award definitions and specific doctoral programme regulations\n"
                    "- Online/remote examination procedures\n"
                    "- Posthumous awards\n\n"
                    
                    "Category: 'academic_integrity'\n"
                    "Topics include:\n"
                    "- Plagiarism (copying, paraphrasing without citation, self-plagiarism)\n"
                    "- Cheating in examinations or coursework\n"
                    "- Collusion and false authorship\n"
                    "- Fabrication or falsification of research results\n"
                    "- Academic malpractice procedures and penalties\n"
                    "- Standing Academic Committee hearings\n"
                    "- Academic Integrity Officer procedures\n"
                    "- Proofreading policies and citation requirements\n"
                    "- Retrospective detection of academic misconduct\n"
                    "- Appeals against academic malpractice penalties\n\n"
                    
                    "Category: 'other'\n"
                    "For questions that don't fit the above categories, such as:\n"
                    "- General university services or facilities\n"
                    "- Accommodation or financial queries\n"
                    "- Non-academic student support\n"
                    "- Administrative procedures unrelated to research degrees\n"
                    "- Questions outside the scope of postgraduate research regulations\n\n"
                    
                    "IMPORTANT DISTINCTIONS:\n"
                    "- Questions about thesis examination, viva procedures, or submission → 'handbook'\n"
                    "- Questions about academic misconduct in thesis/dissertation → 'academic_integrity'\n"
                    "- Questions about normal progression/requirements → 'handbook'\n"
                    "- Questions about dishonesty, cheating, or plagiarism → 'academic_integrity'\n\n"
                    
                    "OUTPUT INSTRUCTION:\n"
                    "Respond with ONLY ONE WORD - the category name in lowercase.\n"
                    "Valid responses: handbook, academic_integrity, or other\n"
                    "Do NOT include any explanation, punctuation, or additional text."
                )
            },
            {"role": "user", "content": question}
        ],
        temperature=0
    )

    # Clean the response to extract just the category
    response = result.choices[0].message.content.strip().lower()
    
    # Remove any extra text - take only the first word
    response = response.split()[0]
    
    # Remove any punctuation
    response = response.replace(',', '').replace('.', '').replace(':', '')
    
    # Validate it's one of the expected categories
    valid_categories = {"handbook", "academic_integrity", "other"}
    if response not in valid_categories:
        # If we got something unexpected, try to parse it
        for category in valid_categories:
            if category in response:
                return category
        # Default fallback
        return "other"
    
    return response