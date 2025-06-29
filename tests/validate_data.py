"""
Data validation for CPC test accuracy
"""
from typing import List, Dict, Any
import json

def validate_parsed_data(parsed_data: List[Dict[str, Any]], test_codes: List[str]) -> Dict[str, Any]:
    """Validate that parsed data contains codes from CPC test"""
    
    # Create lookup by code
    code_lookup = {item['code']: item for item in parsed_data}
    
    # Check test codes
    found_codes = []
    missing_codes = []
    
    for test_code in test_codes:
        if test_code in code_lookup:
            found_codes.append({
                'code': test_code,
                'description': code_lookup[test_code]['description'],
                'type': code_lookup[test_code]['code_type']
            })
        else:
            missing_codes.append(test_code)
    
    return {
        'total_test_codes': len(test_codes),
        'found': len(found_codes),
        'missing': len(missing_codes),
        'found_codes': found_codes,
        'missing_codes': missing_codes,
        'coverage': len(found_codes) / len(test_codes) * 100 if test_codes else 0
    }

# Sample CPC test codes from the exam questions
CPC_TEST_CODES = [
    # CPT codes from test
    "41113", "10060", "20020", "83036", "60220", "50543", "31231", "31256",
    "60500", "73110", "40804", "52000", "99381", "80053", "30110", "70551",
    "99223", "40820", "99213", "50200", "00524", "20005", "41115", "00144",
    "76805", "30903", "71260", "90832", "45378", "99223", "66984", "85025",
    "00860", "10080", "94010", "20100", "11200", "30901", "41105", "93620",
    "10120", "20005", "97110", "97161", "99202", "60210", "52334", "11100",
    "00580", "76856", "62323", "69210", "45385", "99214", "64483", "99232",
    
    # ICD-10-CM codes from test
    "I10", "A90", "M17.1", "J01.11", "N80.0", "E10.9", "D50.0", "G43.009",
    
    # HCPCS codes from test  
    "K0001", "A4465", "J1040", "E0601", "J1745", "L5637", "J0585",
    
    # Medical terms that should be in terminology
    "Bradycardia", "Osteoporosis", "Hyperglycemia", "Cardiomyopathy", 
    "Hepatomegaly", "HIPAA", "NCCI", "Upcoding", "RVU"
]

def validate_cpc_coverage(data_path: str) -> None:
    """Validate CPC test coverage from parsed data file"""
    try:
        with open(data_path, 'r') as f:
            parsed_data = json.load(f)
        
        results = validate_parsed_data(parsed_data, CPC_TEST_CODES)
        
        print(f"\n📊 CPC Test Code Coverage Analysis:")
        print(f"   Total test codes: {results['total_test_codes']}")
        print(f"   Found: {results['found']} ({results['coverage']:.1f}%)")
        print(f"   Missing: {results['missing']}")
        
        if results['missing_codes']:
            print(f"\n⚠️  Missing codes: {', '.join(results['missing_codes'][:10])}")
            if len(results['missing_codes']) > 10:
                print(f"   ... and {len(results['missing_codes']) - 10} more")
        
        # Check code types distribution
        code_types = {}
        for item in parsed_data:
            ct = item.get('code_type', 'Unknown')
            code_types[ct] = code_types.get(ct, 0) + 1
        
        print(f"\n📈 Data Distribution:")
        for ct, count in sorted(code_types.items()):
            print(f"   {ct}: {count}")
            
    except Exception as e:
        print(f"❌ Validation error: {e}") 