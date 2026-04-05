import { useRef, useEffect } from 'react'

// Consistent speaker colours
const SPEAKER_COLORS = [
  '#8b5cf6', '#ec4899', '#06b6d4', '#f59e0b',
  '#10b981', '#ef4444', '#3b82f6', '#f97316',
]
const speakerColorMap = {}
let colorIndex = 0

function getSpeakerColor(speaker) {
  if (!speakerColorMap[speaker]) {
    speakerColorMap[speaker] = SPEAKER_COLORS[colorIndex % SPEAKER_COLORS.length]
    colorIndex++
  }
  return speakerColorMap[speaker]
}

const LABEL_BADGES = {
  action_item: { text: 'Action', color: 'bg-red-500/20 text-red-300 border-red-500/30' },
  decision: { text: 'Decision', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  topic: { text: 'Topic', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  deadline_mention: { text: 'Deadline', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
}

export default function TranscriptPanel({ segments }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [segments])

  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-2xl border border-purple-900/20 overflow-hidden">
      <div className="px-5 py-4 border-b border-purple-900/20 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <h2 className="text-sm font-semibold text-purple-200 uppercase tracking-wider">Live Transcript</h2>
        <span className="ml-auto text-xs text-gray-500">{segments.length} segments</span>
      </div>

      <div className="h-[500px] overflow-y-auto p-4 space-y-3">
        {segments.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-600 text-sm">
            <p>Waiting for speech...</p>
          </div>
        )}

        {segments.map((seg, i) => {
          const color = getSpeakerColor(seg.speaker_label || seg.display_name)
          const badge = LABEL_BADGES[seg.label]

          return (
            <div key={i} className="flex gap-3 group">
              <div
                className="w-1 rounded-full flex-shrink-0 mt-1 mb-1"
                style={{ backgroundColor: color }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold" style={{ color }}>
                    {seg.display_name || seg.speaker_label || 'Unknown'}
                  </span>
                  {badge && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${badge.color}`}>
                      {badge.text}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">{seg.text}</p>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
