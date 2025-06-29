"""
PDF parser for CPC practice test.

This module parses the CPC practice test PDF and extracts questions,
answer choices, correct answers, and explanations into structured data.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber
from cpc_parser.schema import Question, QuestionDataset


class CPCTestParser:
    """Parser for CPC practice test PDF files."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the parser with a PDF file path.
        
        Args:
            pdf_path: Path to the CPC test PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.questions: List[Dict] = []
        self.answer_key: Dict[int, Tuple[str, str]] = {}
        self.explanations: Dict[int, str] = {}
        
    def parse(self) -> QuestionDataset:
        """
        Parse the entire PDF and return a QuestionDataset.
        
        Returns:
            QuestionDataset containing all parsed questions
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            # Step 1: Parse questions from pages 4-35 (approximately)
            self._parse_questions(pdf)
            
            # Step 2: Parse answer key
            self._parse_answer_key(pdf)
            
            # Step 3: Parse explanations
            self._parse_explanations(pdf)
            
        # Step 4: Combine all data into Question objects
        questions = self._combine_data()
        
        return QuestionDataset(questions=questions)
    
    def _parse_questions(self, pdf) -> None:
        """Parse questions from the test section."""
        print("Parsing questions...")
        
        all_text = ""
        # Questions start on page 4 (index 3) and go until answer key
        for page_num in range(3, len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if not text:
                continue
                
            # Stop when we hit the answer key
            if "Answer Key" in text:
                break
                
            # Remove the "Medical Coding Ace" header
            text = text.replace("Medical Coding Ace\n", "").strip()
            all_text += text + "\n"
        
        # Now parse all questions from the combined text
        # Split by question numbers
        question_splits = re.split(r'\n?(\d+)\.\s+', all_text)
        
        # First element is empty or pre-question text, so skip it
        # Then pairs of (number, question_text)
        for i in range(1, len(question_splits), 2):
            if i+1 >= len(question_splits):
                break
                
            q_num = int(question_splits[i])
            remaining_text = question_splits[i+1]
            
            # Find where the options start (first occurrence of \nA.)
            option_start = remaining_text.find('\nA.')
            if option_start == -1:
                continue
                
            # Question text is everything before options
            q_text = remaining_text[:option_start].strip()
            q_text = q_text.replace('\n', ' ')  # Replace newlines with spaces
            
            # Extract options
            options_text = remaining_text[option_start:]
            options = {}
            
            # Parse each option
            for letter in ['A', 'B', 'C', 'D']:
                pattern = f'\\n{letter}\\. ([^\\n]+)'
                match = re.search(pattern, options_text)
                if match:
                    options[letter] = match.group(1).strip()
            
            # Store the question data
            if len(options) == 4:  # Ensure we have all 4 options
                self.questions.append({
                    'id': q_num,
                    'stem': q_text,
                    'options': options
                })
            else:
                print(f"Warning: Question {q_num} has {len(options)} options instead of 4")
                    
        print(f"Parsed {len(self.questions)} questions")
    
    def _parse_answer_key(self, pdf) -> None:
        """Parse the answer key section."""
        print("Parsing answer key...")
        
        answer_key_started = False
        combined_text = ""
        
        # Find answer key pages
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if not text:
                continue
                
            # Check if this is an answer key page
            if "Answer Key" in text:
                answer_key_started = True
            
            # If we're in answer key section and see checkbox pattern
            if answer_key_started and "[ ]" in text:
                # Remove header
                text = text.replace("Medical Coding Ace\n", "").strip()
                combined_text += text + "\n"
            
            # Stop when we hit explanations
            elif answer_key_started and "Explanations" in text and "[ ]" not in text:
                break
        
        # Now parse all answers from combined text
        # Split into lines and process
        lines = combined_text.split('\n')
        
        current_answer = None
        for line in lines:
            # Check if this line starts a new answer
            match = re.match(r'\[\s*\]\s*(\d+)\.\s*([A-D])\.\s*(.+)', line)
            if match:
                # Save previous answer if exists
                if current_answer:
                    self.answer_key[current_answer[0]] = (current_answer[1], current_answer[2])
                
                # Start new answer
                q_num = int(match.group(1))
                answer_letter = match.group(2)
                answer_text = match.group(3).strip()
                current_answer = [q_num, answer_letter, answer_text]
            
            # Check if this is a continuation of the previous answer
            elif current_answer and line.strip() and not line.startswith('[ ]'):
                # Append to current answer text
                current_answer[2] += ' ' + line.strip()
        
        # Don't forget the last answer
        if current_answer:
            self.answer_key[current_answer[0]] = (current_answer[1], current_answer[2])
                
        print(f"Parsed {len(self.answer_key)} answers")
    
    def _parse_explanations(self, pdf) -> None:
        """Parse the explanations section."""
        print("Parsing explanations...")
        
        # Find where explanations start (around page 41)
        explanation_start = None
        for page_num in range(35, len(pdf.pages)):  # Start looking from page 36
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text and "Explanations" in text and "Answer Key" not in text:
                explanation_start = page_num
                break
        
        if explanation_start is None:
            print("Warning: Explanations section not found")
            return
            
        print(f"Found explanations starting at page {explanation_start + 1}")
        
        # Combine all explanation pages into one text
        all_explanation_text = ""
        for page_num in range(explanation_start, len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if not text:
                continue
                
            # Remove header
            text = text.replace("Medical Coding Ace\n", "").strip()
            all_explanation_text += text + "\n"
        
        # Split by question numbers first
        # This pattern finds question starts: number followed by period and space
        question_splits = re.split(r'\n(\d+)\.\s+', all_explanation_text)
        
        # Process each question (skip first element as it's before first question)
        for i in range(1, len(question_splits), 2):
            if i+1 >= len(question_splits):
                break
                
            q_num = int(question_splits[i])
            remaining_text = question_splits[i+1]
            
            # Find where "Explanation:" appears
            exp_match = re.search(r'Explanation:\s*\n?(.+?)(?=\n\d+\.|$)', remaining_text, re.DOTALL)
            
            if exp_match:
                explanation_text = exp_match.group(1).strip()
                
                # Clean up the explanation text
                # Remove excessive whitespace
                explanation_text = re.sub(r'\s+', ' ', explanation_text)
                # Fix sentence spacing
                explanation_text = re.sub(r'\.\s*', '. ', explanation_text)
                explanation_text = explanation_text.strip()
                
                self.explanations[q_num] = explanation_text
            
        print(f"Parsed {len(self.explanations)} explanations")
    
    def _combine_data(self) -> List[Question]:
        """Combine questions, answers, and explanations into Question objects."""
        print("Combining data into Question objects...")
        
        combined_questions = []
        
        for q_data in self.questions:
            q_id = q_data['id']
            
            # Get answer from answer key
            if q_id not in self.answer_key:
                print(f"Warning: No answer found for question {q_id}")
                continue
                
            answer_letter, answer_text = self.answer_key[q_id]
            
            # Get explanation (optional)
            explanation = self.explanations.get(q_id, "")
            
            # Create Question object
            try:
                question = Question(
                    id=q_id,
                    stem=q_data['stem'],
                    options=q_data['options'],
                    correct_answer_letter=answer_letter,
                    correct_answer_text=answer_text,
                    explanation=explanation
                )
                combined_questions.append(question)
            except Exception as e:
                print(f"Error creating question {q_id}: {e}")
                continue
        
        print(f"Successfully created {len(combined_questions)} Question objects")
        return combined_questions


def parse_cpc_test(pdf_path: str, output_path: Optional[str] = None) -> QuestionDataset:
    """
    Parse a CPC test PDF and optionally save to JSONL.
    
    Args:
        pdf_path: Path to the CPC test PDF
        output_path: Optional path to save JSONL output
        
    Returns:
        QuestionDataset containing all parsed questions
    """
    parser = CPCTestParser(pdf_path)
    dataset = parser.parse()
    
    if output_path:
        dataset.to_jsonl(output_path)
        print(f"Saved {len(dataset.questions)} questions to {output_path}")
    
    return dataset


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_pdf.py <pdf_path> [output_jsonl_path]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    dataset = parse_cpc_test(pdf_path, output_path)
    
    # Print statistics
    stats = dataset.get_statistics()
    print("\nDataset Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")