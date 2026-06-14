// SafeClick Web Crawler Lambda
// Captures website content using headless Chrome

const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { LambdaClient, InvokeCommand } = require('@aws-sdk/client-lambda');
const puppeteer = require('puppeteer-core');
const chromium = require('@sparticuz/chromium');

const s3Client = new S3Client({});
const lambdaClient = new LambdaClient({});

// Environment variables
const ARTIFACTS_BUCKET = process.env.ARTIFACTS_BUCKET;
const ANALYZER_FUNCTION_NAME = process.env.ANALYZER_FUNCTION_NAME || 'safeclick-analyzer';
const LOG_LEVEL = process.env.LOG_LEVEL || 'INFO';

/**
 * Main Lambda handler
 */
exports.handler = async (event) => {
  const { scanId, url } = event;
  const startTime = Date.now();
  
  logInfo('Crawler started', { scanId, url });
  
  let browser = null;
  
  try {
    // Launch browser
    browser = await puppeteer.launch({
      args: chromium.args,
      defaultViewport: chromium.defaultViewport,
      executablePath: await chromium.executablePath(),
      headless: chromium.headless
    });
    
    const page = await browser.newPage();
    
    // Set viewport
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Navigate to URL with timeout
    const response = await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    const statusCode = response.status();
    const finalUrl = page.url();
    
    logInfo('Page loaded', { scanId, url, statusCode, finalUrl });
    
    // Capture HTML
    const html = await page.content();
    
    // Capture screenshot
    const screenshot = await page.screenshot({
      fullPage: true,
      type: 'png'
    });
    
    // Extract metadata
    const title = await page.title();
    const domain = new URL(url).hostname;
    
    const metadata = {
      scanId,
      url,
      finalUrl,
      domain,
      title,
      statusCode,
      timestamp: new Date().toISOString(),
      captureTimeMs: Date.now() - startTime
    };
    
    await browser.close();
    browser = null;
    
    // Store artifacts in S3
    const s3Keys = await storeArtifacts(scanId, html, screenshot, metadata);
    
    logInfo('Artifacts stored', { scanId, s3Keys });
    
    // Invoke Analyzer Lambda
    await invokeAnalyzer(scanId, url, s3Keys);
    
    logInfo('Crawler completed', { scanId, durationMs: Date.now() - startTime });
    
    return { success: true, scanId, s3Keys };
    
  } catch (error) {
    logError('Crawler failed', { scanId, url, error: error.message, stack: error.stack });
    
    // Store error metadata
    const errorMetadata = {
      scanId,
      url,
      error: error.message,
      timestamp: new Date().toISOString()
    };
    
    await storeErrorMetadata(scanId, errorMetadata);
    
    throw error;
    
  } finally {
    if (browser) {
      await browser.close();
    }
  }
};

/**
 * Store artifacts in S3
 */
async function storeArtifacts(scanId, html, screenshot, metadata) {
  const prefix = `scans/${scanId}`;
  
  const s3Keys = {
    html: `${prefix}/page.html`,
    screenshot: `${prefix}/screenshot.png`,
    metadata: `${prefix}/metadata.json`
  };
  
  // Upload HTML
  await s3Client.send(new PutObjectCommand({
    Bucket: ARTIFACTS_BUCKET,
    Key: s3Keys.html,
    Body: html,
    ContentType: 'text/html',
    ServerSideEncryption: 'AES256'
  }));
  
  // Upload screenshot
  await s3Client.send(new PutObjectCommand({
    Bucket: ARTIFACTS_BUCKET,
    Key: s3Keys.screenshot,
    Body: screenshot,
    ContentType: 'image/png',
    ServerSideEncryption: 'AES256'
  }));
  
  // Upload metadata
  await s3Client.send(new PutObjectCommand({
    Bucket: ARTIFACTS_BUCKET,
    Key: s3Keys.metadata,
    Body: JSON.stringify(metadata, null, 2),
    ContentType: 'application/json',
    ServerSideEncryption: 'AES256'
  }));
  
  return s3Keys;
}

/**
 * Store error metadata in S3
 */
async function storeErrorMetadata(scanId, errorMetadata) {
  try {
    await s3Client.send(new PutObjectCommand({
      Bucket: ARTIFACTS_BUCKET,
      Key: `scans/${scanId}/error.json`,
      Body: JSON.stringify(errorMetadata, null, 2),
      ContentType: 'application/json',
      ServerSideEncryption: 'AES256'
    }));
  } catch (err) {
    logError('Failed to store error metadata', { scanId, error: err.message });
  }
}

/**
 * Invoke Analyzer Lambda
 */
async function invokeAnalyzer(scanId, url, s3Keys) {
  const payload = {
    scanId,
    url,
    s3Keys
  };
  
  const command = new InvokeCommand({
    FunctionName: ANALYZER_FUNCTION_NAME,
    InvocationType: 'Event',
    Payload: JSON.stringify(payload)
  });
  
  await lambdaClient.send(command);
  
  logInfo('Analyzer invoked', { scanId });
}

/**
 * Structured logging functions
 */
function logInfo(message, metadata = {}) {
  if (LOG_LEVEL === 'INFO' || LOG_LEVEL === 'DEBUG') {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'INFO',
      component: 'WebCrawler',
      message,
      ...metadata
    }));
  }
}

function logError(message, metadata = {}) {
  console.error(JSON.stringify({
    timestamp: new Date().toISOString(),
    level: 'ERROR',
    component: 'WebCrawler',
    message,
    ...metadata
  }));
}
