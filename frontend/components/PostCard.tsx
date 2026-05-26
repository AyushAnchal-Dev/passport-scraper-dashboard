'use client'

import React, { useState } from 'react'
import { motion, useMotionValue, useTransform } from 'framer-motion'
import { MessageSquare, Heart, Share2, Eye, Globe, MapPin, ChevronDown, Check, Loader2 } from 'lucide-react'
import { translatePost } from '../lib/api'
import { formatDate } from '../lib/utils'

interface PostCardProps {
  post: {
    post_id: string
    platform: string
    author: string
    author_avatar?: string
    url?: string
    content: string
    created_at: string
    likes: number
    reposts: number
    comments: number
    views: number
    category?: string
    sentiment?: string
    summary?: string
    original_language: string
    geolocation?: { city: string; country: string }
  }
}

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi' },
  { code: 'pa', name: 'Punjabi' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'ar', name: 'Arabic' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ru', name: 'Russian' },
  { code: 'ja', name: 'Japanese' }
]

export default function PostCard({ post }: PostCardProps) {
  const [translatedText, setTranslatedText] = useState<string | null>(null)
  const [translatedSummary, setTranslatedSummary] = useState<string | null>(null)
  const [activeLang, setActiveLang] = useState<string>('original')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false)

  // 3D Card Hover Tilt Coordinates
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const rotateX = useTransform(y, [-100, 100], [10, -10])
  const rotateY = useTransform(x, [-100, 100], [-10, 10])

  function handleMouseMove(event: React.MouseEvent<HTMLDivElement, MouseEvent>) {
    const el = event.currentTarget
    const rect = el.getBoundingClientRect()
    const width = rect.width
    const height = rect.height
    const mouseX = event.clientX - rect.left - width / 2
    const mouseY = event.clientY - rect.top - height / 2
    x.set(mouseX)
    y.set(mouseY)
  }

  function handleMouseLeave() {
    x.set(0)
    y.set(0)
  }

  const handleTranslate = async (langCode: string) => {
    setDropdownOpen(false)
    if (langCode === 'original') {
      setActiveLang('original')
      setTranslatedText(null)
      setTranslatedSummary(null)
      return
    }
    
    setIsLoading(true)
    try {
      const data = await translatePost(post.post_id, langCode)
      setTranslatedText(data.translated_content)
      setTranslatedSummary(data.translated_summary)
      setActiveLang(langCode)
    } catch (e) {
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }

  const sentimentStyles: Record<string, string> = {
    positive: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.15)]',
    negative: 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.15)]',
    neutral: 'bg-slate-500/10 text-slate-400 border-slate-500/20'
  }

  const platformGlows: Record<string, string> = {
    twitter: 'hover:border-sky-500/30 hover:shadow-[0_0_20px_rgba(14,165,233,0.15)]',
    reddit: 'hover:border-orange-500/30 hover:shadow-[0_0_20px_rgba(249,115,22,0.15)]',
    facebook: 'hover:border-blue-600/30 hover:shadow-[0_0_20px_rgba(37,99,235,0.15)]',
    instagram: 'hover:border-pink-500/30 hover:shadow-[0_0_20px_rgba(236,72,153,0.15)]',
    linkedin: 'hover:border-blue-500/30 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)]',
    youtube: 'hover:border-red-600/30 hover:shadow-[0_0_20px_rgba(220,38,38,0.15)]',
    tiktok: 'hover:border-teal-400/30 hover:shadow-[0_0_20px_rgba(45,212,191,0.15)]',
  }

  return (
    <motion.div
      style={{ rotateX, rotateY, z: 100 }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={cn(
        "glass-panel relative flex flex-col p-6 rounded-2xl transition-all duration-300 transform-style-3d cursor-default border border-white/5",
        platformGlows[post.platform.toLowerCase()] || "hover:border-accent-purple/30 hover:shadow-[0_0_20px_rgba(139,92,246,0.15)]"
      )}
    >
      {/* Top Header */}
      <div className="flex items-start justify-between w-full mb-4">
        <div className="flex items-center gap-3">
          <img
            src={post.author_avatar || `https://api.dicebear.com/7.x/initials/svg?seed=${post.author}`}
            alt={post.author}
            className="w-10 h-10 rounded-full border border-white/10"
          />
          <div>
            <div className="font-semibold text-white text-sm">{post.author}</div>
            <div className="text-xs text-white/50 flex items-center gap-1.5 capitalize">
              <span className={cn(
                "inline-block w-2.5 h-2.5 rounded-full",
                post.platform === 'twitter' ? 'bg-sky-400' :
                post.platform === 'reddit' ? 'bg-orange-500' :
                post.platform === 'youtube' ? 'bg-red-600' :
                post.platform === 'instagram' ? 'bg-pink-500' :
                post.platform === 'linkedin' ? 'bg-blue-500' : 'bg-accent-purple'
              )} />
              {post.platform} • <span suppressHydrationWarning>{formatDate(post.created_at)}</span>
            </div>
          </div>
        </div>

        {/* NLP Indicators */}
        <div className="flex items-center gap-2">
          {post.category && (
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-accent-purple/20 text-accent-purple bg-accent-purple/5">
              {post.category}
            </span>
          )}
          {post.sentiment && (
            <span className={cn(
              "text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border capitalize",
              sentimentStyles[post.sentiment] || sentimentStyles.neutral
            )}>
              {post.sentiment}
            </span>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col mb-4">
        {/* original/translated text toggles */}
        <div className="text-white/90 text-sm leading-relaxed mb-3 break-words relative min-h-[3.5rem]">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-black/10 rounded">
              <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
            </div>
          ) : null}
          
          {activeLang === 'original' ? post.content : translatedText || post.content}
        </div>

        {/* Post Summary Widget */}
        {(post.summary || translatedSummary) && (
          <div className="bg-white/5 border border-white/5 rounded-xl p-3.5 mt-auto">
            <div className="text-[10px] font-bold text-accent-cyan tracking-wider uppercase mb-1">
              AI Summary (~30 words)
            </div>
            <div className="text-xs text-white/70 italic leading-relaxed">
              "{activeLang === 'original' ? post.summary : translatedSummary || post.summary}"
            </div>
          </div>
        )}
      </div>

      {/* Bottom Footer Info */}
      <div className="flex items-center justify-between border-t border-white/5 pt-4 mt-auto">
        <div className="flex items-center gap-4 text-white/50 text-xs">
          {post.geolocation && (
            <div className="flex items-center gap-1 text-accent-pink bg-accent-pink/5 border border-accent-pink/10 px-2 py-0.5 rounded-full">
              <MapPin className="w-3.5 h-3.5" />
              <span>{post.geolocation.city}, {post.geolocation.country}</span>
            </div>
          )}
          
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1"><Heart className="w-3.5 h-3.5" /> {post.likes}</span>
            <span className="flex items-center gap-1"><MessageSquare className="w-3.5 h-3.5" /> {post.comments}</span>
            {post.reposts > 0 && <span className="flex items-center gap-1"><Share2 className="w-3.5 h-3.5" /> {post.reposts}</span>}
            {post.views > 0 && <span className="flex items-center gap-1"><Eye className="w-3.5 h-3.5" /> {post.views}</span>}
          </div>
        </div>

        {/* Translation Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 hover:border-white/20 text-xs font-medium text-white/80 hover:text-white transition-all bg-white/5 hover:bg-white/10"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{LANGUAGES.find(l => l.code === activeLang)?.name || 'Original'}</span>
            <ChevronDown className="w-3.5 h-3.5 opacity-60" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 bottom-full mb-2 w-40 rounded-xl bg-[#0b0f19] border border-white/10 p-1.5 shadow-2xl z-50 overflow-hidden max-h-64 overflow-y-auto">
              <button
                onClick={() => handleTranslate('original')}
                className="flex items-center justify-between w-full px-2.5 py-1.5 text-left text-xs rounded-lg hover:bg-white/5 text-white/70 hover:text-white"
              >
                <span>Original</span>
                {activeLang === 'original' && <Check className="w-3.5 h-3.5 text-accent-cyan" />}
              </button>
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleTranslate(lang.code)}
                  className="flex items-center justify-between w-full px-2.5 py-1.5 text-left text-xs rounded-lg hover:bg-white/5 text-white/70 hover:text-white"
                >
                  <span>{lang.name}</span>
                  {activeLang === lang.code && <Check className="w-3.5 h-3.5 text-accent-cyan" />}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function cn(...classes: any[]) {
  return classes.filter(Boolean).join(' ')
}
