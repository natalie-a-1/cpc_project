"""
Tests for the Question and QuestionDataset Pydantic models.
"""

import pytest
from pydantic import ValidationError
from cpc_parser.schema import Question, QuestionDataset


class TestQuestion:
    """Test cases for the Question model."""
    
    def test_valid_question_creation(self):
        """Test creating a valid question."""
        question = Question(
            id=1,
            stem="Which CPT code represents excision of a benign lesion?",
            options={
                "A": "11400",
                "B": "11401", 
                "C": "11402",
                "D": "11403"
            },
            correct_answer_letter="A",
            correct_answer_text="11400",
            explanation="CPT code 11400 is for excision of benign lesions."
        )
        
        assert question.id == 1
        assert question.correct_answer_letter == "A"
        assert question.options["A"] == "11400"
        assert question.correct_answer_text == "11400"
    
    def test_id_validation(self):
        """Test ID must be between 1-100."""
        # Test too low
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=0,
                stem="Test question?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a"
            )
        assert "greater than or equal to 1" in str(exc_info.value)
        
        # Test too high
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=101,
                stem="Test question?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a"
            )
        assert "less than or equal to 100" in str(exc_info.value)
    
    def test_stem_validation(self):
        """Test stem must be at least 3 characters."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=1,
                stem="Hi",  # Only 2 characters
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a"
            )
        assert "at least 3 characters" in str(exc_info.value)
    
    def test_stem_cleaning(self):
        """Test stem whitespace cleaning and punctuation."""
        # Test whitespace cleaning
        q1 = Question(
            id=1,
            stem="Which   code   is    correct",  # Multiple spaces
            options={"A": "a", "B": "b", "C": "c", "D": "d"},
            correct_answer_letter="A",
            correct_answer_text="a"
        )
        assert q1.stem == "Which code is correct?"
        
        # Test adding period for non-question
        q2 = Question(
            id=2,
            stem="The correct code is found in the manual",
            options={"A": "a", "B": "b", "C": "c", "D": "d"},
            correct_answer_letter="A",
            correct_answer_text="a"
        )
        assert q2.stem.endswith(".")
    
    def test_options_validation(self):
        """Test options must contain exactly A, B, C, D."""
        # Missing option
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=1,
                stem="Test question?",
                options={"A": "a", "B": "b", "C": "c"},  # Missing D
                correct_answer_letter="A",
                correct_answer_text="a"
            )
        assert "must contain exactly keys A, B, C, D" in str(exc_info.value)
        
        # Extra option
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=1,
                stem="Test question?",
                options={"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
                correct_answer_letter="A",
                correct_answer_text="a"
            )
        
        # Empty option value
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=1,
                stem="Test question?",
                options={"A": "a", "B": "", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a"
            )
        assert "Option B cannot be empty" in str(exc_info.value)
    
    def test_answer_letter_validation(self):
        """Test correct_answer_letter must be A, B, C, or D."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=1,
                stem="Test question?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="E",  # Invalid
                correct_answer_text="a"
            )
        assert "Input should be" in str(exc_info.value)
    
    def test_answer_consistency_validation(self):
        """Test correct_answer_text auto-corrects to match correct_answer_letter option."""
        q = Question(
            id=1,
            stem="Test question?",
            options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            correct_answer_letter="B",
            correct_answer_text="Wrong text"  # Should auto-correct to "Option B"
        )
        assert q.correct_answer_text == "Option B"
    
    def test_to_jsonl_dict(self):
        """Test conversion to JSONL dictionary format."""
        q = Question(
            id=1,
            stem="Test question?",
            options={"A": "a", "B": "b", "C": "c", "D": "d"},
            correct_answer_letter="A",
            correct_answer_text="a",
            explanation="Test explanation"
        )
        
        jsonl_dict = q.to_jsonl_dict()
        assert jsonl_dict["id"] == 1
        assert jsonl_dict["stem"] == "Test question?"
        assert jsonl_dict["option_a"] == "a"
        assert jsonl_dict["option_b"] == "b"
        assert jsonl_dict["option_c"] == "c"
        assert jsonl_dict["option_d"] == "d"
        assert jsonl_dict["correct_answer_letter"] == "A"
        assert jsonl_dict["explanation"] == "Test explanation"
    
    def test_to_prompt(self):
        """Test prompt generation."""
        q = Question(
            id=1,
            stem="Which code is correct?",
            options={"A": "11400", "B": "11401", "C": "11402", "D": "11403"},
            correct_answer_letter="A",
            correct_answer_text="11400"
        )
        
        # With options
        prompt_with = q.to_prompt(include_options=True)
        assert "Question 1: Which code is correct?" in prompt_with
        assert "A. 11400" in prompt_with
        assert "B. 11401" in prompt_with
        
        # Without options
        prompt_without = q.to_prompt(include_options=False)
        assert prompt_without == "Question 1: Which code is correct?"
    
    def test_to_training_messages(self):
        """Test conversion to fine-tuning format."""
        q = Question(
            id=1,
            stem="Test question?",
            options={"A": "a", "B": "b", "C": "c", "D": "d"},
            correct_answer_letter="A",
            correct_answer_text="a",
            explanation="Because A is correct"
        )
        
        messages = q.to_training_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert "Test question?" in messages[0]["content"]
        assert messages[1]["role"] == "assistant"
        assert "The correct answer is A" in messages[1]["content"]
        assert "Because A is correct" in messages[1]["content"]


class TestQuestionDataset:
    """Test cases for the QuestionDataset model."""
    
    def test_valid_dataset_creation(self):
        """Test creating a valid dataset."""
        questions = [
            Question(
                id=i,
                stem=f"Test question {i}?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a"
            )
            for i in range(1, 4)
        ]
        
        dataset = QuestionDataset(questions=questions)
        assert len(dataset.questions) == 3
    
    def test_duplicate_id_validation(self):
        """Test that duplicate IDs are rejected."""
        questions = [
            Question(
                id=1,  # Duplicate ID
                stem=f"Test question {i}?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a"
            )
            for i in range(2)
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            QuestionDataset(questions=questions)
        assert "Duplicate question IDs found" in str(exc_info.value)
    
    def test_get_statistics(self):
        """Test dataset statistics calculation."""
        questions = [
            Question(
                id=1,
                stem="First test question?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a",
                explanation="Explanation 1"
            ),
            Question(
                id=2,
                stem="Second test question?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="B",
                correct_answer_text="b",
                explanation=""
            ),
            Question(
                id=3,
                stem="Third test question?",
                options={"A": "a", "B": "b", "C": "c", "D": "d"},
                correct_answer_letter="A",
                correct_answer_text="a",
                explanation="Explanation 3"
            )
        ]
        
        dataset = QuestionDataset(questions=questions)
        stats = dataset.get_statistics()
        
        assert stats["total_questions"] == 3
        assert stats["answer_distribution"]["A"] == 2
        assert stats["answer_distribution"]["B"] == 1
        assert stats["answer_distribution"]["C"] == 0
        assert stats["answer_distribution"]["D"] == 0
        assert stats["questions_with_explanations"] == 2 