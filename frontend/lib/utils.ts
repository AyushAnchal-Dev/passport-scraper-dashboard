import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string): string {
  try {
    const d = new Date(dateString)
    // Use a fixed locale + UTC timezone so SSR and CSR always produce identical output
    // (prevents Next.js hydration mismatch when server/client are in different locales)
    return d.toLocaleString('en-US', {
      timeZone: 'UTC',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
  } catch (e) {
    return dateString
  }
}

export function exportToCSV(posts: any[]) {
  const headers = ["Post ID", "Platform", "Author", "Original Content", "Summary", "Category", "Sentiment", "Likes", "Comments", "Region", "Date"]
  
  const rows = posts.map(item => [
    item.post_id,
    item.platform,
    item.author,
    item.content.replace(/"/g, '""'),
    item.summary ? item.summary.replace(/"/g, '""') : "",
    item.category || "General",
    item.sentiment || "Neutral",
    item.likes || 0,
    item.comments || 0,
    item.geolocation ? `${item.geolocation.city}, ${item.geolocation.country}` : "Global",
    item.created_at
  ])

  const csvContent = "data:text/csv;charset=utf-8," 
    + [headers.join(","), ...rows.map(e => e.map(val => `"${val}"`).join(","))].join("\n")
  
  const encodedUri = encodeURI(csvContent)
  const link = document.createElement("a")
  link.setAttribute("href", encodedUri)
  link.setAttribute("download", `passport_social_analytics_${new Date().toISOString().split('T')[0]}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export function exportToPDF() {
  // Triggers browser print-to-PDF. 
  // Combined with custom print styles in globals/pages, this generates an optimized PDF report.
  window.print()
}
