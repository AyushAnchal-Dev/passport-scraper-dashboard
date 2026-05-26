'use client'

import React from 'react'

interface WordCloudProps {
  words: Record<string, number>
  onWordClick: (word: string) => void
  activeSearch: string
}

const ACCENT_COLORS = [
  'text-accent-purple hover:bg-accent-purple/10 border-accent-purple/20',
  'text-accent-cyan hover:bg-accent-cyan/10 border-accent-cyan/20',
  'text-accent-pink hover:bg-accent-pink/10 border-accent-pink/20',
  'text-accent-green hover:bg-accent-green/10 border-accent-green/20',
  'text-accent-yellow hover:bg-accent-yellow/10 border-accent-yellow/20',
]

export default function WordCloud({ words, onWordClick, activeSearch }: WordCloudProps) {
  const wordEntries = Object.entries(words)

  if (wordEntries.length === 0) {
    return (
      <div className="text-sm text-white/40 italic text-center py-4">
        No keywords extracted yet.
      </div>
    )
  }

  // Find max/min counts to normalize font size mapping
  const counts = wordEntries.map(([_, count]) => count)
  const maxCount = Math.max(...counts)
  const minCount = Math.min(...counts)

  const getFontSize = (count: number) => {
    if (maxCount === minCount) return 'text-sm'
    
    // Scale count between 0 and 4
    const scale = (count - minCount) / (maxCount - minCount)
    if (scale > 0.8) return 'text-xl md:text-2xl font-bold'
    if (scale > 0.5) return 'text-lg md:text-xl font-semibold'
    if (scale > 0.2) return 'text-sm md:text-md font-medium'
    return 'text-xs md:text-sm text-white/70'
  }

  return (
    <div className="flex flex-wrap gap-2 items-center justify-center p-4 border border-white/5 rounded-2xl bg-white/5 backdrop-blur-md">
      {wordEntries.map(([word, count], index) => {
        const colorClass = ACCENT_COLORS[index % ACCENT_COLORS.length]
        const sizeClass = getFontSize(count)
        const isActive = activeSearch.toLowerCase() === word.toLowerCase()

        return (
          <button
            key={word}
            onClick={() => onWordClick(isActive ? '' : word)}
            className={`px-3 py-1.5 rounded-xl border text-center transition-all duration-300 ${colorClass} ${sizeClass} ${
              isActive
                ? 'bg-white/20 border-white/40 text-white font-extrabold scale-110 shadow-[0_0_15px_rgba(255,255,255,0.25)]'
                : 'bg-white/5'
            }`}
          >
            <span>{word}</span>
            <span className="text-[10px] opacity-50 ml-1.5 font-normal">({count})</span>
          </button>
        )
      })}
    </div>
  )
}
