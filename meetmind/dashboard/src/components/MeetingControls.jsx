import { useState } from 'react'

export default function MeetingControls({ status, onLaunch, onStop, onFinalize, onDemo }) {
  const [meetUrl, setMeetUrl] = useState('')
  const [hostEmail, setHostEmail] = useState('')

  const handleLaunch = () => {
    if (!meetUrl.trim()) return
    onLaunch(meetUrl.trim(), hostEmail.trim() || null)
  }

  return (
    <div className="bg-white rounded-sm border border-gray-300 p-5 font-mono text-gray-800">
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[250px]">
          <label className="block text-xs text-gray-700 mb-1.5 uppercase tracking-wider font-bold">Meet URL</label>
          <input
            type="url"
            value={meetUrl}
            onChange={(e) => setMeetUrl(e.target.value)}
            placeholder="https://meet.google.com/abc-defg-hij"
            disabled={status === 'active' || status === 'processing'}
            className="w-full px-4 py-2.5 rounded-sm bg-white border border-gray-300 text-gray-800 placeholder-gray-400 focus:outline-none focus:border-gray-500 focus:ring-1 focus:ring-gray-500 transition-all text-sm disabled:opacity-50"
          />
        </div>

        <div className="w-64">
          <label className="block text-xs text-gray-700 mb-1.5 uppercase tracking-wider font-bold">Host Email (optional)</label>
          <input
            type="email"
            value={hostEmail}
            onChange={(e) => setHostEmail(e.target.value)}
            placeholder="host@company.com"
            disabled={status === 'active' || status === 'processing'}
            className="w-full px-4 py-2.5 rounded-sm bg-white border border-gray-300 text-gray-800 placeholder-gray-400 focus:outline-none focus:border-gray-500 focus:ring-1 focus:ring-gray-500 transition-all text-sm disabled:opacity-50"
          />
        </div>

        <div className="flex gap-2">
          {(status === 'idle' || status === 'complete') && (
            <>
              <button
                onClick={handleLaunch}
                disabled={!meetUrl.trim()}
                className="px-6 py-2.5 rounded-sm bg-gray-800 text-white border border-gray-800 text-sm font-bold uppercase hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-none"
              >
                Launch Bot
              </button>
              <button
                onClick={onDemo}
                className="px-6 py-2.5 rounded-sm bg-white text-gray-800 border border-gray-300 text-sm font-bold uppercase hover:bg-gray-50 transition-all shadow-none"
              >
                Demo Mode
              </button>
            </>
          )}

          {status === 'active' && (
            <>
              <button
                onClick={onStop}
                className="px-6 py-2.5 rounded-sm bg-white border border-gray-300 text-gray-800 text-sm font-bold uppercase hover:bg-gray-50 transition-all"
              >
                Stop Bot
              </button>
              <button
                onClick={onFinalize}
                className="px-6 py-2.5 rounded-sm bg-gray-800 border border-gray-800 text-white text-sm font-bold uppercase hover:bg-gray-700 transition-all"
              >
                Finalize
              </button>
            </>
          )}

          {status === 'processing' && (
            <div className="px-6 py-2.5 rounded-sm bg-white border border-gray-300 text-gray-800 text-sm font-bold uppercase flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin" />
              Processing...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
