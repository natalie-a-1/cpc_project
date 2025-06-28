"""
Tests for validate_data module
"""
import pytest
import json
import tempfile
import os
from tests.validate_data import validate_parsed_data, validate_cpc_coverage, CPC_TEST_CODES

class TestValidateData:
    """Test the validation functionality"""
    
    def test_validate_parsed_data_all_found(self):
        """Test validation when all codes are found"""
        parsed_data = [
            {'code': 'I10', 'description': 'Essential hypertension', 'code_type': 'ICD-10-CM'},
            {'code': '99213', 'description': 'Office visit', 'code_type': 'CPT'},
            {'code': 'K0001', 'description': 'Standard wheelchair', 'code_type': 'HCPCS'}
        ]
        test_codes = ['I10', '99213', 'K0001']
        
        results = validate_parsed_data(parsed_data, test_codes)
        
        assert results['total_test_codes'] == 3
        assert results['found'] == 3
        assert results['missing'] == 0
        assert results['coverage'] == 100.0
        assert len(results['found_codes']) == 3
        assert len(results['missing_codes']) == 0
    
    def test_validate_parsed_data_partial_found(self):
        """Test validation when some codes are missing"""
        parsed_data = [
            {'code': 'I10', 'description': 'Essential hypertension', 'code_type': 'ICD-10-CM'},
            {'code': '99213', 'description': 'Office visit', 'code_type': 'CPT'}
        ]
        test_codes = ['I10', '99213', 'K0001', 'J1040']
        
        results = validate_parsed_data(parsed_data, test_codes)
        
        assert results['total_test_codes'] == 4
        assert results['found'] == 2
        assert results['missing'] == 2
        assert results['coverage'] == 50.0
        assert 'K0001' in results['missing_codes']
        assert 'J1040' in results['missing_codes']
    
    def test_validate_parsed_data_empty(self):
        """Test validation with empty data"""
        results = validate_parsed_data([], [])
        
        assert results['total_test_codes'] == 0
        assert results['found'] == 0
        assert results['missing'] == 0
        assert results['coverage'] == 0
    
    def test_validate_cpc_coverage_file(self):
        """Test the file-based validation function"""
        # Create a temporary test file
        test_data = [
            {'code': 'I10', 'description': 'Essential hypertension', 'code_type': 'ICD-10-CM'},
            {'code': '99213', 'description': 'Office visit', 'code_type': 'CPT'},
            {'code': 'K0001', 'description': 'Standard wheelchair', 'code_type': 'HCPCS'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            # Capture output
            import io
            import sys
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            validate_cpc_coverage(temp_file)
            
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()
            
            # Check that output contains expected information
            assert 'CPC Test Code Coverage Analysis' in output
            assert 'Data Distribution' in output
            assert 'CPT: 1' in output
            assert 'ICD-10-CM: 1' in output
            assert 'HCPCS: 1' in output
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_cpc_test_codes_not_empty(self):
        """Test that CPC_TEST_CODES constant contains expected codes"""
        assert len(CPC_TEST_CODES) > 0
        
        # Check for some expected code types
        cpt_codes = [code for code in CPC_TEST_CODES if code.isdigit() and len(code) == 5]
        icd10_codes = [code for code in CPC_TEST_CODES if code and code[0].isalpha() and '.' in code or (code and code[0].isalpha() and len(code) >= 3)]
        hcpcs_codes = [code for code in CPC_TEST_CODES if code and code[0].isalpha() and len(code) == 5]
        
        assert len(cpt_codes) > 0, "Should have CPT codes"
        assert len(icd10_codes) > 0, "Should have ICD-10 codes"
        assert len(hcpcs_codes) > 0, "Should have HCPCS codes" 