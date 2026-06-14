'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Shield, ArrowLeft, Trash2, Search, Filter, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import Link from 'next/link'
import type { ScanResult } from '@/lib/api'

interface HistoryEntry extends ScanResult {
  scannedAt: string
}

export default function History() {
  const [scans, setScans] = useState<HistoryEntry[]>([])
  const [filteredScans, setFilteredScans] = useState<HistoryEntry[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [filterVerdict, setFilterVerdict] = useState<string>('all')

  useEffect(() => {
    // Load from localStorage
    const history = JSON.parse(localStorage.getItem('scanHistory') || '[]')
    setScans(history)
    setFilteredScans(history)
  }, [])

  useEffect(() => {
    // Apply filters
    let filtered = scans

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(scan => 
        scan.url.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Verdict filter
    if (filterVerdict !== 'all') {
      filtered = filtered.filter(scan => scan.verdict === filterVerdict)
    }

    setFilteredScans(filtered)
  }, [searchQuery, filterVerdict, scans])

  const clearHistory = () => {
    if (confirm('Are you sure you want to clear all scan history?')) {
      localStorage.removeItem('scanHistory')
      setScans([])
      setFilteredScans([])
    }
  }

  const deleteScan = (index: number) => {
    const newScans = scans.filter((_, i) => i !== index)
    localStorage.setItem('scanHistory', JSON.stringify(newScans))
    setScans(newScans)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const phishingCount = scans.filter(s => s.verdict === 'Phishing').length
  const suspiciousCount = scans.filter(s => s.verdict === 'Suspicious').length
  const legitimateCount = scans.filter(s => s.verdict === 'Legitimate').length

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
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Link href="/">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="mb-4 px-4 py-2 bg-slate-800/50 hover:bg-slate-700/50 text-white rounded-xl transition-all flex items-center gap-2 border border-slate-700"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Scanner
            </motion.button>
          </Link>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-10 h-10 text-blue-400" />
              <h1 className="text-4xl font-bold text-white">Scan History</h1>
            </div>
            {scans.length > 0 && (
              <button
                onClick={clearHistory}
                className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-xl transition-all flex items-center gap-2 border border-red-500/50"
              >
                <Trash2 className="w-4 h-4" />
                Clear All
              </button>
            )}
          </div>
        </motion.div>

        {scans.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-strong rounded-3xl p-12 text-center"
          >
            <Shield className="w-20 h-20 text-gray-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">No Scan History</h2>
            <p className="text-gray-400 mb-6">Start scanning URLs to build your history</p>
            <Link href="/">
              <button className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold rounded-xl transition-all">
                Scan Your First URL
              </button>
            </Link>
          </motion.div>
        ) : (
          <>
            {/* Statistics Cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
            >
              <div className="glass-strong rounded-xl p-6">
                <p className="text-gray-400 text-sm mb-1">Total Scans</p>
                <p className="text-4xl font-bold text-white">{scans.length}</p>
              </div>
              <div className="glass-strong rounded-xl p-6">
                <p className="text-gray-400 text-sm mb-1">Phishing Detected</p>
                <p className="text-4xl font-bold text-red-400">{phishingCount}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {scans.length > 0 ? Math.round((phishingCount / scans.length) * 100) : 0}% of total
                </p>
              </div>
              <div className="glass-strong rounded-xl p-6">
                <p className="text-gray-400 text-sm mb-1">Suspicious</p>
                <p className="text-4xl font-bold text-yellow-400">{suspiciousCount}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {scans.length > 0 ? Math.round((suspiciousCount / scans.length) * 100) : 0}% of total
                </p>
              </div>
              <div className="glass-strong rounded-xl p-6">
                <p className="text-gray-400 text-sm mb-1">Safe Sites</p>
                <p className="text-4xl font-bold text-green-400">{legitimateCount}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {scans.length > 0 ? Math.round((legitimateCount / scans.length) * 100) : 0}% of total
                </p>
              </div>
            </motion.div>

            {/* Search and Filter */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-strong rounded-xl p-6 mb-6"
            >
              <div className="flex flex-col md:flex-row gap-4">
                {/* Search */}
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search URLs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Filter */}
                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <select
                    value={filterVerdict}
                    onChange={(e) => setFilterVerdict(e.target.value)}
                    className="pl-10 pr-8 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none cursor-pointer"
                  >
                    <option value="all">All Results</option>
                    <option value="Legitimate">Legitimate Only</option>
                    <option value="Suspicious">Suspicious Only</option>
                    <option value="Phishing">Phishing Only</option>
                  </select>
                </div>
              </div>

              {filteredScans.length !== scans.length && (
                <p className="text-sm text-gray-400 mt-3">
                  Showing {filteredScans.length} of {scans.length} scans
                </p>
              )}
            </motion.div>

            {/* Scan List */}
            <div className="space-y-4">
              {filteredScans.length === 0 ? (
                <div className="glass-strong rounded-xl p-8 text-center">
                  <p className="text-gray-400">No scans match your filters</p>
                </div>
              ) : (
                filteredScans.map((scan, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="glass-strong rounded-xl p-6 hover:bg-slate-800/50 transition-all"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      {/* Left: URL and Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-3 mb-2">
                          {scan.verdict === 'Legitimate' ? (
                            <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                          ) : scan.verdict === 'Suspicious' ? (
                            <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-1" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-1" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-white font-semibold break-all">{scan.url}</p>
                            <p className="text-gray-400 text-sm mt-1">{formatDate(scan.scannedAt)}</p>
                          </div>
                        </div>

                        {/* Additional Info */}
                        <div className="flex flex-wrap gap-3 ml-8 text-sm">
                          <span className="text-gray-400">
                            Risk Score: <span className={`font-semibold ${
                              scan.riskScore < 30 ? 'text-green-400' :
                              scan.riskScore < 70 ? 'text-yellow-400' :
                              'text-red-400'
                            }`}>{scan.riskScore}</span>
                          </span>
                          {scan.detectedBrand && (
                            <span className="text-gray-400">
                              Brand: <span className="text-yellow-400 font-semibold">{scan.detectedBrand}</span>
                            </span>
                          )}
                          <span className="text-gray-400">
                            Confidence: <span className="text-white font-semibold">{scan.confidence}</span>
                          </span>
                        </div>
                      </div>

                      {/* Right: Verdict Badge and Actions */}
                      <div className="flex items-center gap-3">
                        <div className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap ${
                          scan.verdict === 'Legitimate' ? 'bg-green-500/20 text-green-400 border border-green-500/50' :
                          scan.verdict === 'Suspicious' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50' :
                          'bg-red-500/20 text-red-400 border border-red-500/50'
                        }`}>
                          {scan.verdict}
                        </div>
                        <button
                          onClick={() => deleteScan(index)}
                          className="p-2 hover:bg-red-500/20 text-gray-400 hover:text-red-400 rounded-lg transition-all"
                          title="Delete scan"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Explanation (collapsible) */}
                    {scan.explanation && (
                      <details className="mt-4 ml-8">
                        <summary className="text-sm text-blue-400 cursor-pointer hover:text-blue-300">
                          View Analysis
                        </summary>
                        <p className="text-gray-300 text-sm mt-2 leading-relaxed">
                          {scan.explanation}
                        </p>
                      </details>
                    )}
                  </motion.div>
                ))
              )}
            </div>
          </>
        )}
      </div>
    </main>
  )
}
