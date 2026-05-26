'use client'

import React from 'react'

interface ChartData {
  name: string
  count: number
}

interface AnalyticsChartsProps {
  categories: ChartData[]
  platforms: ChartData[]
}

const ACCENT_COLORS = ['#8b5cf6', '#06b6d4', '#ec4899', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#a855f7']

export default function AnalyticsCharts({ categories, platforms }: AnalyticsChartsProps) {
  
  // Category Donut Chart Math
  const totalCategoryCount = categories.reduce((sum, item) => sum + item.count, 0)
  
  // Platform Bar Chart Math
  const maxPlatformCount = platforms.reduce((max, item) => Math.max(max, item.count), 1)

  // Circular donut helpers
  let accumulatedPercentage = 0
  const radius = 50
  const strokeWidth = 14
  const circumference = 2 * Math.PI * radius

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mb-6">
      
      {/* Category Donut Chart */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col items-center">
        <h3 className="text-sm font-bold tracking-wider text-white/70 uppercase mb-6 self-start">
          Topical Categories
        </h3>
        
        {totalCategoryCount === 0 ? (
          <div className="h-48 flex items-center justify-center text-sm text-white/40 italic">
            No categorization data available
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row items-center gap-6 w-full justify-around">
            {/* SVG Donut */}
            <div className="relative w-40 h-40">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 140 140">
                <circle
                  cx="70"
                  cy="70"
                  r={radius}
                  fill="transparent"
                  stroke="rgba(255,255,255,0.03)"
                  strokeWidth={strokeWidth}
                />
                {categories.map((item, index) => {
                  const percentage = (item.count / totalCategoryCount) * 100
                  const strokeLength = (percentage / 100) * circumference
                  const strokeOffset = circumference - strokeLength + (accumulatedPercentage / 100) * circumference
                  accumulatedPercentage -= percentage
                  
                  const color = ACCENT_COLORS[index % ACCENT_COLORS.length]

                  return (
                    <circle
                      key={item.name}
                      cx="70"
                      cy="70"
                      r={radius}
                      fill="transparent"
                      stroke={color}
                      strokeWidth={strokeWidth}
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeOffset}
                      strokeLinecap="round"
                      className="transition-all duration-1000 ease-out hover:opacity-80 cursor-pointer"
                      style={{
                        filter: `drop-shadow(0 0 4px ${color}80)`
                      }}
                    >
                      <title>{`${item.name}: ${item.count} posts (${percentage.toFixed(1)}%)`}</title>
                    </circle>
                  )
                })}
              </svg>
              {/* Inner Center Label */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-black text-white">{totalCategoryCount}</span>
                <span className="text-[10px] uppercase tracking-wider text-white/50">Total Posts</span>
              </div>
            </div>

            {/* Donut Legend */}
            <div className="flex flex-col gap-2 max-h-44 overflow-y-auto w-full sm:w-auto pr-2">
              {categories.slice(0, 5).map((item, index) => {
                const color = ACCENT_COLORS[index % ACCENT_COLORS.length]
                const percentage = ((item.count / totalCategoryCount) * 100).toFixed(0)
                
                return (
                  <div key={item.name} className="flex items-center justify-between gap-4 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                      <span className="text-white/70 font-medium truncate max-w-[120px]">{item.name}</span>
                    </div>
                    <span className="text-white/40 font-bold">{percentage}%</span>
                  </div>
                )
              })}
              {categories.length > 5 && (
                <span className="text-[10px] text-white/30 italic text-center">
                  + {categories.length - 5} more categories
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Platform Shares Bar Chart */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col">
        <h3 className="text-sm font-bold tracking-wider text-white/70 uppercase mb-6">
          Platform Shares
        </h3>
        
        {platforms.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-sm text-white/40 italic">
            No platform metric data available
          </div>
        ) : (
          <div className="flex flex-col gap-4 justify-center flex-1">
            {platforms.map((item, index) => {
              const percentage = (item.count / maxPlatformCount) * 100
              const color = ACCENT_COLORS[(index + 1) % ACCENT_COLORS.length]

              return (
                <div key={item.name} className="flex flex-col gap-1.5 w-full">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="capitalize text-white/70">{item.name}</span>
                    <span className="text-white/40">{item.count} posts</span>
                  </div>
                  
                  {/* Progress Container */}
                  <div className="h-2.5 w-full rounded-full bg-white/5 border border-white/5 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-out"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: color,
                        boxShadow: `0 0 10px ${color}80`
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

    </div>
  )
}
