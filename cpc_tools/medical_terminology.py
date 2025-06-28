"""
Medical Terminology Knowledge Base for CPC Test
"""
from typing import Dict, List, Any

class MedicalTerminology:
    """Medical terminology and anatomy knowledge for CPC test"""
    
    @staticmethod
    def get_terminology_data() -> List[Dict[str, Any]]:
        """Get medical terminology and anatomy data for vector database"""
        
        terminology = [
            # Anatomy terms from test questions
            {
                'term': 'Medulla Oblongata',
                'definition': 'Part of the brainstem responsible for regulating vital functions like heartbeat and breathing',
                'category': 'Anatomy',
                'system': 'Nervous System'
            },
            {
                'term': 'Cerebellum',
                'definition': 'Part of the brain that coordinates muscle movements and maintains posture and balance',
                'category': 'Anatomy',
                'system': 'Nervous System'
            },
            {
                'term': 'Pericardium',
                'definition': 'Double-layered sac that encloses the heart',
                'category': 'Anatomy',
                'system': 'Cardiovascular System'
            },
            {
                'term': 'Myocardium',
                'definition': 'Muscular wall of the heart',
                'category': 'Anatomy',
                'system': 'Cardiovascular System'
            },
            {
                'term': 'Endocardium',
                'definition': 'Inner lining of the heart chambers',
                'category': 'Anatomy',
                'system': 'Cardiovascular System'
            },
            {
                'term': 'Epicardium',
                'definition': 'Outermost layer of the heart wall',
                'category': 'Anatomy',
                'system': 'Cardiovascular System'
            },
            {
                'term': 'Femur',
                'definition': 'The longest and strongest bone in the human body, also known as the thigh bone',
                'category': 'Anatomy',
                'system': 'Skeletal System'
            },
            {
                'term': 'Pancreas',
                'definition': 'Organ responsible for producing insulin and digestive enzymes',
                'category': 'Anatomy',
                'system': 'Endocrine System'
            },
            
            # Medical terms from test questions
            {
                'term': 'Bradycardia',
                'definition': 'Slow heartbeat, slower than normal heart rate',
                'category': 'Medical Terminology',
                'prefix': 'brady-',
                'root': 'card',
                'suffix': '-ia'
            },
            {
                'term': 'Tachycardia',
                'definition': 'Fast heartbeat, faster than normal heart rate',
                'category': 'Medical Terminology',
                'prefix': 'tachy-',
                'root': 'card',
                'suffix': '-ia'
            },
            {
                'term': 'Osteoporosis',
                'definition': 'Condition where bones become brittle and fragile due to loss of tissue',
                'category': 'Medical Terminology',
                'prefix': 'osteo-',
                'suffix': '-porosis'
            },
            {
                'term': 'Hyperglycemia',
                'definition': 'High blood sugar level',
                'category': 'Medical Terminology',
                'prefix': 'hyper-',
                'root': 'glyc',
                'suffix': '-emia'
            },
            {
                'term': 'Hypoglycemia',
                'definition': 'Low blood sugar level',
                'category': 'Medical Terminology',
                'prefix': 'hypo-',
                'root': 'glyc',
                'suffix': '-emia'
            },
            {
                'term': 'Cardiomyopathy',
                'definition': 'Disease of the heart muscle',
                'category': 'Medical Terminology',
                'prefix': 'cardio-',
                'suffix': '-myopathy'
            },
            {
                'term': 'Hepatomegaly',
                'definition': 'Enlargement of the liver',
                'category': 'Medical Terminology',
                'prefix': 'hepato-',
                'suffix': '-megaly'
            },
            
            # Medical prefixes
            {
                'term': 'osteo-',
                'definition': 'Prefix relating to bone',
                'category': 'Medical Prefix'
            },
            {
                'term': 'cardio-',
                'definition': 'Prefix relating to heart',
                'category': 'Medical Prefix'
            },
            {
                'term': 'hepato-',
                'definition': 'Prefix relating to liver',
                'category': 'Medical Prefix'
            },
            {
                'term': 'nephro-',
                'definition': 'Prefix relating to kidney',
                'category': 'Medical Prefix'
            },
            {
                'term': 'neuro-',
                'definition': 'Prefix relating to nerves or nervous system',
                'category': 'Medical Prefix'
            },
            
            # Coding guidelines from test
            {
                'term': 'Modifier -25',
                'definition': 'CPT modifier indicating significant and separately identifiable evaluation and management service',
                'category': 'Coding Guidelines',
                'type': 'CPT Modifier'
            },
            {
                'term': 'Three-Day Payment Window Rule',
                'definition': 'Medicare rule where outpatient services provided within 3 days prior to inpatient admission are bundled with the inpatient stay',
                'category': 'Coding Guidelines',
                'type': 'Medicare Rule'
            },
            {
                'term': 'NCCI',
                'definition': 'National Correct Coding Initiative - prevents improper payment of procedures that should not be billed together',
                'category': 'Coding Guidelines',
                'type': 'Medicare'
            },
            {
                'term': 'Upcoding',
                'definition': 'Billing a higher service code than what was actually performed to receive higher reimbursement',
                'category': 'Coding Guidelines',
                'type': 'Fraud and Abuse'
            },
            {
                'term': 'HIPAA',
                'definition': 'Health Insurance Portability and Accountability Act - federal law protecting privacy and security of patient medical information',
                'category': 'Coding Guidelines',
                'type': 'Regulation'
            },
            {
                'term': 'RVU',
                'definition': 'Relative Value Unit - reflects complexity, time, and cost associated with performing a procedure',
                'category': 'Coding Guidelines',
                'type': 'Reimbursement'
            }
        ]
        
        # Convert to format compatible with code data
        formatted_data = []
        for item in terminology:
            text_parts = [item['term'], item['definition']]
            if 'category' in item:
                text_parts.append(item['category'])
            if 'system' in item:
                text_parts.append(item['system'])
            
            entry = {
                'code': item['term'],
                'description': item['definition'],
                'code_type': 'Medical Terminology',
                'text_for_embedding': ' | '.join(text_parts),
                'enhanced_text': ' | '.join(text_parts)
            }
            formatted_data.append(entry)
        
        return formatted_data 