"""
SafeClick Results Handler Lambda
Stores analysis results in DynamoDB
"""

import json
import os
from typing import Dict, Any
from datetime import datetime

import boto3

# AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
RESULTS_TABLE_NAME = os.environ.get('RESULTS_TABLE')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Get table
table = dynamodb.Table(RESULTS_TABLE_NAME)


def handler(event, context):
    """Main Lambda handler"""
    # Check if this is a query request
    if event.get('httpMethod') == 'GET' and event.get('queryStringParameters'):
        return handle_query(event)
    
    scan_id = event.get('scanId')
    
    log_info('Results handler started', {'scanId': scan_id})
    
    try:
        # Validate input
        validation_result = validate_input(event)
        if not validation_result['valid']:
            log_error('Validation failed', {'scanId': scan_id, 'errors': validation_result['errors']})
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Validation failed',
                    'message': validation_result['errors']
                })
            }
        
        # Prepare DynamoDB item
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        item = {
            'url': event['url'],
            'timestamp': timestamp,
            'scanId': scan_id,
            'verdict': event['verdict'],
            'riskScore': event['riskScore'],
            'confidence': event['confidence'],
            'detectedBrand': event.get('detectedBrand'),
            'tactics': event.get('tactics', []),
            'explanation': event['explanation'],
            'processingTimeMs': event.get('processingTimeMs', 0),
            'whitelisted': event.get('whitelisted', False)
        }
        
        # Add enhancement fields if present
        if event.get('rekognition_analysis'):
            item['rekognition_analysis'] = event['rekognition_analysis']
        
        if event.get('domain_analysis'):
            item['domain_analysis'] = event['domain_analysis']
        
        # Write to DynamoDB
        table.put_item(Item=item)
        
        log_info('Results stored', {'scanId': scan_id, 'verdict': event['verdict']})
        
        # Format response
        response = {
            'scanId': scan_id,
            'url': event['url'],
            'verdict': event['verdict'],
            'riskScore': event['riskScore'],
            'confidence': event['confidence'],
            'detectedBrand': event.get('detectedBrand'),
            'tactics': event.get('tactics', []),
            'explanation': event['explanation'],
            'timestamp': timestamp,
            'processingTimeMs': event.get('processingTimeMs', 0),
            'whitelisted': event.get('whitelisted', False)
        }
        
        # Add enhancement fields to response if present
        if event.get('rekognition_analysis'):
            response['rekognition_analysis'] = event['rekognition_analysis']
        
        if event.get('domain_analysis'):
            response['domain_analysis'] = event['domain_analysis']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
        
    except Exception as error:
        log_error('Results handler failed', {'scanId': scan_id, 'error': str(error)})
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': 'Failed to store results',
                'scanId': scan_id
            })
        }


def validate_input(event: Dict) -> Dict[str, Any]:
    """Validate input schema"""
    errors = []
    
    required_fields = ['scanId', 'url', 'verdict', 'riskScore', 'confidence', 'explanation']
    
    for field in required_fields:
        if field not in event:
            errors.append(f'Missing required field: {field}')
    
    # Validate verdict
    if 'verdict' in event and event['verdict'] not in ['Phishing', 'Suspicious', 'Legitimate']:
        errors.append(f'Invalid verdict: {event["verdict"]}')
    
    # Validate riskScore
    if 'riskScore' in event:
        try:
            score = int(event['riskScore'])
            if score < 0 or score > 100:
                errors.append(f'Risk score must be between 0 and 100: {score}')
        except (ValueError, TypeError):
            errors.append(f'Risk score must be a number: {event["riskScore"]}')
    
    # Validate confidence
    if 'confidence' in event and event['confidence'] not in ['High', 'Medium', 'Low']:
        errors.append(f'Invalid confidence: {event["confidence"]}')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def handle_query(event: Dict) -> Dict:
    """Handle query requests for scan history or specific scan"""
    params = event.get('queryStringParameters', {})
    scan_id = params.get('scanId')
    url = params.get('url')
    
    # Query by scanId (for real-time polling)
    if scan_id:
        try:
            # Query using scanId-index GSI
            response = table.query(
                IndexName='scanId-index',
                KeyConditionExpression='scanId = :scanId',
                ExpressionAttributeValues={':scanId': scan_id},
                Limit=1
            )
            
            items = response.get('Items', [])
            
            if items:
                result = items[0]
                log_info('Scan found', {'scanId': scan_id})
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'status': 'completed',
                        'result': result
                    }, default=str)
                }
            else:
                # Not found yet - still processing
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'status': 'processing',
                        'scanId': scan_id
                    })
                }
        except Exception as error:
            log_error('ScanId query failed', {'scanId': scan_id, 'error': str(error)})
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Query failed',
                    'message': str(error)
                })
            }
    
    # Query by URL (for history)
    if not url:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Missing required parameter: url or scanId'
            })
        }
    
    try:
        # Query DynamoDB by URL
        response = table.query(
            KeyConditionExpression='#url = :url',
            ExpressionAttributeNames={'#url': 'url'},
            ExpressionAttributeValues={':url': url},
            ScanIndexForward=False,  # Sort by timestamp descending
            Limit=10  # Return last 10 scans
        )
        
        items = response.get('Items', [])
        
        log_info('Query completed', {'url': url, 'count': len(items)})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'url': url,
                'count': len(items),
                'results': items
            }, default=str)
        }
        
    except Exception as error:
        log_error('Query failed', {'url': url, 'error': str(error)})
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Query failed',
                'message': str(error)
            })
        }


def log_info(message: str, metadata: Dict = None):
    """Structured info logging"""
    if LOG_LEVEL in ['INFO', 'DEBUG']:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': 'INFO',
            'component': 'ResultsHandler',
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
        'component': 'ResultsHandler',
        'message': message
    }
    if metadata:
        log_entry.update(metadata)
    print(json.dumps(log_entry))
