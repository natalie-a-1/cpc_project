"""
Procedures API tool for querying the Clinical Tables NLM Procedures database
"""
import requests
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ProceduresApi:
    """
    API wrapper for the Clinical Tables NLM Procedures database
    
    Provides access to Major surgeries and implants procedures (about 280)
    from the Regenstrief Institute's Medical Gopher program with extensive synonyms.
    
    Based on: https://clinicaltables.nlm.nih.gov/apidoc/procedures/v3/doc.html
    """
    
    BASE_URL = "https://clinicaltables.nlm.nih.gov/api/procedures/v3/search"
    
    def __init__(self):
        """Initialize the Procedures API client"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CPC-Agent/1.0'
        })
    
    def search_procedures(self, 
                         terms: str, 
                         max_results: int = 10,
                         include_details: bool = True) -> Dict[str, Any]:
        """
        Search for procedures by terms
        
        Args:
            terms: Search string (procedure name or keywords)
            max_results: Maximum number of results to return (max 500)
            include_details: Whether to include detailed procedure information
            
        Returns:
            Dict with search results and metadata
        """
        try:
            params = {
                'terms': terms,
                'maxList': min(max_results, 500),
                'df': 'consumer_name',  # Default display field
                'sf': 'consumer_name,primary_name,word_synonyms,synonyms,term_icd9_code,term_icd9_text',  # Search fields
                'cf': 'key_id'  # Code field (unique identifier)
            }
            
            if include_details:
                params['ef'] = 'primary_name,consumer_name,term_icd9_code,term_icd9_text,word_synonyms,synonyms,info_link_data'
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the NLM API response format
            # Format: [total_results, codes_array, extra_data_hash, display_strings_array, code_systems_array]
            if len(data) < 4:
                return {
                    'success': False,
                    'error': 'Invalid response format from Procedures API',
                    'results': []
                }
            
            total_results = data[0]
            key_ids = data[1] if data[1] else []
            extra_data = data[2] if data[2] else {}
            display_strings = data[3] if data[3] else []
            
            # Build structured results
            results = []
            for i, key_id in enumerate(key_ids):
                result = {
                    'key_id': key_id,
                    'display': display_strings[i][0] if i < len(display_strings) and len(display_strings[i]) > 0 else '',
                }
                
                # Add extra details if requested
                if include_details and extra_data:
                    if 'primary_name' in extra_data and i < len(extra_data['primary_name']):
                        result['primary_name'] = extra_data['primary_name'][i]
                    if 'consumer_name' in extra_data and i < len(extra_data['consumer_name']):
                        result['consumer_name'] = extra_data['consumer_name'][i]
                    if 'term_icd9_code' in extra_data and i < len(extra_data['term_icd9_code']):
                        result['icd9_code'] = extra_data['term_icd9_code'][i]
                    if 'term_icd9_text' in extra_data and i < len(extra_data['term_icd9_text']):
                        result['icd9_text'] = extra_data['term_icd9_text'][i]
                    if 'word_synonyms' in extra_data and i < len(extra_data['word_synonyms']):
                        result['word_synonyms'] = extra_data['word_synonyms'][i]
                    if 'synonyms' in extra_data and i < len(extra_data['synonyms']):
                        result['synonyms'] = extra_data['synonyms'][i]
                    if 'info_link_data' in extra_data and i < len(extra_data['info_link_data']):
                        result['info_links'] = extra_data['info_link_data'][i]
                
                # Add procedure category classification
                result['category'] = self._classify_procedure(result.get('primary_name', '') or result.get('display', ''))
                
                results.append(result)
            
            return {
                'success': True,
                'total_results': total_results,
                'returned_count': len(results),
                'search_terms': terms,
                'results': results
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Procedures API request failed: {e}")
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
                'results': []
            }
        except Exception as e:
            logger.error(f"Procedures API error: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'results': []
            }
    
    def get_procedure_details(self, key_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific procedure by key_id
        
        Args:
            key_id: The unique identifier for the procedure
            
        Returns:
            Dict with procedure details or error information
        """
        try:
            params = {
                'terms': key_id,
                'maxList': 1,
                'df': 'consumer_name',
                'sf': 'key_id',  # Search only in key_id field for exact match
                'ef': 'primary_name,consumer_name,term_icd9_code,term_icd9_text,word_synonyms,synonyms,info_link_data'
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 4 or not data[1]:
                return {
                    'success': False,
                    'error': f'Procedure with key_id {key_id} not found',
                    'key_id': key_id
                }
            
            key_ids = data[1]
            extra_data = data[2] if data[2] else {}
            display_strings = data[3] if data[3] else []
            
            # Check if we got an exact match
            if key_ids[0] != key_id:
                return {
                    'success': False,
                    'error': f'Exact match for procedure key_id {key_id} not found',
                    'key_id': key_id
                }
            
            result = {
                'success': True,
                'key_id': key_ids[0],
                'display': display_strings[0][0] if display_strings and len(display_strings[0]) > 0 else '',
            }
            
            # Add detailed information
            if extra_data:
                if 'primary_name' in extra_data and extra_data['primary_name']:
                    result['primary_name'] = extra_data['primary_name'][0]
                if 'consumer_name' in extra_data and extra_data['consumer_name']:
                    result['consumer_name'] = extra_data['consumer_name'][0]
                if 'term_icd9_code' in extra_data and extra_data['term_icd9_code']:
                    result['icd9_code'] = extra_data['term_icd9_code'][0]
                if 'term_icd9_text' in extra_data and extra_data['term_icd9_text']:
                    result['icd9_text'] = extra_data['term_icd9_text'][0]
                if 'word_synonyms' in extra_data and extra_data['word_synonyms']:
                    result['word_synonyms'] = extra_data['word_synonyms'][0]
                if 'synonyms' in extra_data and extra_data['synonyms']:
                    result['synonyms'] = extra_data['synonyms'][0]
                if 'info_link_data' in extra_data and extra_data['info_link_data']:
                    result['info_links'] = extra_data['info_link_data'][0]
            
            # Add category classification
            result['category'] = self._classify_procedure(result.get('primary_name', '') or result.get('display', ''))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting procedure details: {e}")
            return {
                'success': False,
                'error': f'Error retrieving procedure details: {str(e)}',
                'key_id': key_id
            }
    
    def search_by_category(self, category_terms: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Search for procedures by category or type
        
        Args:
            category_terms: Terms describing the category (e.g., "cardiac", "orthopedic", "transplant")
            max_results: Maximum number of results
            
        Returns:
            Dict with categorized search results
        """
        # Use the regular search but enhance with procedure-specific terms
        results = self.search_procedures(category_terms, max_results, include_details=True)
        
        if results['success']:
            # Results already include category classification from search_procedures
            pass
        
        return results
    
    def _classify_procedure(self, procedure_name: str) -> str:
        """
        Classify procedure by its name/description into broad categories
        
        Based on common surgical and medical procedure categories
        """
        if not procedure_name:
            return 'Unknown'
        
        name_lower = procedure_name.lower()
        
        # Define procedure categories based on common medical terminology
        categories = {
            'Cardiac/Cardiovascular': ['heart', 'cardiac', 'coronary', 'valve', 'bypass', 'angioplasty', 'pacemaker', 'defibrillator'],
            'Orthopedic': ['joint', 'bone', 'fracture', 'arthroscop', 'replacement', 'hip', 'knee', 'spine', 'spinal'],
            'Neurological': ['brain', 'spinal', 'neurolog', 'cranial', 'neurosurg'],
            'Gastrointestinal': ['gastric', 'intestin', 'colon', 'stomach', 'liver', 'gallbladder', 'appendectomy'],
            'Transplant': ['transplant', 'graft', 'donor'],
            'Cancer/Oncology': ['tumor', 'cancer', 'oncolog', 'resection', 'biopsy'],
            'Vascular': ['vascular', 'artery', 'vein', 'vessel'],
            'Respiratory': ['lung', 'respiratory', 'thorac', 'bronch'],
            'Urological': ['kidney', 'bladder', 'urolog', 'prostate'],
            'Reproductive': ['hysterectomy', 'cesarean', 'reproductive', 'gynecolog'],
            'Ophthalmic': ['eye', 'retina', 'cataract', 'ophthalm'],
            'ENT': ['ear', 'nose', 'throat', 'tonsil'],
            'Plastic/Reconstructive': ['plastic', 'reconstructive', 'cosmetic'],
            'Emergency': ['emergency', 'trauma', 'repair'],
            'Implant': ['implant', 'prosth', 'device']
        }
        
        # Check each category for matching terms
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'General Surgery'
    
    def validate_key_id_format(self, key_id: str) -> bool:
        """
        Validate if a string could be a valid procedure key_id
        
        Key IDs appear to be numeric strings based on the API documentation
        """
        if not key_id:
            return False
        
        return key_id.isdigit() and len(key_id) <= 10  # Reasonable bounds for numeric IDs 