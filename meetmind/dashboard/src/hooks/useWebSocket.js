import { useState, useEffect } from 'react'

export function useWebSocket(sessionId) {
  const [segments, setSegments] = useState([])
  const [actionItems, setActionItems] = useState([])

  useEffect(() => {
    if (!sessionId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//localhost:8001/ws/sessions/${sessionId}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'segment') {
          setSegments(prev => [...prev, msg.data])
        } else if (msg.type === 'action_item') {
          setActionItems(prev => [...prev, msg.data])
        } else if (msg.type === 'finalized') {
          console.log('Meeting finalized:', msg.data)
        }
      } catch (e) {
        console.error('WebSocket parse error:', e)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
    }

    // Ping every 30s to keep alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [sessionId])

  return { segments, actionItems }
}
