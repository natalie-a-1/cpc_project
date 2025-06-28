"""
HCPCS API tool for querying the Clinical Tables NLM HCPCS Level II database
"""
import requests
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class HCPCSApi:
    """
    API wrapper for the Clinical Tables NLM HCPCS Level II database
    
    Provides access to Healthcare Common Procedure Coding System Level II codes
    which cover items, supplies, and non-physician services not covered by CPT codes.
    
    Based on: https://clinicaltables.nlm.nih.gov/apidoc/hcpcs/v3/doc.html
    """
    
    BASE_URL = "https://clinicaltables.nlm.nih.gov/api/hcpcs/v3/search"
    
    def __init__(self):
        """Initialize the HCPCS API client"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CPC-Agent/1.0'
        })
    
    def search_codes(self, 
                    terms: str, 
                    max_results: int = 10,
                    include_details: bool = True) -> Dict[str, Any]:
        """
        Search for HCPCS codes by terms
        
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
                'maxList': min(max_results, 500),
                'df': 'code,display',  # Display fields
                'sf': 'code,short_desc,long_desc',  # Search fields
                'cf': 'code'  # Code field
            }
            
            if include_details:
                params['ef'] = 'short_desc,long_desc,add_dt,term_dt,obsolete,is_noc'
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the NLM API response format
            # Format: [total_results, codes_array, extra_data_hash, display_strings_array, code_systems_array]
            if len(data) < 4:
                return {
                    'success': False,
                    'error': 'Invalid response format from HCPCS API',
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
                
                # Add extra details if requested
                if include_details and extra_data:
                    if 'short_desc' in extra_data and i < len(extra_data['short_desc']):
                        result['short_description'] = extra_data['short_desc'][i]
                    if 'long_desc' in extra_data and i < len(extra_data['long_desc']):
                        result['long_description'] = extra_data['long_desc'][i]
                    if 'add_dt' in extra_data and i < len(extra_data['add_dt']):
                        result['add_date'] = extra_data['add_dt'][i]
                    if 'term_dt' in extra_data and i < len(extra_data['term_dt']):
                        result['term_date'] = extra_data['term_dt'][i]
                    if 'obsolete' in extra_data and i < len(extra_data['obsolete']):
                        result['obsolete'] = extra_data['obsolete'][i]
                    if 'is_noc' in extra_data and i < len(extra_data['is_noc']):
                        result['is_not_otherwise_classified'] = extra_data['is_noc'][i]
                
                results.append(result)
            
            return {
                'success': True,
                'total_results': total_results,
                'returned_count': len(results),
                'search_terms': terms,
                'results': results
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HCPCS API request failed: {e}")
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
                'results': []
            }
        except Exception as e:
            logger.error(f"HCPCS API error: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'results': []
            }
    
    def get_code_details(self, code: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific HCPCS code
        
        Args:
            code: The HCPCS code to look up
            
        Returns:
            Dict with code details or error information
        """
        try:
            params = {
                'terms': code,
                'maxList': 1,
                'df': 'code,display',
                'sf': 'code',  # Search only in code field for exact match
                'ef': 'short_desc,long_desc,add_dt,term_dt,act_eff_dt,obsolete,is_noc'
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 4 or not data[1]:
                return {
                    'success': False,
                    'error': f'HCPCS code {code} not found',
                    'code': code
                }
            
            codes = data[1]
            extra_data = data[2] if data[2] else {}
            display_strings = data[3] if data[3] else []
            
            # Check if we got an exact match
            if codes[0].upper() != code.upper():
                return {
                    'success': False,
                    'error': f'Exact match for HCPCS code {code} not found',
                    'code': code
                }
            
            result = {
                'success': True,
                'code': codes[0],
                'display': display_strings[0][1] if display_strings and len(display_strings[0]) > 1 else '',
            }
            
            # Add detailed information
            if extra_data:
                if 'short_desc' in extra_data and extra_data['short_desc']:
                    result['short_description'] = extra_data['short_desc'][0]
                if 'long_desc' in extra_data and extra_data['long_desc']:
                    result['long_description'] = extra_data['long_desc'][0]
                if 'add_dt' in extra_data and extra_data['add_dt']:
                    result['add_date'] = extra_data['add_dt'][0]
                if 'term_dt' in extra_data and extra_data['term_dt']:
                    result['term_date'] = extra_data['term_dt'][0]
                if 'act_eff_dt' in extra_data and extra_data['act_eff_dt']:
                    result['effective_date'] = extra_data['act_eff_dt'][0]
                if 'obsolete' in extra_data and extra_data['obsolete']:
                    result['obsolete'] = extra_data['obsolete'][0]
                if 'is_noc' in extra_data and extra_data['is_noc']:
                    result['is_not_otherwise_classified'] = extra_data['is_noc'][0]
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting HCPCS code details: {e}")
            return {
                'success': False,
                'error': f'Error retrieving code details: {str(e)}',
                'code': code
            }
    
    def search_by_category(self, category_terms: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Search for HCPCS codes by category or equipment type
        
        Args:
            category_terms: Terms describing the category (e.g., "wheelchair", "oxygen", "prosthetic")
            max_results: Maximum number of results
            
        Returns:
            Dict with categorized search results
        """
        # Use the regular search but filter for common medical equipment/supply terms
        results = self.search_codes(category_terms, max_results, include_details=True)
        
        if results['success']:
            # Add category classification
            for result in results['results']:
                result['category'] = self._classify_hcpcs_code(result['code'])
        
        return results
    
    def _classify_hcpcs_code(self, code: str) -> str:
        """
        Classify HCPCS code by its prefix according to standard categories
        
        Based on HCPCS Level II code structure from the API documentation
        """
        if not code:
            return 'Unknown'
        
        prefix = code[0].upper()
        
        category_map = {
            'A': 'Transportation Services, Medical and Surgical Supplies',
            'B': 'Enteral and Parenteral Therapy', 
            'C': 'Outpatient PPS',
            'D': 'Dental Procedures',
            'E': 'Durable Medical Equipment',
            'G': 'Procedures/Professional Services (Temporary)',
            'H': 'Alcohol and Drug Abuse Treatment Services',
            'J': 'Drugs Administered Other Than Oral Method',
            'K': 'Temporary Codes for Durable Medical Equipment',
            'L': 'Orthotic/Prosthetic Procedures',
            'M': 'Other Medical Services', 
            'P': 'Pathology and Laboratory Services',
            'Q': 'Temporary Codes',
            'R': 'Diagnostic Radiology Services',
            'S': 'Temporary National Codes',
            'T': 'National T-Codes',
            'V': 'Vision Services'
        }
        
        return category_map.get(prefix, f'Category {prefix}')
    
    def validate_code_format(self, code: str) -> bool:
        """
        Validate if a string follows HCPCS Level II format
        
        HCPCS Level II codes are alphanumeric: Letter + 4 digits (e.g., E0100, A4450)
        """
        if not code or len(code) != 5:
            return False
        
        return (code[0].isalpha() and 
                code[1:].isdigit() and 
                code[0].upper() in 'ABCDEGHJKLMPQRSTV') 