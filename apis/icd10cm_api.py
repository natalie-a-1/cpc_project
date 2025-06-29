"""
ICD-10-CM API tool for querying the Clinical Tables NLM ICD-10-CM database
"""
import requests
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ICD10CMApi:
    """
    API wrapper for the Clinical Tables NLM ICD-10-CM database
    
    Provides access to International Classification of Diseases, 10th Revision, 
    Clinical Modification codes for medical diagnoses and reasons for visits.
    
    Based on: https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html
    """
    
    BASE_URL = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
    
    def __init__(self):
        """Initialize the ICD-10-CM API client"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CPC-Agent/1.0'
        })
    
    def search_codes(self, 
                    terms: str, 
                    max_results: int = 10,
                    include_details: bool = True) -> Dict[str, Any]:
        """
        Search for ICD-10-CM codes by terms
        
        Args:
            terms: Search string (code or description keywords)
            max_results: Maximum number of results to return (max 500)
            include_details: Whether to include detailed code information
            
        Returns:
            Dict with search results and metadata
        """
        try:
            params = {
                'terms': terms,
                'maxList': min(max_results, 500)
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the NLM API response format
            # Format: [total_results, codes_array, extra_data_hash, display_strings_array, code_systems_array]
            if len(data) < 4:
                return {
                    'success': False,
                    'error': 'Invalid response format from ICD-10-CM API',
                    'results': []
                }
            
            total_results = data[0]
            codes = data[1] if data[1] else []
            extra_data = data[2] if data[2] else {}
            display_strings = data[3] if data[3] else []
            
            # Build structured results
            results = []
            for i, code in enumerate(codes):
                result = {
                    'code': code,
                    'display': display_strings[i][1] if i < len(display_strings) and len(display_strings[i]) > 1 else '',
                }
                
                # Note: ICD-10-CM API doesn't provide additional detail fields like HCPCS
                
                # Add category classification
                result['category'] = self._classify_icd10cm_code(result['code'])
                
                results.append(result)
            
            return {
                'success': True,
                'total_results': total_results,
                'returned_count': len(results),
                'search_terms': terms,
                'results': results
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ICD-10-CM API request failed: {e}")
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
                'results': []
            }
        except Exception as e:
            logger.error(f"ICD-10-CM API error: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'results': []
            }
    
    def get_code_details(self, code: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific ICD-10-CM code
        
        Args:
            code: The ICD-10-CM code to look up
            
        Returns:
            Dict with code details or error information
        """
        try:
            params = {
                'terms': code,
                'maxList': 1
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 4 or not data[1]:
                return {
                    'success': False,
                    'error': f'ICD-10-CM code {code} not found',
                    'code': code
                }
            
            codes = data[1]
            extra_data = data[2] if data[2] else {}
            display_strings = data[3] if data[3] else []
            
            # Check if we got an exact match
            if codes[0].upper() != code.upper():
                return {
                    'success': False,
                    'error': f'Exact match for ICD-10-CM code {code} not found',
                    'code': code
                }
            
            result = {
                'success': True,
                'code': codes[0],
                'display': display_strings[0][1] if display_strings and len(display_strings[0]) > 1 else '',
                'category': self._classify_icd10cm_code(codes[0])
            }
            
            # Note: ICD-10-CM API doesn't provide additional detail fields
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting ICD-10-CM code details: {e}")
            return {
                'success': False,
                'error': f'Error retrieving code details: {str(e)}',
                'code': code
            }
    
    def search_by_category(self, category_terms: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Search for ICD-10-CM codes by category or condition type
        
        Args:
            category_terms: Terms describing the category (e.g., "diabetes", "hypertension", "cancer")
            max_results: Maximum number of results
            
        Returns:
            Dict with categorized search results
        """
        # Map common medical terms to ICD-10-CM prefixes
        condition_to_prefix = {
            'diabetes': ['E10', 'E11', 'E13'],
            'hypertension': ['I10', 'I11', 'I12', 'I13'],
            'pneumonia': ['J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18'],
            'fracture': ['S02', 'S12', 'S22', 'S32', 'S42', 'S52', 'S62', 'S72', 'S82', 'S92'],
            'cancer': ['C00', 'C01', 'C02', 'C03', 'C04', 'C05'],
            'injury': ['S00', 'S01', 'S02', 'T07', 'T14'],
            'infection': ['A00', 'A01', 'A02', 'B00', 'B01', 'B02']
        }
        
        # Try to find relevant prefixes for the search terms
        search_prefixes = []
        terms_lower = category_terms.lower()
        
        for condition, prefixes in condition_to_prefix.items():
            if condition in terms_lower:
                search_prefixes.extend(prefixes[:2])  # Limit to first 2 prefixes
                break
        
        if search_prefixes:
            # Search using the identified prefixes
            all_results = []
            for prefix in search_prefixes:
                result = self.search_codes(prefix, max_results=max_results//len(search_prefixes))
                if result.get('success') and result.get('results'):
                    all_results.extend(result['results'])
            
            return {
                'success': True,
                'total_results': len(all_results),
                'returned_count': len(all_results),
                'search_terms': category_terms,
                'results': all_results[:max_results]
            }
        
        # Fall back to regular search
        return self.search_codes(category_terms, max_results, include_details=True)
    
    def _classify_icd10cm_code(self, code: str) -> str:
        """
        Classify ICD-10-CM code by its prefix according to standard categories
        
        Based on ICD-10-CM code structure from the API documentation
        """
        if not code:
            return 'Unknown'
        
        # ICD-10-CM codes start with letter(s) followed by numbers
        prefix = code[0].upper()
        
        category_map = {
            'A': 'Certain Infectious and Parasitic Diseases (A00-B99)',
            'B': 'Certain Infectious and Parasitic Diseases (A00-B99)',
            'C': 'Neoplasms (C00-D49)',
            'D': 'Diseases of Blood/Blood-forming Organs and Immune System (D50-D89) or Neoplasms (C00-D49)',
            'E': 'Endocrine, Nutritional and Metabolic Diseases (E00-E89)',
            'F': 'Mental, Behavioral and Neurodevelopmental Disorders (F01-F99)',
            'G': 'Diseases of the Nervous System (G00-G99)',
            'H': 'Diseases of the Eye/Adnexa (H00-H59) or Diseases of Ear/Mastoid Process (H60-H95)',
            'I': 'Diseases of the Circulatory System (I00-I99)',
            'J': 'Diseases of the Respiratory System (J00-J99)',
            'K': 'Diseases of the Digestive System (K00-K95)',
            'L': 'Diseases of the Skin and Subcutaneous Tissue (L00-L99)',
            'M': 'Diseases of the Musculoskeletal System and Connective Tissue (M00-M99)',
            'N': 'Diseases of the Genitourinary System (N00-N99)',
            'O': 'Pregnancy, Childbirth and the Puerperium (O00-O9A)',
            'P': 'Certain Conditions Originating in the Perinatal Period (P00-P96)',
            'Q': 'Congenital Malformations, Deformations and Chromosomal Abnormalities (Q00-Q99)',
            'R': 'Symptoms, Signs and Abnormal Clinical and Laboratory Findings (R00-R99)',
            'S': 'Injury, Poisoning and Certain Other Consequences of External Causes (S00-T88)',
            'T': 'Injury, Poisoning and Certain Other Consequences of External Causes (S00-T88)',
            'V': 'External Causes of Morbidity (V00-Y99)',
            'W': 'External Causes of Morbidity (V00-Y99)',
            'X': 'External Causes of Morbidity (V00-Y99)',
            'Y': 'External Causes of Morbidity (V00-Y99)',
            'Z': 'Factors Influencing Health Status and Contact with Health Services (Z00-Z99)'
        }
        
        return category_map.get(prefix, f'Category {prefix}')
    
    def validate_code_format(self, code: str) -> bool:
        """
        Validate if a string follows ICD-10-CM format
        
        ICD-10-CM codes are alphanumeric: Letter(s) + numbers + optional decimal + more numbers
        Examples: I10, E11.9, S72.001A
        """
        if not code or len(code) < 3:
            return False
        
        import re
        # ICD-10-CM pattern: 1-2 letters, followed by 2+ digits, optional decimal and more digits/letters
        icd10_pattern = r'^[A-Z]{1,2}\d{2,3}(\.\d{1,4}[A-Z]?)?$'
        return bool(re.match(icd10_pattern, code.upper())) 