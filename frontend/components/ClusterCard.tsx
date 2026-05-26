'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Layers, ChevronDown, ChevronUp } from 'lucide-react'
import PostCard from './PostCard'

interface ClusterCardProps {
  cluster: {
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
    duplicates: any[]
    cluster_size: number
  }
}

export default function ClusterCard({ cluster }: ClusterCardProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false)

  const hasDuplicates = cluster.duplicates && cluster.duplicates.length > 0

  return (
    <div className="flex flex-col gap-3 w-full">
      {/* Primary Clustered Card */}
      <div className="relative group">
        {/* Decorative Stack Effect under the card */}
        {hasDuplicates && !isExpanded && (
          <>
            <div className="absolute inset-x-2 -bottom-2 h-10 rounded-2xl bg-black/40 border border-white/5 -z-10 transition-all duration-300 group-hover:-bottom-3 scale-[0.97]" />
            <div className="absolute inset-x-4 -bottom-4 h-10 rounded-2xl bg-black/50 border border-white/5 -z-20 transition-all duration-300 group-hover:-bottom-5 scale-[0.94]" />
          </>
        )}

        {/* Stack Label Badge */}
        {hasDuplicates && (
          <div className="absolute -top-3.5 right-6 flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-accent-purple to-accent-cyan text-[10px] font-bold text-white uppercase tracking-wider shadow-lg border border-white/10 z-20">
            <Layers className="w-3.5 h-3.5" />
            <span>{cluster.cluster_size} Similar Posts</span>
          </div>
        )}

        {/* The representative post */}
        <PostCard post={cluster} />
      </div>

      {/* Expand/Collapse Trigger */}
      {hasDuplicates && (
        <div className="flex justify-center -mt-1.5">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-full border border-white/5 hover:border-white/10 bg-[#0e1424]/90 hover:bg-[#141b2f] text-xs font-semibold tracking-wider text-accent-cyan hover:text-white transition-all shadow-[0_4px_12px_rgba(6,182,212,0.1)] hover:shadow-[0_4px_15px_rgba(6,182,212,0.2)]"
          >
            {isExpanded ? (
              <>
                <span>Collapse Thread</span>
                <ChevronUp className="w-3.5 h-3.5" />
              </>
            ) : (
              <>
                <span>Show {cluster.duplicates.length} duplicate discussions</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      )}

      {/* Expanded Duplicates List with Left Connective Line */}
      <AnimatePresence>
        {isExpanded && hasDuplicates && (
          <motion.div
            initial={{ height: 0, opacity: 0, y: -10 }}
            animate={{ height: 'auto', opacity: 1, y: 0 }}
            exit={{ height: 0, opacity: 0, y: -10 }}
            transition={{ duration: 0.4, ease: [0.04, 0.62, 0.23, 0.98] }}
            className="overflow-hidden flex flex-col gap-4 pl-6 relative border-l border-dashed border-accent-cyan/30 ml-8 mt-2"
          >
            {cluster.duplicates.map((dupPost, idx) => (
              <motion.div
                key={dupPost.post_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.08 }}
                className="relative"
              >
                {/* Visual connection dot */}
                <div className="absolute -left-[30px] top-6 w-2.5 h-2.5 rounded-full bg-accent-cyan border border-black" />
                <PostCard post={dupPost} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
