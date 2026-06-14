'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Shield, Sparkles, AlertTriangle, CheckCircle, XCircle, History } from 'lucide-react'
import { scanURL, pollResults, type ScanResult } from '@/lib/api'
import Link from 'next/link'

export default function Home() {
  const [url, setUrl] = useState('')
  const [isScanning, setIsScanning] = useState(false)
  const [result, setResult] = useState<ScanResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  const handleScan = async () => {
    if (!url) return

    setIsScanning(true)
    setError(null)
    setResult(null)
    setProgress(0)

    try {
      console.log('Starting scan for:', url)
      
      // Start scan
      const scanResponse = await scanURL(url)
      console.log('Scan initiated:', scanResponse)
      setProgress(20)

      // Simulate progress during polling
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90))
      }, 2000)

      // Poll for results using scanId
      console.log('Polling for results with scanId:', scanResponse.scanId)
      const scanResult = await pollResults(scanResponse.scanId)
      clearInterval(progressInterval)
      
      console.log('Scan complete:', scanResult)
      setProgress(100)
      setResult(scanResult)
      
      // Save to history
      saveToHistory(scanResult)
    } catch (err) {
      console.error('Scan failed:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to scan URL. Please check the console for details.'
      setError(errorMessage)
    } finally {
      setIsScanning(false)
    }
  }

  const handleNewScan = () => {
    setUrl('')
    setResult(null)
    setError(null)
    setProgress(0)
  }

  const saveToHistory = (scanResult: ScanResult) => {
    try {
      const history = JSON.parse(localStorage.getItem('scanHistory') || '[]')
      const newEntry = {
        ...scanResult,
        scannedAt: new Date().toISOString()
      }
      history.unshift(newEntry)
      // Keep only last 50 scans
      localStorage.setItem('scanHistory', JSON.stringify(history.slice(0, 50)))
    } catch (error) {
      console.error('Failed to save to history:', error)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
        />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <Shield className="w-12 h-12 text-blue-400" />
            <h1 className="text-5xl font-bold text-white">SafeClick</h1>
          </div>
          <p className="text-xl text-gray-300">AI-Powered Phishing Detection</p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-gray-400">Powered by Claude AI</span>
          </div>
          
          {/* Navigation to History */}
          <Link href="/history">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="mt-4 px-6 py-2 bg-slate-800/50 hover:bg-slate-700/50 text-white rounded-xl transition-all flex items-center gap-2 mx-auto border border-slate-700"
            >
              <History className="w-4 h-4" />
              View Scan History
            </motion.button>
          </Link>
        </motion.div>

        {/* Main Content */}
        {!result ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="max-w-2xl mx-auto"
          >
            <div className="glass-strong rounded-3xl p-8 md:p-12">
              {!isScanning ? (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Enter URL to Analyze
                    </label>
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleScan()}
                      placeholder="https://example.com/suspicious-link"
                      className="w-full px-6 py-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    />
                  </div>

                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400"
                    >
                      {error}
                    </motion.div>
                  )}

                  <button
                    onClick={handleScan}
                    disabled={!url || isScanning}
                    className="w-full py-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold rounded-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none glow-primary"
                  >
                    Analyze URL
                  </button>

                  <p className="text-center text-sm text-gray-400">
                    Try: <code className="px-2 py-1 bg-slate-800 rounded text-blue-400">https://www.google.com</code>
                  </p>
                </div>
              ) : (
                <div className="space-y-6 text-center">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="w-20 h-20 mx-auto"
                  >
                    <Shield className="w-full h-full text-blue-400" />
                  </motion.div>

                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">Analyzing URL...</h3>
                    <p className="text-gray-400">This may take 15-20 seconds</p>
                  </div>

                  <div className="space-y-2">
                    <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                    <p className="text-sm text-gray-400">{progress}% Complete</p>
                  </div>

                  <div className="space-y-2 text-sm text-gray-400">
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: progress > 0 ? 1 : 0.3 }}
                    >
                      ✓ Submitting URL for analysis
                    </motion.p>
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: progress > 30 ? 1 : 0.3 }}
                    >
                      ✓ Capturing website screenshot
                    </motion.p>
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: progress > 60 ? 1 : 0.3 }}
                    >
                      ✓ Analyzing content with AI
                    </motion.p>
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: progress > 90 ? 1 : 0.3 }}
                    >
                      ✓ Finalizing results
                    </motion.p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-4xl mx-auto space-y-6"
          >
            {/* Phishing Detection Status */}
            <div className="flex flex-col items-center gap-4">
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center"
              >
                <p className="text-gray-400 text-sm mb-2">Phishing Detection Result</p>
                <h2 className="text-3xl font-bold text-white mb-1">
                  {result.verdict === 'Phishing' ? '⚠️ This is a Phishing Site!' : 
                   result.verdict === 'Suspicious' ? '⚠️ This Site is Suspicious' : 
                   '✅ This Site is Safe'}
                </h2>
              </motion.div>

              {/* Verdict Badge */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", duration: 0.6 }}
                className={`px-8 py-4 rounded-2xl font-bold text-2xl flex items-center gap-3 ${
                  result.verdict === 'Legitimate'
                    ? 'bg-green-500/20 text-green-400 border-2 border-green-500 glow-success'
                    : result.verdict === 'Suspicious'
                    ? 'bg-yellow-500/20 text-yellow-400 border-2 border-yellow-500 glow-warning'
                    : 'bg-red-500/20 text-red-400 border-2 border-red-500 glow-danger'
                }`}
              >
                {result.verdict === 'Legitimate' ? (
                  <CheckCircle className="w-8 h-8" />
                ) : result.verdict === 'Suspicious' ? (
                  <AlertTriangle className="w-8 h-8" />
                ) : (
                  <XCircle className="w-8 h-8" />
                )}
                {result.verdict}
              </motion.div>

              {/* Safety Recommendation */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className={`px-6 py-3 rounded-xl text-center max-w-2xl ${
                  result.verdict === 'Legitimate'
                    ? 'bg-green-500/10 border border-green-500/30'
                    : result.verdict === 'Suspicious'
                    ? 'bg-yellow-500/10 border border-yellow-500/30'
                    : 'bg-red-500/10 border border-red-500/30'
                }`}
              >
                <p className={`font-semibold ${
                  result.verdict === 'Legitimate' ? 'text-green-400' :
                  result.verdict === 'Suspicious' ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {result.verdict === 'Phishing' 
                    ? '🚫 DO NOT enter any personal information, passwords, or payment details on this site!'
                    : result.verdict === 'Suspicious'
                    ? '⚠️ Exercise caution. Verify the site\'s authenticity before entering sensitive information.'
                    : '✅ This site appears safe to visit. Always verify URLs before entering sensitive data.'}
                </p>
              </motion.div>
            </div>

            {/* Results Card */}
            <div className="glass-strong rounded-3xl p-8 md:p-12 space-y-8">
              {/* Risk Score */}
              <div className="flex justify-center">
                <div className="relative w-48 h-48">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="96"
                      cy="96"
                      r="88"
                      stroke="rgba(255,255,255,0.1)"
                      strokeWidth="12"
                      fill="none"
                    />
                    <motion.circle
                      cx="96"
                      cy="96"
                      r="88"
                      stroke={
                        result.riskScore < 30
                          ? '#10B981'
                          : result.riskScore < 70
                          ? '#F59E0B'
                          : '#EF4444'
                      }
                      strokeWidth="12"
                      fill="none"
                      strokeLinecap="round"
                      initial={{ strokeDasharray: "0 552" }}
                      animate={{
                        strokeDasharray: `${(result.riskScore / 100) * 552} 552`
                      }}
                      transition={{ duration: 1, ease: "easeOut" }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <motion.span
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.5 }}
                      className="text-5xl font-bold text-white"
                    >
                      {result.riskScore}
                    </motion.span>
                    <span className="text-gray-400">Risk Score</span>
                  </div>
                </div>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass rounded-xl p-6">
                  <p className="text-sm text-gray-400 mb-2">Confidence Level</p>
                  <p className="text-2xl font-bold text-white">{result.confidence}</p>
                </div>

                {result.detectedBrand && (
                  <div className="glass rounded-xl p-6">
                    <p className="text-sm text-gray-400 mb-2">Detected Brand</p>
                    <p className="text-2xl font-bold text-yellow-400">{result.detectedBrand}</p>
                  </div>
                )}
              </div>

              {/* Phishing Status Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className={`rounded-xl p-6 border-2 ${
                  result.verdict === 'Phishing'
                    ? 'bg-red-500/10 border-red-500'
                    : result.verdict === 'Suspicious'
                    ? 'bg-yellow-500/10 border-yellow-500'
                    : 'bg-green-500/10 border-green-500'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-full ${
                    result.verdict === 'Phishing'
                      ? 'bg-red-500/20'
                      : result.verdict === 'Suspicious'
                      ? 'bg-yellow-500/20'
                      : 'bg-green-500/20'
                  }`}>
                    {result.verdict === 'Phishing' ? (
                      <XCircle className={`w-8 h-8 ${
                        result.verdict === 'Phishing' ? 'text-red-400' : ''
                      }`} />
                    ) : result.verdict === 'Suspicious' ? (
                      <AlertTriangle className="w-8 h-8 text-yellow-400" />
                    ) : (
                      <CheckCircle className="w-8 h-8 text-green-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className={`text-xl font-bold mb-2 ${
                      result.verdict === 'Phishing'
                        ? 'text-red-400'
                        : result.verdict === 'Suspicious'
                        ? 'text-yellow-400'
                        : 'text-green-400'
                    }`}>
                      {result.verdict === 'Phishing' 
                        ? 'Phishing Detected!'
                        : result.verdict === 'Suspicious'
                        ? 'Potentially Suspicious'
                        : 'Safe to Visit'}
                    </h3>
                    <p className="text-gray-300 mb-3">
                      {result.verdict === 'Phishing'
                        ? 'This website is attempting to steal your personal information. Do not enter any credentials, payment details, or personal data.'
                        : result.verdict === 'Suspicious'
                        ? 'This website shows some suspicious characteristics. Proceed with caution and verify its authenticity before sharing sensitive information.'
                        : 'This website appears legitimate and safe to visit. However, always verify URLs and use caution when entering sensitive information online.'}
                    </p>
                    {result.verdict === 'Phishing' && (
                      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mt-3">
                        <p className="text-red-300 font-semibold text-sm">⚠️ Recommended Actions:</p>
                        <ul className="text-red-300 text-sm mt-2 space-y-1 list-disc list-inside">
                          <li>Close this website immediately</li>
                          <li>Do not enter any personal information</li>
                          <li>Report this site to your IT department or authorities</li>
                          <li>Clear your browser cache and cookies</li>
                        </ul>
                      </div>
                    )}
                    {result.verdict === 'Suspicious' && (
                      <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3 mt-3">
                        <p className="text-yellow-300 font-semibold text-sm">⚠️ Safety Tips:</p>
                        <ul className="text-yellow-300 text-sm mt-2 space-y-1 list-disc list-inside">
                          <li>Verify the URL matches the official domain</li>
                          <li>Check for HTTPS and valid SSL certificate</li>
                          <li>Look for contact information and privacy policy</li>
                          <li>Be cautious with requests for sensitive data</li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>

              {/* Explanation */}
              <div className="glass rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3">AI Analysis</h3>
                <p className="text-gray-300 leading-relaxed">{result.explanation}</p>
                
                {result.tactics && result.tactics.length > 0 && (
                  <div className="mt-4">
                    <p className="font-semibold text-white mb-2">Detected Tactics:</p>
                    <ul className="list-disc list-inside space-y-1 text-gray-300">
                      {result.tactics.map((tactic, i) => (
                        <li key={i}>{tactic}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Scan Details */}
              <div className="border-t border-gray-700 pt-6 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">URL Scanned:</span>
                  <span className="text-white font-mono text-xs">{result.url}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Processing Time:</span>
                  <span className="text-white">{(result.processingTimeMs / 1000).toFixed(2)}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Scan ID:</span>
                  <span className="text-white font-mono text-xs">{result.scanId}</span>
                </div>
              </div>

              {/* New Scan Button */}
              <button
                onClick={handleNewScan}
                className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl transition-all"
              >
                Scan Another URL
              </button>
            </div>
          </motion.div>
        )}

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-12 text-gray-400 text-sm"
        >
          <p>Powered by Claude AI</p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>API Operational</span>
          </div>
        </motion.div>
      </div>
    </main>
  )
}
