import { useRef, useEffect } from 'react'

// Consistent speaker colours - using grayscale for academic look
const SPEAKER_COLORS = [
  '#1f2937', '#374151', '#4b5563', '#6b7280',
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
  action_item: { text: 'ACTION ITEM', color: 'bg-gray-800 text-white border-gray-800 font-bold' },
  decision: { text: 'DECISION', color: 'bg-white text-gray-800 border-gray-800 font-bold' },
  topic: { text: 'TOPIC', color: 'bg-gray-100 text-gray-600 border-gray-300' },
  deadline_mention: { text: 'DEADLINE', color: 'bg-gray-700 text-white border-gray-700 font-bold uppercase' },
}

export default function TranscriptPanel({ segments }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [segments])

  return (
    <div className="bg-white rounded-sm border border-gray-300 overflow-hidden font-mono text-gray-800">
      <div className="px-5 py-4 border-b border-gray-300 flex items-center gap-2 bg-gray-50">
        <div className="w-3 h-3 bg-gray-600 rounded-full animate-pulse" />
        <h2 className="text-sm font-bold uppercase tracking-widest text-gray-700">Live Transcript</h2>
        <span className="ml-auto text-xs text-gray-600 border border-gray-300 bg-white px-2 py-0.5 font-bold rounded-sm text-gray-500">{segments.length} SEGMENTS</span>
      </div>

      <div className="h-[500px] overflow-y-auto p-4 space-y-4">
        {segments.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm uppercase font-bold tracking-widest">
            <p>Waiting for speech...</p>
          </div>
        )}

        {segments.map((seg, i) => {
          const color = getSpeakerColor(seg.speaker_label || seg.display_name)
          const badge = LABEL_BADGES[seg.label]

          return (
            <div key={i} className="flex gap-4 group">
              <div
                className="w-1 flex-shrink-0 mt-1 mb-1 rounded-full"
                style={{ backgroundColor: color }}
              />
              <div className="flex-1 min-w-0 border-b border-gray-100 pb-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-700" style={{ color }}>
                    {seg.display_name || seg.speaker_label || 'Unknown'}
                  </span>
                  {badge && (
                    <span className={`text-[10px] px-2 py-0.5 border rounded-sm uppercase tracking-widest ${badge.color}`}>
                      {badge.text}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-800 leading-relaxed font-medium">{seg.text}</p>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
