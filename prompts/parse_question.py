def parse_gemini_output_to_structured_json(text_response):

    if not text_response or not isinstance(text_response, str):
        return text_response

    questions_data = []
    current_task_label = None
    lines = [line.strip() for line in text_response.splitlines() if line.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("**Task 1"):
            current_task_label = "Task 1"
            i += 1
            continue
        elif line.startswith("**Task 2"):
            current_task_label = "Task 2"
            i += 1
            continue
        
        if line.startswith("Question:"):
            question_obj = {} 
            question_obj["task"] = current_task_label
            question_obj["question_text"] = line.replace("Question:", "").strip()
            
            # Check next line for "Answer:"
            if (i + 1) < len(lines) and lines[i+1].startswith("Answer:"):
                i += 1 # Move to Answer line
                answer_text = lines[i].replace("Answer:", "").strip()
                
                # Check line after Answer for "Options:" to determine if MCQ
                if (i + 1) < len(lines) and lines[i+1].startswith("Options:"):
                    question_obj["type"] = "MCQ"
                    question_obj["answer"] = answer_text # Should be a letter like "A", "B", etc.
                    question_obj["options"] = {}
                    
                    i += 1 # Move to "Options:" line
                    i += 1 # Move to the first option line
                    while i < len(lines) and re.match(r"^[A-D]\)", lines[i]):
                        option_match = re.match(r"^([A-D])\)\s*(.*)", lines[i])
                        if option_match:
                            opt_letter = option_match.group(1)
                            opt_text = option_match.group(2).strip()
                            question_obj["options"][opt_letter] = opt_text
                        else: # Should not be reached if re.match is true
                            break 
                        i += 1 # Move to next option line or line after last option
                    questions_data.append(question_obj)
                    continue # Parsed MCQ, continue outer loop (i is now at line after last option)
                else:
                    # No "Options:" line followed Answer, so it's Subjective
                    question_obj["type"] = "Subjective"
                    question_obj["answer"] = answer_text # This is the phrase
                    questions_data.append(question_obj)
                    i += 1 # Move past Answer line for next iteration
                    continue
            else:
                # "Question:" was found, but "Answer:" did not follow immediately.
                # Add the question if you want to capture questions even if malformed,
                # or simply skip. For now, we skip adding this malformed entry.
                i += 1 # Move past the "Question:" line
                continue
        
        i += 1 # Default: move to the next line if current line wasn't a recognized start

    return questions_data if questions_data else text_response