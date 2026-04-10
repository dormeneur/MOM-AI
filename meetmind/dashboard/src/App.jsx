import { useState, useEffect, useRef } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import TranscriptPanel from './components/TranscriptPanel'
import ActionItemsPanel from './components/ActionItemsPanel'
import ParticipantMap from './components/ParticipantMap'
import MeetingControls from './components/MeetingControls'
import SummaryModal from './components/SummaryModal'

const API = ''  // Uses Vite proxy (see vite.config.js)

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [status, setStatus] = useState('idle')     // idle | active | processing | complete
  const [participants, setParticipants] = useState([])
  const [elapsed, setElapsed] = useState(0)
  const [showSummary, setShowSummary] = useState(false)
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
      if (res.ok) {
        setStatus('complete')
        setShowSummary(true)
      }
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

      // Auto-finalize demo when it ends (rough estimate or just let user click Finalize)
      // Actually, demo has a set length or user can stop. We leave it as is.
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
    idle: 'text-gray-700 border border-gray-400',
    active: 'text-gray-800 border border-gray-800 font-bold',
    processing: 'text-gray-500 border border-gray-300',
    complete: 'text-gray-700 border border-gray-400',
  }

  return (
    <div className="min-h-screen bg-[#fafaf9] text-gray-800 font-mono relative">
      {/* Header */}
      <header className="border-b border-gray-300 bg-white">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 border-2 border-gray-800 flex items-center justify-center text-gray-800 font-bold text-lg rounded-sm">
              M
            </div>
            <h1 className="text-xl font-bold tracking-widest uppercase text-gray-800">
              MeetMind
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 text-xs uppercase tracking-wider rounded-sm ${statusColors[status]}`}>
              {status}
            </span>
            {status === 'active' && (
              <span className="text-sm font-mono border border-gray-400 px-2 py-1 rounded-sm text-gray-700 bg-gray-50">
                {formatTime(elapsed)}
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

      {/* Summary Modal */}
      {showSummary && (
        <SummaryModal onClose={() => setShowSummary(false)} />
      )}
    </div>
  )
}
