import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SafeClick - AI Phishing Detection',
  description: 'Analyze suspicious URLs in real-time using Claude AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
