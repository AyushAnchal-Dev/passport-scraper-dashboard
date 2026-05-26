import './globals.css'
import type { Metadata, Viewport } from 'next'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#030712',
}

export const metadata: Metadata = {
  title: 'AERO-PASS | Passport Social Analytics & Scraper Dashboard',
  description:
    'Real-time social media analytics dashboard for passport services — scraping, NLP categorization, sentiment analysis, DBSCAN clustering, and multi-language translation across Reddit, Twitter/X, Instagram, YouTube, LinkedIn, and Facebook.',
  keywords: [
    'passport',
    'social media scraper',
    'NLP analytics',
    'sentiment analysis',
    'passport seva',
    'tatkal passport',
    'visa tracker',
    'travel issues',
    'DBSCAN clustering',
    'real-time dashboard',
  ],
  authors: [{ name: 'AERO-PASS Team' }],
  creator: 'AERO-PASS',
  publisher: 'AERO-PASS',
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    title: 'AERO-PASS | Passport Social Analytics Dashboard',
    description:
      'Intelligent real-time social scraper and NLP engine for passport applications, renewals, visas, scams, and travel issues. 6 platforms, 10 NLP categories, live clustering.',
    siteName: 'AERO-PASS',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AERO-PASS Dashboard',
    description:
      'Real-time passport social media analytics with NLP categorization, sentiment analysis, and DBSCAN clustering.',
    creator: '@aeropass',
  },
  icons: {
    icon: '/favicon.ico',
  },
  manifest: '/manifest.json',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
