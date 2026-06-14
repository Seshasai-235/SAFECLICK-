# SafeClick UI

Modern, animated web interface for SafeClick phishing detection system.

## Features

- ✨ Beautiful animations with Framer Motion
- 🎨 Glassmorphism design with gradient backgrounds
- 📱 Fully responsive (mobile, tablet, desktop)
- ⚡ Real-time scanning with progress indicators
- 🔄 Automatic polling for results
- 🎯 Clear verdict display with risk scores
- 🌐 Integrated with AWS API Gateway

## Quick Start

### 1. Install Dependencies

```bash
npm install
# or
pnpm install
# or
yarn install
```

### 2. Configure API Endpoint

The API endpoint is already configured in `.env.local`:
```
NEXT_PUBLIC_API_ENDPOINT=https://2creda2yj3.execute-api.us-east-1.amazonaws.com/dev
```

### 3. Run Development Server

```bash
npm run dev
# or
pnpm dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production

```bash
npm run build
npm start
```

## Deployment

### Deploy to Vercel (Recommended)

1. Push to GitHub
2. Import project in Vercel
3. Add environment variable: `NEXT_PUBLIC_API_ENDPOINT`
4. Deploy!

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### Deploy to Netlify

1. Push to GitHub
2. Import project in Netlify
3. Add environment variable: `NEXT_PUBLIC_API_ENDPOINT`
4. Deploy!

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Backend**: AWS API Gateway + Lambda + Bedrock

## Project Structure

```
safeclick-ui/
├── app/
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Main page with all components
├── lib/
│   └── api.ts            # API integration
├── .env.local            # Environment variables
├── package.json          # Dependencies
├── tailwind.config.js    # Tailwind configuration
└── tsconfig.json         # TypeScript configuration
```

## How It Works

1. **User enters URL** → Input validation
2. **Click "Analyze URL"** → POST to `/analyze`
3. **Show loading animation** → Progress bar + status messages
4. **Poll for results** → GET `/results?url=...` every 3 seconds
5. **Display results** → Verdict badge, risk score, AI explanation
6. **Scan another URL** → Reset and repeat

## API Integration

### POST /analyze
```json
Request: { "url": "https://example.com" }
Response: { "scanId": "...", "status": "processing", "url": "..." }
```

### GET /results?url={url}
```json
Response: {
  "url": "...",
  "count": 1,
  "results": [{
    "verdict": "Legitimate",
    "riskScore": 5,
    "confidence": "High",
    "explanation": "...",
    "detectedBrand": "Google",
    "tactics": [],
    "timestamp": "...",
    "processingTimeMs": 5000,
    "scanId": "..."
  }]
}
```

## Customization

### Change Colors

Edit `tailwind.config.js`:
```javascript
colors: {
  primary: '#3B82F6',    // Blue
  success: '#10B981',    // Green
  warning: '#F59E0B',    // Yellow
  danger: '#EF4444',     // Red
}
```

### Adjust Polling

Edit `lib/api.ts`:
```typescript
// Poll every 5 seconds instead of 3
await new Promise(resolve => setTimeout(resolve, 5000))

// Try 15 times instead of 10
export async function pollResults(url: string, maxAttempts = 15)
```

### Modify Animations

Edit `app/page.tsx` - all animations use Framer Motion:
```typescript
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5 }}
>
```

## Troubleshooting

### CORS Errors
- API Gateway already has CORS enabled
- Check browser console for details
- Try in incognito mode

### Timeout Errors
- Increase `maxAttempts` in `lib/api.ts`
- Check AWS Lambda logs
- Verify API endpoint is correct

### Build Errors
- Delete `.next` folder
- Delete `node_modules`
- Run `npm install` again
- Run `npm run build`

## License

MIT

## Support

For issues or questions, check the main SafeClick documentation.
