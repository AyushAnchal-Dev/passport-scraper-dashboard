const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export interface FilterParams {
  platform?: string;
  category?: string;
  language?: string;
  sentiment?: string;
  region?: string;
  author?: string;
  search?: string;
  sort_by?: string;
  clustered?: boolean;
}

export async function fetchPosts(filters: FilterParams = {}) {
  const query = new URLSearchParams()
  
  Object.entries(filters).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') {
      query.append(key, String(val))
    }
  })

  const response = await fetch(`${API_URL}/api/posts?${query.toString()}`)
  if (!response.ok) {
    throw new Error('Failed to fetch posts')
  }
  return response.json()
}

export async function fetchStats() {
  const response = await fetch(`${API_URL}/api/stats`)
  if (!response.ok) {
    throw new Error('Failed to fetch statistics')
  }
  return response.json()
}

export async function translatePost(postId: string, targetLanguage: string) {
  const response = await fetch(`${API_URL}/api/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      post_id: postId,
      target_language: targetLanguage,
    }),
  })
  
  if (!response.ok) {
    throw new Error('Translation failed')
  }
  return response.json()
}

export function getWebSocketUri(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return `${process.env.NEXT_PUBLIC_WS_URL}/api/ws`
  }
  if (process.env.NEXT_PUBLIC_API_URL) {
    const url = process.env.NEXT_PUBLIC_API_URL
    const protocol = url.startsWith('https') ? 'wss:' : 'ws:'
    const host = url.replace(/^https?:\/\//, '')
    return `${protocol}//${host}/api/ws`
  }
  if (typeof window !== 'undefined') {
    const isHttps = window.location.protocol === 'https:'
    const protocol = isHttps ? 'wss:' : 'ws:'
    const host = window.location.host.split(':')[0]
    return `${protocol}//${host}:8000/api/ws`
  }
  return `${WS_URL}/api/ws`
}
