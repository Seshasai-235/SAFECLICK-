# SafeClick - AI-Powered Phishing Detection

Real-time phishing website detection using Multi-Modal AI (LLM + Computer Vision + Domain Intelligence) on AWS Serverless Architecture.

**Live Demo:** https://dm61nlne5crlk.cloudfront.net

## What It Does

Submit any URL → SafeClick visits the website, captures a screenshot, analyzes it with AI, and tells you if it's **Phishing**, **Suspicious**, or **Legitimate** — with a risk score, confidence level, and natural-language explanation.

## Architecture

```
User → CloudFront (UI) → API Gateway → API Handler Lambda
                                              ↓
                                     Web Crawler Lambda (Headless Chrome)
                                        ↓           ↓
                                       S3        Analyzer Lambda
                                   (artifacts)    ↓        ↓        ↓
                                           Bedrock    Rekognition   Domain Analysis
                                           (Nova Pro)  (Logo+OCR)   (Heuristics)
                                                   ↓
                                          Results Handler Lambda → DynamoDB
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, Tailwind CSS, Framer Motion |
| API | Amazon API Gateway (REST) |
| Compute | AWS Lambda (Node.js 20.x + Python 3.10) |
| AI/ML | Amazon Bedrock (Nova Pro), Amazon Rekognition |
| Storage | Amazon S3 (encrypted), Amazon DynamoDB |
| CDN | Amazon CloudFront |
| IaC | AWS SAM |

## Prerequisites

- AWS Account with Bedrock access
- AWS CLI configured (`aws configure`)
- AWS SAM CLI installed
- Node.js 20.x
- Python 3.10+

## Quick Start

### 1. Install Dependencies

```bash
cd src/api-handler && npm install && cd ../..
cd src/web-crawler && npm install && cd ../..
cd src/analyzer && pip install -r requirements.txt -t . && cd ../..
cd src/results-handler && pip install -r requirements.txt -t . && cd ../..
```

### 2. Build

```bash
sam build
```

### 3. Deploy Backend

```bash
sam deploy --stack-name safeclick-dev --region us-east-1 --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset
```

Note the **API Endpoint** from the output (e.g., `https://xyz.execute-api.us-east-1.amazonaws.com/dev/analyze`)

### 4. Deploy Frontend

Update the API endpoint in the UI:

```bash
# Edit safeclick-ui/.env.local
NEXT_PUBLIC_API_ENDPOINT=https://YOUR_API_ENDPOINT/dev
```

Build and deploy the frontend:

```bash
cd safeclick-ui
npm install
npm run build

# Create S3 bucket for frontend
aws s3 mb s3://safeclick-frontend-YOUR_ACCOUNT_ID

# Upload
aws s3 sync out/ s3://safeclick-frontend-YOUR_ACCOUNT_ID --delete

# Enable website hosting
aws s3 website s3://safeclick-frontend-YOUR_ACCOUNT_ID --index-document index.html --error-document 404.html
```

Then create a CloudFront distribution pointing to the S3 website endpoint.

### 5. Run Locally (Frontend Only)

```bash
cd safeclick-ui
npm install
npm run dev
```

Open http://localhost:3000

## Test URLs

| URL | Expected Verdict |
|-----|-----------------|
| `https://www.google.com` | Legitimate (Risk 5) |
| `https://testsafebrowsing.appspot.com/s/phishing.html` | Phishing (Risk 90) |
| `https://httpbin.org/forms/post` | Suspicious (Risk 50-60) |

## Project Structure

```
SafeClick/
├── src/
│   ├── api-handler/          # URL validation, scan ID generation (Node.js)
│   ├── web-crawler/          # Headless Chrome, screenshot capture (Node.js)
│   ├── analyzer/             # AI analysis pipeline (Python)
│   └── results-handler/      # DynamoDB storage & queries (Python)
├── safeclick-ui/             # Next.js frontend
├── evaluation/               # Test dataset & evaluation scripts
├── template.yaml             # AWS SAM infrastructure template
├── samconfig.toml            # SAM deployment config
└── deploy.sh                 # Deployment script
```

## How It Works

1. **URL Submission** → API validates format, generates scan ID
2. **Web Crawling** → Headless Chrome visits the URL, captures HTML + screenshot
3. **AI Analysis** →
   - Checks trusted domain whitelist (instant result for Google, Amazon, etc.)
   - Runs Amazon Rekognition for logo detection and OCR
   - Analyzes domain patterns (suspicious TLDs, hyphens, length)
   - Sanitizes HTML to prevent prompt injection
   - Sends text + screenshot to Amazon Bedrock Nova Pro (multimodal LLM)
   - Fuses all signals into a final risk score
4. **Results** → Stores in DynamoDB, returns verdict to user

## Security Features

- 4-layer prompt injection defense (HTML sanitization, XML delimiters, output validation, fail-safe defaults)
- AES-256 encryption at rest (S3, DynamoDB)
- TLS 1.2+ encryption in transit
- Least-privilege IAM roles per Lambda
- HTTPS-only S3 bucket policy

## Cost

~$0.02 per URL scan (non-whitelisted). Whitelisted domains are nearly free (<$0.001).
Zero idle costs — fully serverless.

## Cleanup

To delete all resources:

```bash
sam delete --stack-name safeclick-dev --no-prompts
aws s3 rb s3://safeclick-frontend-YOUR_ACCOUNT_ID --force
# Delete CloudFront distribution via AWS Console
```


