import { useState } from 'react'

export default function MeetingControls({ status, onLaunch, onStop, onFinalize, onDemo }) {
  const [meetUrl, setMeetUrl] = useState('')
  const [hostEmail, setHostEmail] = useState('')

  const handleLaunch = () => {
    if (!meetUrl.trim()) return
    onLaunch(meetUrl.trim(), hostEmail.trim() || null)
  }

  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-2xl border border-purple-900/20 p-5">
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[250px]">
          <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Meet URL</label>
          <input
            type="url"
            value={meetUrl}
            onChange={(e) => setMeetUrl(e.target.value)}
            placeholder="https://meet.google.com/abc-defg-hij"
            disabled={status === 'active' || status === 'processing'}
            className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-purple-900/30 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20 transition-all text-sm disabled:opacity-50"
          />
        </div>

        <div className="w-64">
          <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Host Email (optional)</label>
          <input
            type="email"
            value={hostEmail}
            onChange={(e) => setHostEmail(e.target.value)}
            placeholder="host@company.com"
            disabled={status === 'active' || status === 'processing'}
            className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-purple-900/30 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20 transition-all text-sm disabled:opacity-50"
          />
        </div>

        <div className="flex gap-2">
          {(status === 'idle' || status === 'complete') && (
            <>
              <button
                onClick={handleLaunch}
                disabled={!meetUrl.trim()}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-medium hover:from-purple-500 hover:to-pink-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/20 hover:shadow-purple-500/30"
              >
                🚀 Launch Bot
              </button>
              <button
                onClick={onDemo}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 text-white text-sm font-medium hover:from-emerald-500 hover:to-cyan-500 transition-all shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30"
              >
                🧪 Demo Mode
              </button>
            </>
          )}

          {status === 'active' && (
            <>
              <button
                onClick={onStop}
                className="px-6 py-2.5 rounded-xl bg-red-600/20 border border-red-500/30 text-red-300 text-sm font-medium hover:bg-red-600/30 transition-all"
              >
                ⏹ Stop Bot
              </button>
              <button
                onClick={onFinalize}
                className="px-6 py-2.5 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-300 text-sm font-medium hover:bg-blue-600/30 transition-all"
              >
                📋 Finalize
              </button>
            </>
          )}

          {status === 'processing' && (
            <div className="px-6 py-2.5 rounded-xl bg-amber-600/20 border border-amber-500/30 text-amber-300 text-sm font-medium flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
              Processing...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
