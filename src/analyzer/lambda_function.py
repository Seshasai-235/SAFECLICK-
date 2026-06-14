"""
SafeClick Analyzer Lambda
Analyzes website content using Amazon Bedrock Claude 3.5 Sonnet
"""

import json
import os
import base64
import re
from typing import Dict, Any, Optional
from datetime import datetime

import boto3
from bs4 import BeautifulSoup

# AWS clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda')
rekognition_client = boto3.client('rekognition', region_name='us-east-1')

# Environment variables
ARTIFACTS_BUCKET = os.environ.get('ARTIFACTS_BUCKET')
RESULTS_HANDLER_FUNCTION = os.environ.get('RESULTS_HANDLER_FUNCTION', 'safeclick-results')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Bedrock model configuration
# Using cross-region inference profile for Nova Pro (multimodal, active)
BEDROCK_MODEL_ID = 'us.amazon.nova-pro-v1:0'
MAX_TOKENS = 2048
TEMPERATURE = 0.0

# Trusted domains whitelist - known legitimate sites
TRUSTED_DOMAINS = {
    # Major tech companies
    'google.com', 'youtube.com', 'gmail.com', 'google.co.in',
    'microsoft.com', 'outlook.com', 'office.com', 'live.com', 'bing.com',
    'apple.com', 'icloud.com',
    'amazon.com', 'aws.amazon.com',
    'facebook.com', 'instagram.com', 'whatsapp.com', 'meta.com',
    'twitter.com', 'x.com',
    'linkedin.com',
    'github.com', 'gitlab.com',
    'stackoverflow.com', 'stackexchange.com',
    
    # AI & Tech services
    'openai.com', 'chat.openai.com', 'chatgpt.com',
    'anthropic.com', 'claude.ai',
    'deepmind.com',
    'nvidia.com',
    
    # Cloud & Development
    'cloudflare.com',
    'vercel.com', 'netlify.com',
    'heroku.com',
    'digitalocean.com',
    
    # Financial institutions (major banks)
    'chase.com', 'bankofamerica.com', 'wellsfargo.com', 'citi.com',
    'paypal.com', 'stripe.com', 'square.com',
    
    # E-commerce
    'ebay.com', 'walmart.com', 'target.com',
    'shopify.com',
    
    # Streaming & Entertainment
    'netflix.com', 'spotify.com', 'hulu.com', 'disney.com',
    'twitch.tv', 'reddit.com',
    
    # Education
    'wikipedia.org', 'coursera.org', 'udemy.com', 'khanacademy.org',
    
    # News & Media
    'nytimes.com', 'bbc.com', 'cnn.com', 'reuters.com',
    
    # Government
    'gov', 'gov.uk', 'gov.in', 'irs.gov', 'usa.gov',
    
    # Other trusted services
    'dropbox.com', 'zoom.us', 'slack.com',
    'adobe.com', 'canva.com',
    'wordpress.com', 'medium.com',
}


def handler(event, context):
    """Main Lambda handler"""
    scan_id = event['scanId']
    url = event['url']
    s3_keys = event['s3Keys']
    start_time = datetime.now()
    
    log_info('Analyzer started', {'scanId': scan_id, 'url': url})
    
    try:
        # Retrieve metadata first to check domain
        metadata = json.loads(retrieve_s3_object(s3_keys['metadata']))
        domain = metadata.get('domain', '')
        
        # Check if domain is whitelisted
        if is_trusted_domain(domain):
            log_info('Domain is whitelisted', {'scanId': scan_id, 'domain': domain})
            
            # Return immediate legitimate verdict
            analysis_result = {
                'scanId': scan_id,
                'url': url,
                'verdict': 'Legitimate',
                'riskScore': 5,
                'confidence': 'High',
                'detectedBrand': extract_brand_from_domain(domain),
                'tactics': [],
                'explanation': f'This is a verified legitimate website. {domain} is on our trusted domains list and is recognized as an official, safe website.',
                'processingTimeMs': int((datetime.now() - start_time).total_seconds() * 1000),
                'whitelisted': True
            }
            
            # Invoke Results Handler
            invoke_results_handler(analysis_result)
            
            log_info('Analyzer completed (whitelisted)', {'scanId': scan_id, 'durationMs': analysis_result['processingTimeMs']})
            
            return {'success': True, 'scanId': scan_id}
        
        # Continue with normal analysis for non-whitelisted domains
        # Retrieve artifacts from S3
        html_content = retrieve_s3_object(s3_keys['html'])
        screenshot_bytes = retrieve_s3_object(s3_keys['screenshot'], binary=True)
        
        log_info('Artifacts retrieved', {'scanId': scan_id})
        
        # Analyze with Rekognition
        rekognition_result = analyze_with_rekognition(screenshot_bytes)
        
        # Check domain age and characteristics
        domain_info = check_domain_age(domain)
        
        log_info('Enhanced analysis complete', {
            'scanId': scan_id,
            'rekognition_brands': len(rekognition_result.get('brands', [])),
            'domain_suspicious': domain_info.get('is_suspicious', False)
        })
        
        # Sanitize HTML
        sanitized_html, extracted_content = sanitize_and_extract(html_content)
        
        log_info('HTML sanitized', {'scanId': scan_id})
        
        # Construct prompt with enhanced data
        prompt = construct_prompt(url, metadata, extracted_content, rekognition_result, domain_info)
        
        # Invoke Bedrock
        analysis_result = invoke_bedrock(prompt, screenshot_bytes)
        
        log_info('Bedrock analysis complete', {'scanId': scan_id, 'verdict': analysis_result.get('verdict')})
        
        # Enhance risk score based on Rekognition and domain analysis
        analysis_result = enhance_risk_score(analysis_result, rekognition_result, domain_info, metadata)
        
        # Add metadata
        analysis_result['scanId'] = scan_id
        analysis_result['url'] = url
        analysis_result['processingTimeMs'] = int((datetime.now() - start_time).total_seconds() * 1000)
        analysis_result['whitelisted'] = False
        analysis_result['rekognition_analysis'] = {
            'brands_detected': len(rekognition_result.get('brands', [])),
            'text_extracted': len(rekognition_result.get('extracted_text', []))
        }
        analysis_result['domain_analysis'] = {
            'suspicious_indicators': domain_info.get('suspicious_indicators', 0),
            'is_suspicious': domain_info.get('is_suspicious', False)
        }
        
        # Invoke Results Handler
        invoke_results_handler(analysis_result)
        
        log_info('Analyzer completed', {'scanId': scan_id, 'durationMs': analysis_result['processingTimeMs']})
        
        return {'success': True, 'scanId': scan_id}
        
    except Exception as error:
        log_error('Analyzer failed', {'scanId': scan_id, 'error': str(error)})
        raise


def retrieve_s3_object(key: str, binary: bool = False) -> Any:
    """Retrieve object from S3"""
    response = s3_client.get_object(Bucket=ARTIFACTS_BUCKET, Key=key)
    
    if binary:
        return response['Body'].read()
    else:
        return response['Body'].read().decode('utf-8')


def analyze_with_rekognition(screenshot_bytes: bytes) -> Dict:
    """Analyze screenshot with Amazon Rekognition for logo and text detection"""
    try:
        # Detect labels (logos, brands)
        labels_response = rekognition_client.detect_labels(
            Image={'Bytes': screenshot_bytes},
            MaxLabels=20,
            MinConfidence=70
        )
        
        # Detect text (OCR)
        text_response = rekognition_client.detect_text(
            Image={'Bytes': screenshot_bytes}
        )
        
        # Extract detected brands/logos
        detected_brands = []
        for label in labels_response['Labels']:
            if any(keyword in label['Name'].lower() for keyword in ['logo', 'brand', 'symbol', 'trademark']):
                detected_brands.append({
                    'name': label['Name'],
                    'confidence': label['Confidence']
                })
        
        # Extract all text
        extracted_text = []
        for text_detection in text_response['TextDetections']:
            if text_detection['Type'] == 'LINE':
                extracted_text.append({
                    'text': text_detection['DetectedText'],
                    'confidence': text_detection['Confidence']
                })
        
        log_info('Rekognition analysis complete', {
            'brands_detected': len(detected_brands),
            'text_lines_detected': len(extracted_text)
        })
        
        return {
            'brands': detected_brands,
            'extracted_text': extracted_text,
            'labels': [label['Name'] for label in labels_response['Labels'][:10]]
        }
    
    except Exception as e:
        log_error('Rekognition analysis failed', {'error': str(e)})
        return {
            'brands': [],
            'extracted_text': [],
            'labels': [],
            'error': str(e)
        }


def check_domain_age(domain: str) -> Dict:
    """Check domain age using WHOIS (simplified version)"""
    try:
        import socket
        from urllib.parse import urlparse
        
        # Extract domain from URL
        if domain.startswith('http'):
            domain = urlparse(domain).netloc
        
        # Remove www. prefix
        domain = domain.replace('www.', '')
        
        # For now, we'll use a simplified check
        # In production, you'd use python-whois library or external API
        
        # Check if domain resolves (basic check)
        try:
            socket.gethostbyname(domain)
            domain_exists = True
        except:
            domain_exists = False
        
        # Heuristic: Check if domain looks suspicious
        suspicious_indicators = 0
        
        # Check for suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            suspicious_indicators += 1
        
        # Check for excessive hyphens
        if domain.count('-') > 2:
            suspicious_indicators += 1
        
        # Check for numbers in domain
        if any(char.isdigit() for char in domain):
            suspicious_indicators += 1
        
        # Check domain length
        if len(domain) > 30:
            suspicious_indicators += 1
        
        return {
            'domain': domain,
            'exists': domain_exists,
            'suspicious_indicators': suspicious_indicators,
            'is_suspicious': suspicious_indicators >= 2,
            'checks': {
                'suspicious_tld': any(domain.endswith(tld) for tld in suspicious_tlds),
                'excessive_hyphens': domain.count('-') > 2,
                'contains_numbers': any(char.isdigit() for char in domain),
                'long_domain': len(domain) > 30
            }
        }
    
    except Exception as e:
        log_error('Domain age check failed', {'error': str(e)})
        return {
            'domain': domain,
            'exists': False,
            'suspicious_indicators': 0,
            'is_suspicious': False,
            'error': str(e)
        }


def is_trusted_domain(domain: str) -> bool:
    """Check if domain is in trusted whitelist"""
    if not domain:
        return False
    
    # Normalize domain (remove www., convert to lowercase)
    domain = domain.lower().replace('www.', '')
    
    # Check exact match
    if domain in TRUSTED_DOMAINS:
        return True
    
    # Check if it's a subdomain of a trusted domain
    for trusted in TRUSTED_DOMAINS:
        if domain.endswith('.' + trusted):
            return True
    
    return False


def extract_brand_from_domain(domain: str) -> Optional[str]:
    """Extract brand name from domain"""
    if not domain:
        return None
    
    # Remove www. and TLD
    domain = domain.lower().replace('www.', '')
    
    # Map common domains to brand names
    brand_map = {
        'google': 'Google',
        'microsoft': 'Microsoft',
        'apple': 'Apple',
        'amazon': 'Amazon',
        'facebook': 'Facebook',
        'meta': 'Meta',
        'openai': 'OpenAI',
        'chatgpt': 'ChatGPT',
        'anthropic': 'Anthropic',
        'claude': 'Claude',
        'github': 'GitHub',
        'linkedin': 'LinkedIn',
        'twitter': 'Twitter',
        'netflix': 'Netflix',
        'paypal': 'PayPal',
        'stripe': 'Stripe',
    }
    
    for key, brand in brand_map.items():
        if key in domain:
            return brand
    
    # Default: capitalize first part of domain
    parts = domain.split('.')
    if parts:
        return parts[0].capitalize()
    
    return None


def sanitize_and_extract(html: str) -> tuple:
    """Sanitize HTML and extract meaningful content"""
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove dangerous elements
    for tag in soup(['script', 'style', 'iframe', 'noscript']):
        tag.decompose()
    
    # Remove event handlers
    for tag in soup.find_all(True):
        for attr in list(tag.attrs.keys()):
            if attr.startswith('on') or attr in ['href', 'src'] and tag.attrs[attr].startswith('javascript:'):
                del tag.attrs[attr]
    
    sanitized_html = str(soup)
    
    # Extract meaningful content
    extracted = {
        'forms': extract_forms(soup),
        'links': extract_links(soup),
        'text': extract_text(soup),
        'urgency_keywords': find_urgency_keywords(soup),
        'brand_mentions': find_brand_mentions(soup)
    }
    
    return sanitized_html, extracted


def extract_forms(soup: BeautifulSoup) -> list:
    """Extract form information"""
    forms = []
    for form in soup.find_all('form'):
        form_data = {
            'action': form.get('action', ''),
            'method': form.get('method', 'get'),
            'inputs': []
        }
        for input_tag in form.find_all(['input', 'textarea']):
            form_data['inputs'].append({
                'type': input_tag.get('type', 'text'),
                'name': input_tag.get('name', ''),
                'placeholder': input_tag.get('placeholder', '')
            })
        forms.append(form_data)
    return forms


def extract_links(soup: BeautifulSoup) -> list:
    """Extract suspicious links"""
    links = []
    for link in soup.find_all('a', href=True)[:20]:  # Limit to first 20
        links.append({
            'href': link['href'],
            'text': link.get_text(strip=True)[:100]
        })
    return links


def extract_text(soup: BeautifulSoup) -> str:
    """Extract visible text content"""
    text = soup.get_text(separator=' ', strip=True)
    # Limit to 10000 characters
    return text[:10000]


def find_urgency_keywords(soup: BeautifulSoup) -> list:
    """Find urgency language"""
    urgency_patterns = [
        'urgent', 'verify', 'suspended', 'expire', 'confirm', 
        'immediately', 'act now', 'limited time', 'account locked',
        'unusual activity', 'security alert'
    ]
    
    text = soup.get_text().lower()
    found = []
    
    for pattern in urgency_patterns:
        if pattern in text:
            found.append(pattern)
    
    return found


def find_brand_mentions(soup: BeautifulSoup) -> list:
    """Find brand mentions"""
    brands = [
        'paypal', 'amazon', 'microsoft', 'apple', 'google',
        'facebook', 'netflix', 'bank', 'chase', 'wells fargo'
    ]
    
    text = soup.get_text().lower()
    found = []
    
    for brand in brands:
        if brand in text:
            found.append(brand)
    
    return found


def construct_prompt(url: str, metadata: Dict, extracted: Dict, rekognition_result: Dict = None, domain_info: Dict = None) -> str:
    """Construct structured prompt for Bedrock with enhanced data"""
    domain = metadata.get('domain', '')
    title = metadata.get('title', '')
    
    # Add Rekognition insights
    rekognition_insights = ""
    if rekognition_result:
        brands = rekognition_result.get('brands', [])
        if brands:
            rekognition_insights = f"\n<rekognition_analysis>\nDetected visual brands/logos: {', '.join([b['name'] for b in brands[:5]])}\n</rekognition_analysis>"
    
    # Add domain analysis insights
    domain_insights = ""
    if domain_info and domain_info.get('is_suspicious'):
        indicators = domain_info.get('checks', {})
        suspicious_factors = [k for k, v in indicators.items() if v]
        domain_insights = f"\n<domain_analysis>\nSuspicious domain characteristics: {', '.join(suspicious_factors)}\nSuspicion score: {domain_info.get('suspicious_indicators', 0)}/4\n</domain_analysis>"
    
    prompt = f"""<system>
You are a cybersecurity expert analyzing websites for phishing indicators. Your task is to determine if a website is legitimate, suspicious, or a phishing attempt.

Analyze the provided website content and respond ONLY with valid JSON in this exact format:
{{
  "verdict": "Phishing" | "Suspicious" | "Legitimate",
  "riskScore": <number 0-100>,
  "confidence": "High" | "Medium" | "Low",
  "detectedBrand": "<brand name or null>",
  "tactics": ["<tactic1>", "<tactic2>"],
  "explanation": "<clear explanation>"
}}

Phishing indicators to consider:
- Login forms on non-official domains
- Urgency language (verify now, account suspended, expire soon)
- Brand impersonation (logos, names, styling)
- Suspicious URLs (typosquatting, unusual TLDs)
- Poor grammar or spelling
- Suspicious domain characteristics (new domains, unusual TLDs, excessive hyphens)
- Visual brand mismatches (logo doesn't match claimed brand)
- Requests for sensitive information
- Mismatched sender/domain information
</system>

<website_content>
<url>{url}</url>
<domain>{domain}</domain>
<page_title>{title}</page_title>
<extracted_text>
{extracted['text'][:5000]}
</extracted_text>
<forms>
{json.dumps(extracted['forms'], indent=2)}
</forms>
<links>
{json.dumps(extracted['links'][:10], indent=2)}
</links>
<urgency_keywords>
{', '.join(extracted['urgency_keywords'])}
</urgency_keywords>
<brand_mentions>
{', '.join(extracted['brand_mentions'])}
</brand_mentions>
{rekognition_insights}
{domain_insights}
</website_content>

Analyze this website and respond with JSON only."""
    
    return prompt


def invoke_bedrock(prompt: str, screenshot_bytes: bytes) -> Dict:
    """Invoke Bedrock Amazon Nova Premier"""
    # Encode screenshot
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    
    # Construct messages for Nova
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": screenshot_base64
                        }
                    }
                },
                {
                    "text": prompt
                }
            ]
        }
    ]
    
    # Invoke model with Nova format
    request_body = {
        "messages": messages,
        "inferenceConfig": {
            "max_new_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": 0.9
        }
    }
    
    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(request_body)
    )
    
    response_body = json.loads(response['body'].read())
    
    # Extract text from Nova response
    content = response_body['output']['message']['content'][0]['text']
    
    # Parse JSON from response
    result = parse_llm_response(content)
    
    return result


def parse_llm_response(content: str) -> Dict:
    """Parse and validate LLM response"""
    # Try multiple extraction strategies
    
    # Strategy 1: Extract JSON from markdown code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1)
    
    # Strategy 2: Extract JSON from generic code blocks
    if not json_match:
        json_match = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
    
    # Strategy 3: Find raw JSON object in the text
    if not json_match:
        json_match = re.search(r'(\{[^{}]*"verdict"[^{}]*\})', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
    
    # Strategy 4: Find any JSON object with nested arrays/objects
    if not json_match:
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
    
    # Try to parse JSON
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Try stripping leading/trailing non-JSON text
        content = content.strip()
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            try:
                result = json.loads(content[start:end+1])
            except json.JSONDecodeError:
                return {
                    'verdict': 'Suspicious',
                    'riskScore': 50,
                    'confidence': 'Low',
                    'detectedBrand': None,
                    'tactics': [],
                    'explanation': 'Analysis failed - manual review recommended'
                }
        else:
            return {
                'verdict': 'Suspicious',
                'riskScore': 50,
                'confidence': 'Low',
                'detectedBrand': None,
                'tactics': [],
                'explanation': 'Analysis failed - manual review recommended'
            }
    
    # Validate and normalize
    result['verdict'] = result.get('verdict', 'Suspicious')
    if result['verdict'] not in ['Phishing', 'Suspicious', 'Legitimate']:
        result['verdict'] = 'Suspicious'
    
    result['riskScore'] = max(0, min(100, int(result.get('riskScore', 50))))
    
    result['confidence'] = result.get('confidence', 'Low')
    if result['confidence'] not in ['High', 'Medium', 'Low']:
        result['confidence'] = 'Low'
    
    result['detectedBrand'] = result.get('detectedBrand')
    result['tactics'] = result.get('tactics', [])
    result['explanation'] = result.get('explanation', 'No explanation provided')
    
    return result


def enhance_risk_score(analysis_result: Dict, rekognition_result: Dict, domain_info: Dict, metadata: Dict) -> Dict:
    """Enhance risk score based on Rekognition and domain analysis"""
    risk_score = analysis_result.get('riskScore', 50)
    tactics = analysis_result.get('tactics', [])
    explanation = analysis_result.get('explanation', '')
    
    # Check for brand mismatch using Rekognition
    detected_brand = analysis_result.get('detectedBrand')
    if detected_brand and rekognition_result.get('brands'):
        rekognition_brands = [b['name'].lower() for b in rekognition_result['brands']]
        if detected_brand.lower() not in ' '.join(rekognition_brands):
            risk_score += 10
            tactics.append('Visual brand mismatch detected')
            explanation += ' Rekognition analysis shows visual elements that do not match the claimed brand.'
    
    # Adjust for suspicious domain characteristics
    if domain_info.get('is_suspicious'):
        suspicious_count = domain_info.get('suspicious_indicators', 0)
        risk_score += (suspicious_count * 5)  # Add 5 points per suspicious indicator
        
        checks = domain_info.get('checks', {})
        if checks.get('suspicious_tld'):
            tactics.append('Suspicious top-level domain')
        if checks.get('excessive_hyphens'):
            tactics.append('Excessive hyphens in domain')
        if checks.get('contains_numbers'):
            tactics.append('Numbers in domain name')
        if checks.get('long_domain'):
            tactics.append('Unusually long domain name')
        
        explanation += f' Domain analysis reveals {suspicious_count} suspicious characteristics.'
    
    # Cap risk score at 100
    risk_score = min(100, risk_score)
    
    # Update verdict if risk score changed significantly
    if risk_score >= 70 and analysis_result.get('verdict') != 'Phishing':
        analysis_result['verdict'] = 'Phishing'
    elif risk_score >= 40 and analysis_result.get('verdict') == 'Legitimate':
        analysis_result['verdict'] = 'Suspicious'
    
    analysis_result['riskScore'] = risk_score
    analysis_result['tactics'] = list(set(tactics))  # Remove duplicates
    analysis_result['explanation'] = explanation
    
    return analysis_result


def invoke_results_handler(analysis_result: Dict):
    """Invoke Results Handler Lambda"""
    lambda_client.invoke(
        FunctionName=RESULTS_HANDLER_FUNCTION,
        InvocationType='Event',
        Payload=json.dumps(analysis_result)
    )
    
    log_info('Results handler invoked', {'scanId': analysis_result['scanId']})


def log_info(message: str, metadata: Dict = None):
    """Structured info logging"""
    if LOG_LEVEL in ['INFO', 'DEBUG']:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': 'INFO',
            'component': 'Analyzer',
            'message': message
        }
        if metadata:
            log_entry.update(metadata)
        print(json.dumps(log_entry))


def log_error(message: str, metadata: Dict = None):
    """Structured error logging"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'level': 'ERROR',
        'component': 'Analyzer',
        'message': message
    }
    if metadata:
        log_entry.update(metadata)
    print(json.dumps(log_entry))
