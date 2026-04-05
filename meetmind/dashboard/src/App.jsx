import { useState, useEffect, useRef } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import TranscriptPanel from './components/TranscriptPanel'
import ActionItemsPanel from './components/ActionItemsPanel'
import ParticipantMap from './components/ParticipantMap'
import MeetingControls from './components/MeetingControls'

const API = ''  // Uses Vite proxy (see vite.config.js)

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [status, setStatus] = useState('idle')     // idle | active | processing | complete
  const [participants, setParticipants] = useState([])
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef(null)

  const { segments, actionItems } = useWebSocket(sessionId)

  // Timer
  useEffect(() => {
    if (status === 'active') {
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
    } else {
      clearInterval(timerRef.current)
    }
    return () => clearInterval(timerRef.current)
  }, [status])

  const formatTime = (s) => {
    const m = Math.floor(s / 60).toString().padStart(2, '0')
    const sec = (s % 60).toString().padStart(2, '0')
    return `${m}:${sec}`
  }

  // Fetch participants periodically
  useEffect(() => {
    if (!sessionId) return
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API}/api/sessions/${sessionId}/participants`)
        if (res.ok) setParticipants(await res.json())
      } catch {}
    }, 5000)
    return () => clearInterval(interval)
  }, [sessionId])

  const handleLaunch = async (meetUrl, hostEmail) => {
    try {
      // Create session
      const res = await fetch(`${API}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ meet_url: meetUrl, host_email: hostEmail }),
      })
      const data = await res.json()
      const sid = data.session_id
      setSessionId(sid)
      setStatus('active')
      setElapsed(0)

      // Launch bot
      await fetch(`${API}/api/sessions/${sid}/bot/launch`, { method: 'POST' })
    } catch (e) {
      console.error('Launch failed:', e)
    }
  }

  const handleStop = async () => {
    if (!sessionId) return
    try {
      await fetch(`${API}/api/sessions/${sessionId}/bot/stop`, { method: 'POST' })
      setStatus('processing')
    } catch (e) {
      console.error('Stop failed:', e)
    }
  }

  const handleFinalize = async () => {
    if (!sessionId) return
    try {
      setStatus('processing')
      const res = await fetch(`${API}/api/sessions/${sessionId}/finalize`, { method: 'POST' })
      if (res.ok) setStatus('complete')
    } catch (e) {
      console.error('Finalize failed:', e)
    }
  }

  const handleDemo = async () => {
    try {
      setStatus('processing')
      const res = await fetch(`${API}/api/demo/start`, { method: 'POST' })
      const data = await res.json()
      setSessionId(data.session_id)
      setStatus('active')
      setElapsed(0)
    } catch (e) {
      console.error('Demo failed:', e)
      setStatus('idle')
    }
  }

  const handleUpdateEmail = async (participantId, email) => {
    if (!sessionId) return
    try {
      await fetch(`${API}/api/sessions/${sessionId}/participants/${participantId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      // Refresh
      const res = await fetch(`${API}/api/sessions/${sessionId}/participants`)
      if (res.ok) setParticipants(await res.json())
    } catch (e) {
      console.error('Update failed:', e)
    }
  }

  const statusColors = {
    idle: 'bg-gray-600',
    active: 'bg-emerald-500',
    processing: 'bg-amber-500',
    complete: 'bg-blue-500',
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f0a1a] via-[#1a1030] to-[#0f0a1a]">
      {/* Header */}
      <header className="border-b border-purple-900/30 backdrop-blur-sm bg-black/20">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-purple-500/20">
              M
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
              MeetMind
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full text-xs font-medium text-white ${statusColors[status]} shadow-sm`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
            {status === 'active' && (
              <span className="text-sm text-purple-300 font-mono">
                ⏱ {formatTime(elapsed)}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-screen-2xl mx-auto px-6 py-6">
        {/* Controls */}
        <MeetingControls
          status={status}
          onLaunch={handleLaunch}
          onStop={handleStop}
          onFinalize={handleFinalize}
          onDemo={handleDemo}
        />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Transcript (2/3 width) */}
          <div className="lg:col-span-2">
            <TranscriptPanel segments={segments} />
          </div>

          {/* Sidebar (1/3 width) */}
          <div className="space-y-6">
            <ActionItemsPanel actionItems={actionItems} />
            <ParticipantMap
              participants={participants}
              onUpdateEmail={handleUpdateEmail}
            />
          </div>
        </div>
      </main>
    </div>
  )
}
