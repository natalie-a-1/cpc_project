"""
Simple embedding generator using OpenAI
"""
import openai
import numpy as np
from typing import List
from tqdm import tqdm
import time

class EmbeddingGenerator:
    """Simple embedding generator"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-large"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        # Model dimensions mapping
        self.model_dimensions = {
            "text-embedding-3-large": 1536,
            "text-embedding-3-small": 512,
            "text-embedding-ada-002": 1536
        }
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for texts"""
        print(f"Generating embeddings for {len(texts)} texts...")
        
        all_embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size)):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model,
                    dimensions=1536  # Explicitly request 1536 dimensions
                )
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Add zero vectors as fallback with correct dimension
                expected_dim = self.model_dimensions.get(self.model, 1536)
                zero_vectors = [[0.0] * expected_dim for _ in batch]
                all_embeddings.extend(zero_vectors)
        
        # Validate embeddings before returning
        if not all_embeddings:
            raise ValueError("No embeddings were generated")
        
        # Check dimension consistency
        first_dim = len(all_embeddings[0])
        for i, emb in enumerate(all_embeddings):
            if len(emb) != first_dim:
                print(f"Warning: Embedding {i} has dimension {len(emb)}, expected {first_dim}")
        
        print(f"Generated {len(all_embeddings)} embeddings with dimension {first_dim}")
        return all_embeddings 