"""
Enhanced FAISS vector database builder for CPC test
"""
import json
import numpy as np
import faiss
from typing import List, Dict, Any
from pathlib import Path
from .embedding_generator import EmbeddingGenerator

class MedicalVectorizer:
    """Enhanced FAISS vector database builder for CPC test accuracy"""
    
    def __init__(self, api_key: str):
        self.embedding_generator = EmbeddingGenerator(api_key)
        self.dimension = 1536  # Will be updated based on actual embeddings
    
    def build_vector_database(self, code_data: List[Dict[str, Any]], output_dir: Path):
        """Build FAISS vector database with enhanced embeddings"""
        print("Building enhanced FAISS vector database...")
        
        # Prepare enhanced embeddings with additional context
        enhanced_data = self._enhance_code_data(code_data)
        
        # Generate embeddings
        texts = [item['enhanced_text'] for item in enhanced_data]
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        # Create FAISS index with Inner Product (cosine similarity after L2 normalization)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Debug: Check embedding dimensions
        print(f"Embeddings array shape: {embeddings_array.shape}")
        print(f"Expected dimension: {self.dimension}")
        
        # If embeddings have wrong dimension, fix it
        if embeddings_array.shape[1] != self.dimension:
            print(f"Warning: Embedding dimension mismatch. Got {embeddings_array.shape[1]}, expected {self.dimension}")
            # Update dimension to match actual embeddings
            self.dimension = embeddings_array.shape[1]
        
        faiss.normalize_L2(embeddings_array)
        
        # Use IndexFlatIP for exact search (best for CPC test accuracy)
        index = faiss.IndexFlatIP(self.dimension)
        index.add(embeddings_array)
        
        # Save index
        index_path = output_dir / "medical_codes.faiss"
        faiss.write_index(index, str(index_path))
        
        # Save enhanced metadata
        metadata = []
        for i, item in enumerate(enhanced_data):
            metadata.append({
                'index': i,
                'code': item['code'],
                'description': item['description'],
                'code_type': item['code_type'],
                'enhanced_text': item['enhanced_text'],
                'original_text': item.get('text_for_embedding', ''),
                'level': item.get('level', ''),
                'section': item.get('section', ''),
                'short_description': item.get('short_description', '')
            })
        
        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved enhanced FAISS index with {index.ntotal} vectors to {index_path}")
        print(f"Saved enhanced metadata to {metadata_path}")
        
        return index
    
    def _enhance_code_data(self, code_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance code data with additional context for better retrieval"""
        enhanced_data = []
        
        for item in code_data:
            code = item['code']
            description = item['description']
            code_type = item['code_type']
            
            # Build enhanced text with multiple representations
            enhanced_parts = []
            
            # Include the code and type
            enhanced_parts.append(f"{code_type} code {code}")
            
            # Include the full description
            enhanced_parts.append(description)
            
            # Add code-specific enhancements
            if code_type == 'CPT':
                # Add procedure-related keywords
                if any(word in description.lower() for word in ['excision', 'removal', 'incision']):
                    enhanced_parts.append("surgical procedure")
                if any(word in description.lower() for word in ['exam', 'evaluation', 'assessment']):
                    enhanced_parts.append("evaluation and management")
                if 'biopsy' in description.lower():
                    enhanced_parts.append("tissue sampling diagnostic procedure")
                    
            elif code_type == 'ICD-10-CM':
                # Add diagnosis-related keywords
                if code.startswith('I'):
                    enhanced_parts.append("circulatory system disease")
                elif code.startswith('E'):
                    enhanced_parts.append("endocrine nutritional metabolic disease")
                elif code.startswith('M'):
                    enhanced_parts.append("musculoskeletal system disease")
                elif code.startswith('G'):
                    enhanced_parts.append("nervous system disease")
                elif code.startswith('J'):
                    enhanced_parts.append("respiratory system disease")
                elif code.startswith('N'):
                    enhanced_parts.append("genitourinary system disease")
                    
            elif code_type == 'HCPCS':
                # Add supply/equipment keywords
                if code.startswith('E'):
                    enhanced_parts.append("durable medical equipment DME")
                elif code.startswith('L'):
                    enhanced_parts.append("orthotic prosthetic device")
                elif code.startswith('J'):
                    enhanced_parts.append("drug injection medication")
                elif code.startswith('A'):
                    enhanced_parts.append("medical surgical supply")
            
            # Include any section information
            if 'section' in item and item['section']:
                enhanced_parts.append(item['section'])
            
            # Include level information for HCPCS
            if 'level' in item and item['level']:
                enhanced_parts.append(item['level'])
            
            # Create enhanced text
            enhanced_text = " | ".join(enhanced_parts)
            
            enhanced_item = item.copy()
            enhanced_item['enhanced_text'] = enhanced_text
            enhanced_data.append(enhanced_item)
        
        return enhanced_data 