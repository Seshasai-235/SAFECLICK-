// SafeClick API Handler Lambda
// Entry point for URL submissions

const { LambdaClient, InvokeCommand } = require('@aws-sdk/client-lambda');
const { v4: uuidv4 } = require('uuid');

const lambdaClient = new LambdaClient({});

// Environment variables
const CRAWLER_FUNCTION_NAME = process.env.CRAWLER_FUNCTION_NAME || 'safeclick-crawler';
const LOG_LEVEL = process.env.LOG_LEVEL || 'INFO';

/**
 * Main Lambda handler
 */
exports.handler = async (event) => {
  const startTime = Date.now();
  const scanId = uuidv4();
  
  try {
    // Parse request body
    const body = JSON.parse(event.body || '{}');
    const url = body.url;
    
    // Log request
    logInfo('Request received', { scanId, url, ip: event.requestContext?.identity?.sourceIp });
    
    // Validate URL
    const validation = validateUrl(url);
    if (!validation.valid) {
      return createResponse(400, {
        error: 'Invalid URL format',
        message: validation.message,
        scanId
      });
    }
    
    // Invoke Web Crawler Lambda
    await invokeCrawler(scanId, url);
    
    // Return response
    const response = {
      scanId,
      status: 'processing',
      message: 'URL submitted for analysis',
      url
    };
    
    logInfo('Request processed', { scanId, durationMs: Date.now() - startTime });
    
    return createResponse(200, response);
    
  } catch (error) {
    logError('Request failed', { scanId, error: error.message, stack: error.stack });
    
    return createResponse(500, {
      error: 'Internal server error',
      message: 'An error occurred processing your request',
      scanId
    });
  }
};

/**
 * Validate URL format
 */
function validateUrl(url) {
  if (!url) {
    return { valid: false, message: 'URL is required' };
  }
  
  if (typeof url !== 'string') {
    return { valid: false, message: 'URL must be a string' };
  }
  
  // URL pattern: http(s)://domain.tld/path
  const urlPattern = /^https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(\/.*)?$/;
  
  if (!urlPattern.test(url)) {
    return { valid: false, message: 'URL must start with http:// or https:// and include a valid domain' };
  }
  
  return { valid: true };
}

/**
 * Invoke Web Crawler Lambda
 */
async function invokeCrawler(scanId, url) {
  const payload = {
    scanId,
    url
  };
  
  const command = new InvokeCommand({
    FunctionName: CRAWLER_FUNCTION_NAME,
    InvocationType: 'Event', // Async invocation
    Payload: JSON.stringify(payload)
  });
  
  await lambdaClient.send(command);
  
  logInfo('Crawler invoked', { scanId, url });
}

/**
 * Create HTTP response with CORS headers
 */
function createResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS, GET',
      'Access-Control-Allow-Headers': 'Content-Type'
    },
    body: JSON.stringify(body)
  };
}

/**
 * Structured logging functions
 */
function logInfo(message, metadata = {}) {
  if (LOG_LEVEL === 'INFO' || LOG_LEVEL === 'DEBUG') {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'INFO',
      component: 'ApiHandler',
      message,
      ...metadata
    }));
  }
}

function logError(message, metadata = {}) {
  console.error(JSON.stringify({
    timestamp: new Date().toISOString(),
    level: 'ERROR',
    component: 'ApiHandler',
    message,
    ...metadata
  }));
}

// Export for testing
module.exports.validateUrl = validateUrl;
module.exports.createResponse = createResponse;
