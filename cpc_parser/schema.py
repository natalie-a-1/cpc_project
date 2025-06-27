"""
Pydantic models for CPC practice test questions.

This module defines the data models used throughout the project for representing
CPC practice test questions with proper validation.
"""

from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import json


class Question(BaseModel):
    """
    Model representing a single CPC practice test question.
    
    Attributes:
        id: Question number (1-100)
        stem: The main question text
        options: Dictionary mapping A-D to answer choice text
        correct_answer_letter: The correct answer letter (A, B, C, or D)
        correct_answer_text: The text of the correct answer
        explanation: Explanation of why the answer is correct
    """
    
    id: int = Field(
        ..., 
        ge=1, 
        le=100, 
        description="Question number between 1 and 100"
    )
    
    stem: str = Field(
        ..., 
        min_length=3,
        description="The main question text"
    )
    
    options: Dict[Literal["A", "B", "C", "D"], str] = Field(
        ...,
        description="Answer choices mapped A through D"
    )
    
    correct_answer_letter: Literal["A", "B", "C", "D"] = Field(
        ...,
        description="The correct answer letter"
    )
    
    correct_answer_text: str = Field(
        ...,
        description="The text of the correct answer"
    )
    
    explanation: str = Field(
        default="",
        description="Explanation of why the answer is correct"
    )
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Ensure all four options (A-D) are present."""
        required_keys = {"A", "B", "C", "D"}
        if set(v.keys()) != required_keys:
            raise ValueError(f"Options must contain exactly keys A, B, C, D. Got: {set(v.keys())}")
        
        # Ensure all option values are non-empty strings
        for key, value in v.items():
            if not value or not value.strip():
                raise ValueError(f"Option {key} cannot be empty")
        
        return v
    
    @model_validator(mode='after')
    def validate_answer_consistency(self) -> 'Question':
        """Ensure correct_answer_text matches the text of correct_answer_letter in options."""
        if self.correct_answer_letter not in self.options:
            raise ValueError(f"Answer letter {self.correct_answer_letter} not found in options")
        
        expected_correct_answer_text = self.options[self.correct_answer_letter]
        if self.correct_answer_text != expected_correct_answer_text:
            # Auto-correct if there's a mismatch (useful during parsing)
            self.correct_answer_text = expected_correct_answer_text
        
        return self
    
    @field_validator('stem')
    @classmethod
    def clean_stem(cls, v: str) -> str:
        """Clean and validate the question stem."""
        # Remove excessive whitespace
        cleaned = ' '.join(v.split())
        
        # Ensure it ends with a question mark or period
        if cleaned and not cleaned.endswith(('.', '?', '!', ':')):
            # If it looks like a question, add a question mark
            question_words = ['which', 'what', 'when', 'where', 'who', 'why', 'how']
            if any(cleaned.lower().startswith(word) for word in question_words):
                cleaned += '?'
            else:
                cleaned += '.'
        
        return cleaned
    
    def to_jsonl_dict(self) -> dict:
        """
        Convert to a dictionary suitable for JSONL output.
        
        This flattens the structure for easier processing in benchmarking/fine-tuning.
        """
        return {
            "id": self.id,
            "stem": self.stem,
            "option_a": self.options["A"],
            "option_b": self.options["B"],
            "option_c": self.options["C"],
            "option_d": self.options["D"],
            "correct_answer_letter": self.correct_answer_letter,
            "correct_answer_text": self.correct_answer_text,
            "explanation": self.explanation
        }
    
    def to_prompt(self, include_options: bool = True) -> str:
        """
        Generate a formatted prompt string for model evaluation.
        
        Args:
            include_options: Whether to include the answer choices
            
        Returns:
            Formatted question string
        """
        prompt = f"Question {self.id}: {self.stem}"
        
        if include_options:
            prompt += "\n\n"
            for letter, text in sorted(self.options.items()):
                prompt += f"{letter}. {text}\n"
        
        return prompt.strip()
    
    def to_training_messages(self) -> list[dict]:
        """
        Convert to OpenAI fine-tuning format (messages).
        
        Returns:
            List of message dictionaries for fine-tuning
        """
        return [
            {
                "role": "user",
                "content": self.to_prompt()
            },
            {
                "role": "assistant",
                "content": f"The correct answer is {self.correct_answer_letter}. {self.correct_answer_text}\n\nExplanation: {self.explanation}"
            }
        ]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "stem": "During a regular checkup, Dr. Stevens discovered a suspicious lesion on the floor of Paul's mouth and decided to perform an excision. Which CPT code covers the excision of an oral lesion?",
                "options": {
                    "A": "40800",
                    "B": "41105", 
                    "C": "41113",
                    "D": "40804"
                },
                "correct_answer_letter": "B",
                "correct_answer_text": "41105",
                "explanation": "CPT code 41105 specifically covers excision of lesions on the floor of the mouth."
            }
        }
    }


class QuestionDataset(BaseModel):
    """
    Model for a collection of questions (e.g., a full test).
    """
    
    questions: list[Question] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of questions in the dataset"
    )
    
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata about the dataset"
    )
    
    @field_validator('questions')
    @classmethod
    def validate_unique_ids(cls, v: list[Question]) -> list[Question]:
        """Ensure all question IDs are unique."""
        ids = [q.id for q in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate question IDs found: {set(duplicates)}")
        return v
    
    def to_jsonl(self, output_path: str) -> None:
        """
        Write questions to a JSONL file.
        
        Args:
            output_path: Path to write the JSONL file
        """
        with open(output_path, 'w') as f:
            for question in self.questions:
                json_line = json.dumps(question.to_jsonl_dict(), ensure_ascii=False)
                f.write(json_line + '\n')
    
    @classmethod
    def from_jsonl(cls, input_path: str) -> 'QuestionDataset':
        """
        Load questions from a JSONL file.
        
        Args:
            input_path: Path to the JSONL file
            
        Returns:
            QuestionDataset instance
        """
        questions = []
        with open(input_path, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                # Convert from flattened format back to nested
                question_data = {
                    "id": data["id"],
                    "stem": data["stem"],
                    "options": {
                        "A": data["option_a"],
                        "B": data["option_b"],
                        "C": data["option_c"],
                        "D": data["option_d"]
                    },
                    "correct_answer_letter": data["correct_answer_letter"],
                    "correct_answer_text": data["correct_answer_text"],
                    "explanation": data.get("explanation", "")
                }
                questions.append(Question(**question_data))
        
        return cls(questions=questions)
    
    def get_statistics(self) -> dict:
        """
        Get basic statistics about the dataset.
        
        Returns:
            Dictionary with dataset statistics
        """
        answer_distribution = {"A": 0, "B": 0, "C": 0, "D": 0}
        for q in self.questions:
            answer_distribution[q.correct_answer_letter] += 1
        
        return {
            "total_questions": len(self.questions),
            "answer_distribution": answer_distribution,
            "avg_stem_length": sum(len(q.stem) for q in self.questions) / len(self.questions),
            "avg_explanation_length": sum(len(q.explanation) for q in self.questions) / len(self.questions),
            "questions_with_explanations": sum(1 for q in self.questions if q.explanation)
        }
