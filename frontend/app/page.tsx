'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, SlidersHorizontal, RefreshCw, Download, FileText, 
  Layers, Volume2, ShieldAlert, Award, Compass, HelpCircle, 
  MapPin, Clock, BellRing, Database
} from 'lucide-react'

import { fetchPosts, fetchStats, getWebSocketUri } from '../lib/api'
import { exportToCSV, exportToPDF } from '../lib/utils'
import ClusterCard from '../components/ClusterCard'
import PostCard from '../components/PostCard'
import WordCloud from '../components/WordCloud'
import AnalyticsCharts from '../components/AnalyticsCharts'

// Wrap page in a Suspense boundary to allow Next.js query parameter hooks in app router
export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#030712]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-4 border-accent-purple/20 border-t-accent-purple animate-spin" />
          <span className="text-white/60 text-sm font-semibold uppercase tracking-wider animate-pulse">
            Booting AERO-PASS Analytics...
          </span>
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  )
}

function DashboardContent() {
  // Filters & State
  const [posts, setPosts] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [refreshing, setRefreshing] = useState<boolean>(false)
  
  // URL Param Sync Toggles
  const [search, setSearch] = useState<string>('')
  const [searchInput, setSearchInput] = useState<string>('')
  const [platform, setPlatform] = useState<string>('')
  const [category, setCategory] = useState<string>('')
  const [language, setLanguage] = useState<string>('')
  const [sentiment, setSentiment] = useState<string>('')
  const [region, setRegion] = useState<string>('')
  const [author, setAuthor] = useState<string>('')
  const [authorInput, setAuthorInput] = useState<string>('')
  const [sortBy, setSortBy] = useState<string>('created_at')
  const [clustered, setClustered] = useState<boolean>(true)

  // WebSocket Live Updates
  const [socketMessage, setSocketMessage] = useState<{ count: number; timestamp: string } | null>(null)

  // Infinite Scroll Slice
  const [visibleCount, setVisibleCount] = useState<number>(15)

  // Debounce search input changes
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      setSearch(searchInput)
    }, 300)

    return () => clearTimeout(delayDebounce)
  }, [searchInput])

  // Debounce author/creator input changes
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      setAuthor(authorInput)
    }, 300)

    return () => clearTimeout(delayDebounce)
  }, [authorInput])

  // Initialize filters from URL parameters on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      if (params.get('search')) {
        const s = params.get('search') || ''
        setSearch(s)
        setSearchInput(s)
      }
      if (params.get('platform')) setPlatform(params.get('platform') || '')
      if (params.get('category')) setCategory(params.get('category') || '')
      if (params.get('language')) setLanguage(params.get('language') || '')
      if (params.get('sentiment')) setSentiment(params.get('sentiment') || '')
      if (params.get('region')) setRegion(params.get('region') || '')
      if (params.get('author')) {
        const a = params.get('author') || ''
        setAuthor(a)
        setAuthorInput(a)
      }
      if (params.get('sort_by')) setSortBy(params.get('sort_by') || 'created_at')
      if (params.get('clustered')) setClustered(params.get('clustered') !== 'false')
    }
  }, [])

  // Sync state back to URL parameters to preserve filter states (deep-linking)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (platform) params.set('platform', platform)
      if (category) params.set('category', category)
      if (language) params.set('language', language)
      if (sentiment) params.set('sentiment', sentiment)
      if (region) params.set('region', region)
      if (author) params.set('author', author)
      if (sortBy !== 'created_at') params.set('sort_by', sortBy)
      if (!clustered) params.set('clustered', 'false')
      
      const newRelativePathQuery = window.location.pathname + (params.toString() ? '?' + params.toString() : '')
      window.history.replaceState(null, '', newRelativePathQuery)
    }
  }, [search, platform, category, language, sentiment, region, author, sortBy, clustered])

  const loadData = async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) setRefreshing(true)
    else setLoading(true)
    
    try {
      const [postsData, statsData] = await Promise.all([
        fetchPosts({
          platform,
          category,
          language,
          sentiment,
          search,
          sort_by: sortBy,
          clustered,
          region,
          author
        }),
        fetchStats()
      ])
      
      setPosts(postsData)
      setStats(statsData)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  // Load whenever filters change
  useEffect(() => {
    loadData()
  }, [search, platform, category, language, sentiment, region, author, sortBy, clustered])

  // Setup WebSocket connection for live notifications
  useEffect(() => {
    let ws: WebSocket
    const connectWS = () => {
      try {
        ws = new WebSocket(getWebSocketUri())
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'NEW_POSTS') {
              setSocketMessage({
                count: data.count,
                timestamp: data.timestamp
              })
            }
          } catch (e) {
            console.error(e)
          }
        }

        ws.onclose = () => {
          // Reconnect after 5 seconds
          setTimeout(connectWS, 5000)
        }
      } catch (err) {
        console.error("WS Connection failed, fallback to polling:", err)
      }
    }

    connectWS()
    return () => {
      if (ws) ws.close()
    }
  }, [])

  const handleRefresh = () => {
    setSocketMessage(null)
    loadData(true)
  }

  const handleWordCloudClick = (word: string) => {
    setSearchInput(word)
    setSearch(word)
  }

  const handleExportCSV = () => {
    // Flatten clustered duplicates if any for full data exporting
    const allPostsFlattened: any[] = []
    posts.forEach(p => {
      allPostsFlattened.push(p)
      if (p.duplicates) {
        p.duplicates.forEach((dup: any) => allPostsFlattened.push(dup))
      }
    })
    exportToCSV(allPostsFlattened)
  }

  const activeFiltersCount = [platform, category, language, sentiment, region, author].filter(Boolean).length

  const clearAllFilters = () => {
    setPlatform('')
    setCategory('')
    setLanguage('')
    setSentiment('')
    setRegion('')
    setAuthorInput('')
    setAuthor('')
    setSearchInput('')
    setSearch('')
  }

  return (
    <div className="min-h-screen relative flex flex-col pb-12 bg-background print:bg-white print:text-black">
      {/* Background Neon Glowing Orbs */}
      <div className="pulse-glow w-[500px] h-[500px] bg-accent-purple/10 top-[-100px] left-[-100px]" />
      <div className="pulse-glow w-[400px] h-[400px] bg-accent-cyan/10 top-[20%] right-[-50px]" />
      <div className="pulse-glow w-[600px] h-[600px] bg-accent-pink/5 bottom-[-200px] left-[20%]" />

      {/* Top Banner Live Alert */}
      <AnimatePresence>
        {socketMessage && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            onClick={handleRefresh}
            className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 flex items-center gap-3 px-6 py-3 rounded-full border border-accent-cyan/30 bg-[#070b13]/90 backdrop-blur-md cursor-pointer hover:border-accent-cyan transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)] animate-bounce"
          >
            <BellRing className="w-5 h-5 text-accent-cyan animate-pulse" />
            <span className="text-sm font-bold text-white">
              {socketMessage.count} new passport posts ingested! Click to load.
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header Bar */}
      <header className="border-b border-white/5 bg-background/50 backdrop-blur-md sticky top-0 z-40 print:hidden">
        <div className="max-w-7xl mx-auto px-6 h-18 flex items-center justify-between py-4">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-accent-purple via-accent-pink to-accent-cyan flex items-center justify-center font-extrabold text-white text-lg tracking-tighter">
              A
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-2">
                AERO-PASS <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/20">LIVE SCAPING</span>
              </h1>
              <p className="text-[10px] font-semibold text-white/50">24-Hour Social Media Analytics Dashboard</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/5 hover:border-white/10 bg-white/5 text-white/80 hover:text-white transition-all text-xs font-semibold"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Syncing...' : 'Sync Feed'}</span>
            </button>

            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-accent-purple/20 bg-accent-purple/5 text-accent-purple hover:bg-accent-purple/15 transition-all text-xs font-semibold"
            >
              <Download className="w-3.5 h-3.5" />
              <span>CSV</span>
            </button>

            <button
              onClick={exportToPDF}
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-accent-pink/20 bg-accent-pink/5 text-accent-pink hover:bg-accent-pink/15 transition-all text-xs font-semibold"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>PDF Report</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Grid Layout */}
      <main className="max-w-7xl mx-auto px-6 w-full flex-1 mt-8">
        
        {/* Core Analytics Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 print:hidden">
          <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between">
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-wider">Total Scraped</span>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-2xl font-black text-white">{stats?.total_posts ?? 0}</span>
              <span className="text-xs text-accent-green font-semibold">24h roll</span>
            </div>
            <div className="text-[10px] text-white/50 mt-1 flex items-center gap-1">
              <Database className="w-3 h-3 text-accent-cyan" />
              <span>SQLite/PG Dynamic</span>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between">
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-wider">Appointments & Tatkal</span>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-2xl font-black text-white">
                {stats?.categories?.find((c: any) => c.category === 'Appointments')?.count ?? 0}
              </span>
              <span className="text-xs text-accent-purple font-semibold">high load</span>
            </div>
            <div className="text-[10px] text-white/50 mt-1 flex items-center gap-1">
              <Clock className="w-3 h-3 text-accent-purple" />
              <span>Booking constraints</span>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between">
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-wider">Scams / Fraud Alerts</span>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-2xl font-black text-accent-pink">
                {stats?.categories?.find((c: any) => c.category === 'Scams/Fraud')?.count ?? 0}
              </span>
              <span className="text-xs text-accent-pink font-semibold">watch list</span>
            </div>
            <div className="text-[10px] text-white/50 mt-1 flex items-center gap-1">
              <ShieldAlert className="w-3 h-3 text-accent-pink" />
              <span>Urgent response needed</span>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between">
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-wider">Regional Spread</span>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-2xl font-black text-white">{stats?.regions?.length ?? 0}</span>
              <span className="text-xs text-accent-cyan font-semibold">regions</span>
            </div>
            <div className="text-[10px] text-white/50 mt-1 flex items-center gap-1">
              <MapPin className="w-3 h-3 text-accent-cyan" />
              <span>NER Geo extraction</span>
            </div>
          </div>
        </div>

        {/* Charts & Interactive Word Cloud Row */}
        <div className="grid grid-cols-1 gap-6 mb-6 print:hidden">
          {stats && (
            <AnalyticsCharts 
              categories={stats.categories.map((c: any) => ({ name: c.category, count: c.count }))} 
              platforms={stats.platforms.map((p: any) => ({ name: p.platform, count: p.count }))}
            />
          )}

          {stats?.word_cloud && (
            <div className="flex flex-col gap-3">
              <h3 className="text-xs font-bold uppercase text-white/50 tracking-wider pl-1">
                Trending Passport Keywords (Click to Filter)
              </h3>
              <WordCloud 
                words={stats.word_cloud} 
                onWordClick={handleWordCloudClick} 
                activeSearch={search}
              />
            </div>
          )}
        </div>

        {/* Filters and Feed Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start mt-8 print:block">
          
          {/* Sidebar Filters */}
          <aside className="glass-panel p-6 rounded-2xl lg:sticky lg:top-24 flex flex-col gap-5 print:hidden">
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <SlidersHorizontal className="w-4 h-4 text-accent-cyan" />
                <span>Quick Filters</span>
              </div>
              {activeFiltersCount > 0 && (
                <button
                  onClick={clearAllFilters}
                  className="text-[10px] font-semibold text-accent-pink hover:underline uppercase"
                >
                  Clear ({activeFiltersCount})
                </button>
              )}
            </div>

            {/* Keyword Search */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">Search Keywords</label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Query names, descriptions..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-white/5 bg-white/5 text-white placeholder-white/30 focus:outline-none focus:border-accent-purple/50 transition-all"
                />
                <Search className="w-4 h-4 text-white/30 absolute left-3 top-2.5" />
              </div>
            </div>

            {/* Creator / Handle Search */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">Creator / Handle</label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="e.g. u/author, @handle"
                  value={authorInput}
                  onChange={(e) => setAuthorInput(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-white/5 bg-white/5 text-white placeholder-white/30 focus:outline-none focus:border-accent-purple/50 transition-all"
                />
                <Search className="w-4 h-4 text-white/30 absolute left-3 top-2.5" />
              </div>
            </div>

            {/* Platform Select */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">Social Platform</label>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-white/5 bg-white/5 text-white/80 focus:outline-none focus:border-accent-purple/50 transition-all capitalize"
              >
                <option value="" className="bg-[#0b0f19]">All Platforms</option>
                <option value="twitter" className="bg-[#0b0f19]">Twitter / X</option>
                <option value="reddit" className="bg-[#0b0f19]">Reddit</option>
                <option value="youtube" className="bg-[#0b0f19]">YouTube</option>
                <option value="instagram" className="bg-[#0b0f19]">Instagram</option>
                <option value="facebook" className="bg-[#0b0f19]">Facebook</option>
                <option value="linkedin" className="bg-[#0b0f19]">LinkedIn</option>
              </select>
            </div>

            {/* Category Select */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">NLP Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-white/5 bg-white/5 text-white/80 focus:outline-none focus:border-accent-purple/50 transition-all"
              >
                <option value="" className="bg-[#0b0f19]">All Categories</option>
                <option value="Application" className="bg-[#0b0f19]">Application</option>
                <option value="Renewal" className="bg-[#0b0f19]">Renewal</option>
                <option value="Appointments" className="bg-[#0b0f19]">Appointments</option>
                <option value="Tatkal" className="bg-[#0b0f19]">Tatkal</option>
                <option value="Visa" className="bg-[#0b0f19]">Visa</option>
                <option value="Travel Issues" className="bg-[#0b0f19]">Travel Issues</option>
                <option value="Government Announcements" className="bg-[#0b0f19]">Announcements</option>
                <option value="Scams/Fraud" className="bg-[#0b0f19]">Scams/Fraud</option>
                <option value="News" className="bg-[#0b0f19]">News</option>
                <option value="Personal Experiences" className="bg-[#0b0f19]">Personal Experiences</option>
              </select>
            </div>

            {/* Sentiment Select */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">NLP Sentiment</label>
              <select
                value={sentiment}
                onChange={(e) => setSentiment(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-white/5 bg-white/5 text-white/80 focus:outline-none focus:border-accent-purple/50 transition-all capitalize"
              >
                <option value="" className="bg-[#0b0f19]">All Sentiments</option>
                <option value="positive" className="bg-[#0b0f19]">Positive</option>
                <option value="neutral" className="bg-[#0b0f19]">Neutral</option>
                <option value="negative" className="bg-[#0b0f19]">Negative</option>
              </select>
            </div>

            {/* Language Select */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">Original Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-white/5 bg-white/5 text-white/80 focus:outline-none focus:border-accent-purple/50 transition-all capitalize"
              >
                <option value="" className="bg-[#0b0f19]">All Languages</option>
                <option value="en" className="bg-[#0b0f19]">English</option>
                <option value="hi" className="bg-[#0b0f19]">Hindi (हिंदी)</option>
              </select>
            </div>

            {/* Region / Location Select */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">Region / Location</label>
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-white/5 bg-white/5 text-white/80 focus:outline-none focus:border-accent-purple/50 transition-all capitalize"
              >
                <option value="" className="bg-[#0b0f19]">All Regions</option>
                {stats?.regions?.map((r: any) => (
                  <option key={r.region} value={r.region} className="bg-[#0b0f19]">
                    {r.region} ({r.count})
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Order */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold text-white/50 uppercase tracking-wider">Sorting Metrics</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setSortBy('created_at')}
                  className={`py-2 text-[10px] font-bold uppercase rounded-lg border transition-all ${
                    sortBy === 'created_at'
                      ? 'border-accent-cyan bg-accent-cyan/10 text-accent-cyan shadow-[0_0_10px_rgba(6,182,212,0.15)]'
                      : 'border-white/5 bg-white/5 text-white/60 hover:text-white'
                  }`}
                >
                  Time
                </button>
                <button
                  onClick={() => setSortBy('engagement')}
                  className={`py-2 text-[10px] font-bold uppercase rounded-lg border transition-all ${
                    sortBy === 'engagement'
                      ? 'border-accent-purple bg-accent-purple/10 text-accent-purple shadow-[0_0_10px_rgba(139,92,246,0.15)]'
                      : 'border-white/5 bg-white/5 text-white/60 hover:text-white'
                  }`}
                >
                  Popularity
                </button>
              </div>
            </div>

            {/* Clustered View Toggle */}
            <div className="flex items-center justify-between pt-3 border-t border-white/5 mt-2">
              <div className="flex flex-col">
                <span className="text-xs font-bold text-white">Cluster Similar</span>
                <span className="text-[9px] text-white/40">Groups duplicate threads</span>
              </div>
              <button
                onClick={() => setClustered(!clustered)}
                className={`w-10 h-6 rounded-full p-1 transition-all ${
                  clustered ? 'bg-accent-cyan' : 'bg-white/10'
                }`}
              >
                <div className={`w-4 h-4 rounded-full bg-white transition-all transform ${
                  clustered ? 'translate-x-4' : 'translate-x-0'
                }`} />
              </button>
            </div>

          </aside>

          {/* Main Feed Section */}
          <section className="lg:col-span-3 flex flex-col gap-6 print:block">
            
            {/* Header info */}
            <div className="flex items-center justify-between print:hidden">
              <span className="text-xs font-bold text-white/50 tracking-wider">
                Showing {Math.min(visibleCount, posts.length)} of {posts.length} passport discussion blocks
              </span>
              
              {clustered && (
                <span className="flex items-center gap-1.5 text-xs text-accent-cyan bg-accent-cyan/5 border border-accent-cyan/15 px-2.5 py-1 rounded-full font-medium">
                  <Layers className="w-3.5 h-3.5 animate-pulse" />
                  <span>DBSCAN Embeddings Cluster Active</span>
                </span>
              )}
            </div>

            {/* Print Header (Only visible when printing to PDF) */}
            <div className="hidden print:block mb-8">
              <h1 className="text-3xl font-black">AERO-PASS Passport Social Analytics Report</h1>
              <p className="text-sm text-gray-500" suppressHydrationWarning>Generated on: {new Date().toLocaleString()} | Metric: Last 24 Hours</p>
              <div className="mt-4 p-4 border rounded-xl bg-gray-50 grid grid-cols-3 text-center text-xs">
                <div>Total Ingested: <span className="font-bold">{posts.length}</span></div>
                <div>Category: <span className="font-bold">{category || 'All'}</span></div>
                <div>Platform: <span className="font-bold">{platform || 'All'}</span></div>
              </div>
            </div>

            {loading ? (
              // Loading Skeleton Feed
              <div className="flex flex-col gap-6 w-full print:hidden">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="glass-panel p-6 rounded-2xl flex flex-col gap-4 animate-pulse">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-white/5" />
                        <div className="flex flex-col gap-2">
                          <div className="w-24 h-3 bg-white/5 rounded" />
                          <div className="w-16 h-2.5 bg-white/5 rounded" />
                        </div>
                      </div>
                      <div className="w-16 h-4 bg-white/5 rounded" />
                    </div>
                    <div className="w-full h-12 bg-white/5 rounded-xl" />
                    <div className="w-full h-8 bg-white/5 rounded-lg" />
                  </div>
                ))}
              </div>
            ) : posts.length === 0 ? (
              // Empty Feed State
              <div className="glass-panel p-12 rounded-2xl text-center flex flex-col items-center justify-center gap-4">
                <SlidersHorizontal className="w-12 h-12 text-white/20 animate-bounce" />
                <h3 className="text-lg font-black text-white">No discussions found matching criteria</h3>
                <p className="text-xs text-white/50 max-w-sm">
                  Try clearing some of your search keywords or active filters to view all passport-related queries.
                </p>
                <button
                  onClick={clearAllFilters}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-accent-purple to-accent-cyan text-xs font-bold text-white shadow-lg"
                >
                  Clear All Filters
                </button>
              </div>
            ) : (
              // Feed Content
              <div className="flex flex-col gap-6 print:block print:space-y-6">
                {posts.slice(0, visibleCount).map((postBlock) => (
                  <div key={postBlock.post_id} className="print:break-inside-avoid">
                    {clustered ? (
                      <ClusterCard cluster={postBlock} />
                    ) : (
                      <PostCard post={postBlock} />
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Load More Button for Infinite Scroll */}
            {!loading && posts.length > visibleCount && (
              <div className="flex justify-center mt-6 print:hidden">
                <button
                  onClick={() => setVisibleCount(prev => prev + 15)}
                  className="px-6 py-2.5 rounded-xl border border-white/5 hover:border-white/10 bg-white/5 hover:bg-white/10 text-xs font-bold text-white transition-all"
                >
                  Load More Discussions
                </button>
              </div>
            )}

          </section>

        </div>

      </main>
    </div>
  )
}
