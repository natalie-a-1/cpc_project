"""
Conditions API tool for querying the Clinical Tables NLM Conditions database
"""
import requests
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConditionsApi:
    """
    API wrapper for the Clinical Tables NLM Conditions database
    
    Provides access to over 2,400 medical conditions with ICD-10-CM codes, 
    ICD-9-CM codes, and extensive synonyms from the Regenstrief Institute's
    Medical Gopher program.
    
    Based on: https://clinicaltables.nlm.nih.gov/apidoc/conditions/v3/doc.html
    """
    
    BASE_URL = "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search"
    
    def __init__(self):
        """Initialize the Conditions API client"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CPC-Agent/1.0'
        })
    
    def search_conditions(self, 
                         terms: str, 
                         max_results: int = 10,
                         include_details: bool = True) -> Dict[str, Any]:
        """
        Search for medical conditions by terms
        
        Args:
            terms: Search string (condition name or keywords)
            max_results: Maximum number of results to return (max 500)
            include_details: Whether to include detailed condition information
            
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
                params['ef'] = 'primary_name,consumer_name,icd10cm_codes,icd10cm,term_icd9_code,term_icd9_text,word_synonyms,synonyms,info_link_data'
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the NLM API response format
            # Format: [total_results, codes_array, extra_data_hash, display_strings_array, code_systems_array]
            if len(data) < 4:
                return {
                    'success': False,
                    'error': 'Invalid response format from Conditions API',
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
                    if 'icd10cm_codes' in extra_data and i < len(extra_data['icd10cm_codes']):
                        result['icd10cm_codes'] = extra_data['icd10cm_codes'][i]
                    if 'icd10cm' in extra_data and i < len(extra_data['icd10cm']):
                        result['icd10cm'] = extra_data['icd10cm'][i]
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
                
                # Add condition category classification
                result['category'] = self._classify_condition(result.get('primary_name', '') or result.get('display', ''))
                
                results.append(result)
            
            return {
                'success': True,
                'total_results': total_results,
                'returned_count': len(results),
                'search_terms': terms,
                'results': results
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Conditions API request failed: {e}")
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
                'results': []
            }
        except Exception as e:
            logger.error(f"Conditions API error: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'results': []
            }
    
    def get_condition_details(self, key_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific condition by key_id
        
        Args:
            key_id: The unique identifier for the condition
            
        Returns:
            Dict with condition details or error information
        """
        try:
            params = {
                'terms': key_id,
                'maxList': 1,
                'df': 'consumer_name',
                'sf': 'key_id',  # Search only in key_id field for exact match
                'ef': 'primary_name,consumer_name,icd10cm_codes,icd10cm,term_icd9_code,term_icd9_text,word_synonyms,synonyms,info_link_data'
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 4 or not data[1]:
                return {
                    'success': False,
                    'error': f'Condition with key_id {key_id} not found',
                    'key_id': key_id
                }
            
            key_ids = data[1]
            extra_data = data[2] if data[2] else {}
            display_strings = data[3] if data[3] else []
            
            # Check if we got an exact match
            if key_ids[0] != key_id:
                return {
                    'success': False,
                    'error': f'Exact match for condition key_id {key_id} not found',
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
                if 'icd10cm_codes' in extra_data and extra_data['icd10cm_codes']:
                    result['icd10cm_codes'] = extra_data['icd10cm_codes'][0]
                if 'icd10cm' in extra_data and extra_data['icd10cm']:
                    result['icd10cm'] = extra_data['icd10cm'][0]
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
            result['category'] = self._classify_condition(result.get('primary_name', '') or result.get('display', ''))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting condition details: {e}")
            return {
                'success': False,
                'error': f'Error retrieving condition details: {str(e)}',
                'key_id': key_id
            }
    
    def search_by_category(self, category_terms: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Search for conditions by category or type
        
        Args:
            category_terms: Terms describing the category (e.g., "cardiovascular", "diabetes", "cancer")
            max_results: Maximum number of results
            
        Returns:
            Dict with categorized search results
        """
        # Use the regular search but enhance with condition-specific terms
        results = self.search_conditions(category_terms, max_results, include_details=True)
        
        if results['success']:
            # Results already include category classification from search_conditions
            pass
        
        return results
    
    def _classify_condition(self, condition_name: str) -> str:
        """
        Classify condition by its name/description into broad medical categories
        
        Based on common medical condition categories
        """
        if not condition_name:
            return 'Unknown'
        
        name_lower = condition_name.lower()
        
        # Define condition categories based on common medical terminology
        categories = {
            'Cardiovascular': ['heart', 'cardiac', 'hypertension', 'blood pressure', 'artery', 'vascular', 'circulation', 'angina', 'stroke'],
            'Respiratory': ['lung', 'asthma', 'pneumonia', 'respiratory', 'bronch', 'pulmonary', 'breathing', 'cough'],
            'Endocrine/Metabolic': ['diabetes', 'thyroid', 'hormone', 'metabolic', 'endocrine', 'insulin', 'glucose'],
            'Gastrointestinal': ['stomach', 'intestin', 'bowel', 'digest', 'gastro', 'liver', 'gallbladder', 'colon'],
            'Neurological': ['brain', 'nerve', 'neuro', 'seizure', 'headache', 'migraine', 'alzheimer', 'parkinson'],
            'Musculoskeletal': ['bone', 'joint', 'muscle', 'arthritis', 'fracture', 'back pain', 'osteo'],
            'Infectious Disease': ['infection', 'bacterial', 'viral', 'fungal', 'sepsis', 'pneumonia', 'flu'],
            'Cancer/Oncology': ['cancer', 'tumor', 'malignant', 'carcinoma', 'leukemia', 'lymphoma', 'oncolog'],
            'Dermatological': ['skin', 'rash', 'dermatitis', 'eczema', 'psoriasis', 'dermat'],
            'Genitourinary': ['kidney', 'bladder', 'urinary', 'renal', 'prostate', 'urolog'],
            'Mental Health': ['depression', 'anxiety', 'mental', 'psychiatric', 'bipolar', 'schizo'],
            'Hematological': ['blood', 'anemia', 'bleeding', 'clotting', 'hematolog'],
            'Immunological': ['immune', 'allergy', 'autoimmune', 'lupus', 'immunolog'],
            'Reproductive': ['pregnancy', 'menstrual', 'reproductive', 'gynecolog', 'obstetric'],
            'Pediatric': ['child', 'infant', 'pediatric', 'congenital', 'birth defect']
        }
        
        # Check each category for matching terms
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'General Medical'
    
    def validate_key_id_format(self, key_id: str) -> bool:
        """
        Validate if a string could be a valid condition key_id
        
        Key IDs appear to be numeric strings based on the API documentation
        """
        if not key_id:
            return False
        
        return key_id.isdigit() and len(key_id) <= 10  # Reasonable bounds for numeric IDs 