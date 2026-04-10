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
    <div className="bg-white rounded-sm border border-gray-300 overflow-hidden font-mono text-gray-800">
      <div className="px-5 py-4 border-b border-gray-300 flex items-center gap-2 bg-gray-50">
        <h2 className="text-sm font-bold uppercase tracking-widest text-gray-700">Participants</h2>
      </div>

      <div className="p-4 space-y-2">
        {participants.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-4 uppercase font-bold">No participants detected yet</p>
        )}

        {participants.map((p) => (
          <div key={p.id} className="flex items-center gap-3 bg-white border border-gray-200 rounded-sm px-3 py-2.5">
            <div className="w-8 h-8 flex items-center justify-center text-white bg-gray-600 rounded-full text-xs font-bold flex-shrink-0 uppercase">
              {p.display_name?.charAt(0)?.toUpperCase() || '?'}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-800 font-bold uppercase truncate">{p.display_name}</p>
              {p.speaker_label && (
                <p className="text-[10px] text-gray-500 uppercase border border-gray-200 inline-block rounded-sm px-1.5 mt-1">{p.speaker_label}</p>
              )}
            </div>

            {editing === p.id ? (
              <div className="flex items-center gap-1">
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && saveEmail(p.id)}
                  className="w-40 px-2 py-1 text-xs rounded-sm bg-white border border-gray-300 text-gray-800 focus:outline-none focus:border-gray-500"
                  placeholder="email@example.com"
                  autoFocus
                />
                <button
                  onClick={() => saveEmail(p.id)}
                  className="text-xs text-gray-700 border border-gray-300 rounded-sm px-2 py-1 hover:bg-gray-100 font-bold"
                >
                  SAVE
                </button>
                <button
                  onClick={() => setEditing(null)}
                  className="text-xs text-gray-700 border border-gray-300 rounded-sm px-2 py-1 hover:bg-gray-100 font-bold"
                >
                  CANCEL
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 truncate max-w-[120px]">
                  {p.email || 'No email'}
                </span>
                <button
                  onClick={() => startEdit(p)}
                  className="text-gray-700 border border-gray-300 rounded-sm px-2 py-0.5 text-xs font-bold hover:bg-gray-100 transition-colors"
                  title="Edit email"
                >
                  EDIT
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
