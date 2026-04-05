import { useState } from 'react'

export default function ParticipantMap({ participants, onUpdateEmail }) {
  const [editing, setEditing] = useState(null)
  const [emailInput, setEmailInput] = useState('')

  const startEdit = (p) => {
    setEditing(p.id)
    setEmailInput(p.email || '')
  }

  const saveEmail = (participantId) => {
    if (emailInput.trim()) {
      onUpdateEmail(participantId, emailInput.trim())
    }
    setEditing(null)
    setEmailInput('')
  }

  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-2xl border border-purple-900/20 overflow-hidden">
      <div className="px-5 py-4 border-b border-purple-900/20 flex items-center gap-2">
        <span className="text-base">👥</span>
        <h2 className="text-sm font-semibold text-purple-200 uppercase tracking-wider">Participants</h2>
      </div>

      <div className="p-4 space-y-2">
        {participants.length === 0 && (
          <p className="text-gray-600 text-sm text-center py-4">No participants detected yet</p>
        )}

        {participants.map((p) => (
          <div key={p.id} className="flex items-center gap-3 bg-white/5 rounded-lg px-3 py-2.5 hover:bg-white/8 transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              {p.display_name?.charAt(0)?.toUpperCase() || '?'}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-200 font-medium truncate">{p.display_name}</p>
              {p.speaker_label && (
                <p className="text-[10px] text-gray-500">{p.speaker_label}</p>
              )}
            </div>

            {editing === p.id ? (
              <div className="flex items-center gap-1">
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && saveEmail(p.id)}
                  className="w-40 px-2 py-1 text-xs rounded bg-black/40 border border-purple-700/30 text-gray-200 focus:outline-none focus:border-purple-500"
                  placeholder="email@example.com"
                  autoFocus
                />
                <button
                  onClick={() => saveEmail(p.id)}
                  className="text-xs text-emerald-400 hover:text-emerald-300 px-1"
                >
                  ✓
                </button>
                <button
                  onClick={() => setEditing(null)}
                  className="text-xs text-gray-500 hover:text-gray-400 px-1"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500 truncate max-w-[120px]">
                  {p.email || 'No email'}
                </span>
                <button
                  onClick={() => startEdit(p)}
                  className="text-gray-600 hover:text-purple-400 transition-colors text-xs px-1"
                  title="Edit email"
                >
                  ✏️
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
