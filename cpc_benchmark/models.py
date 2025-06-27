"""
Model providers for benchmarking different LLMs on CPC questions.

This module contains the base ModelProvider class and implementations for:
- OpenAI (GPT-4o)
- Anthropic (Claude 3.5 Sonnet)
- Google (Gemini 1.5 Pro)
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Abstract base class for model providers."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Initialize model provider.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for the provider (if not in env)
        """
        self.model_name = model_name
        self.api_key = api_key
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0
        
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 10) -> Dict[str, Any]:
        """
        Generate a response from the model.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with 'response', 'tokens_used', and 'latency'
        """
        pass
    
    @abstractmethod
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Return the cost per 1k tokens for input and output."""
        pass
    
    def reset_metrics(self):
        """Reset usage metrics."""
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0


class OpenAIProvider(ModelProvider):
    """OpenAI model provider for GPT models."""
    
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        
        # Initialize OpenAI client
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, max_tokens: int = 10) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert medical coder taking a CPC practice test. Answer with only the letter (A, B, C, or D) of the correct answer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.0,  # Deterministic for benchmarking
                n=1
            )
            
            # Extract response
            answer = response.choices[0].message.content.strip()
            
            # Calculate metrics
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Update metrics
            self.total_tokens += total_tokens
            self.request_count += 1
            
            # Calculate cost
            costs = self.get_cost_per_1k_tokens()
            cost = (input_tokens * costs['input'] + output_tokens * costs['output']) / 1000
            self.total_cost += cost
            
            return {
                'response': answer,
                'tokens_used': total_tokens,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'latency': time.time() - start_time,
                'cost': cost
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Get OpenAI pricing per 1k tokens."""
        # Pricing as of Nov 2024
        if self.model_name == "gpt-4o":
            return {'input': 2.5, 'output': 10.0}  # $2.50/$10.00 per 1M tokens
        elif self.model_name == "gpt-4o-mini":
            return {'input': 0.15, 'output': 0.60}  # $0.15/$0.60 per 1M tokens
        else:
            # Default GPT-4 pricing
            return {'input': 30.0, 'output': 60.0}


class AnthropicProvider(ModelProvider):
    """Anthropic model provider for Claude models."""
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        
        # Initialize Anthropic client
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, max_tokens: int = 10) -> Dict[str, Any]:
        """Generate response using Anthropic API."""
        start_time = time.time()
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=0.0,  # Deterministic
                system="You are an expert medical coder taking a CPC practice test. Answer with only the letter (A, B, C, or D) of the correct answer.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response
            answer = response.content[0].text.strip()
            
            # Get token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            # Update metrics
            self.total_tokens += total_tokens
            self.request_count += 1
            
            # Calculate cost
            costs = self.get_cost_per_1k_tokens()
            cost = (input_tokens * costs['input'] + output_tokens * costs['output']) / 1000
            self.total_cost += cost
            
            return {
                'response': answer,
                'tokens_used': total_tokens,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'latency': time.time() - start_time,
                'cost': cost
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Get Anthropic pricing per 1k tokens."""
        # Pricing as of Nov 2024
        if "claude-3-5-sonnet" in self.model_name:
            return {'input': 3.0, 'output': 15.0}  # $3/$15 per 1M tokens
        elif "claude-3-opus" in self.model_name:
            return {'input': 15.0, 'output': 75.0}  # $15/$75 per 1M tokens
        elif "claude-3-haiku" in self.model_name:
            return {'input': 0.25, 'output': 1.25}  # $0.25/$1.25 per 1M tokens
        else:
            # Default to Sonnet pricing
            return {'input': 3.0, 'output': 15.0}


class GoogleProvider(ModelProvider):
    """Google model provider for Gemini models."""
    
    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        
        # Initialize Google AI client
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.0,  # Deterministic
                "max_output_tokens": 10,
            }
        )
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, max_tokens: int = 10) -> Dict[str, Any]:
        """Generate response using Google Gemini API."""
        start_time = time.time()
        
        try:
            # Add system instruction to prompt
            full_prompt = (
                "You are an expert medical coder taking a CPC practice test. "
                "Answer with only the letter (A, B, C, or D) of the correct answer.\n\n"
                + prompt
            )
            
            response = self.model.generate_content(full_prompt)
            
            # Extract response
            answer = response.text.strip()
            
            # Note: Gemini API doesn't provide detailed token counts in the same way
            # We'll estimate based on the response
            estimated_tokens = len(prompt.split()) + len(answer.split())
            
            # Update metrics
            self.total_tokens += estimated_tokens
            self.request_count += 1
            
            # Calculate cost (Gemini is often free for small usage)
            costs = self.get_cost_per_1k_tokens()
            cost = estimated_tokens * costs['combined'] / 1000
            self.total_cost += cost
            
            return {
                'response': answer,
                'tokens_used': estimated_tokens,
                'input_tokens': len(prompt.split()),
                'output_tokens': len(answer.split()),
                'latency': time.time() - start_time,
                'cost': cost
            }
            
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            raise
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Get Google Gemini pricing per 1k tokens."""
        # Gemini pricing structure is different (often has free tier)
        # Using approximate values as of Nov 2024
        if "gemini-1.5-pro" in self.model_name:
            return {'combined': 0.0035, 'input': 0.00125, 'output': 0.00375}  # $3.50 per 1M tokens combined
        elif "gemini-1.5-flash" in self.model_name:
            return {'combined': 0.00035, 'input': 0.000075, 'output': 0.0003}  # $0.35 per 1M tokens combined
        else:
            return {'combined': 0.0035, 'input': 0.00125, 'output': 0.00375} 