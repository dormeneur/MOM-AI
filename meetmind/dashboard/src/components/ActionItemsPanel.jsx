export default function ActionItemsPanel({ actionItems }) {
  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-2xl border border-purple-900/20 overflow-hidden">
      <div className="px-5 py-4 border-b border-purple-900/20 flex items-center gap-2">
        <span className="text-base">📌</span>
        <h2 className="text-sm font-semibold text-purple-200 uppercase tracking-wider">Action Items</h2>
        <span className="ml-auto bg-purple-500/20 text-purple-300 text-xs px-2 py-0.5 rounded-full">
          {actionItems.length}
        </span>
      </div>

      <div className="max-h-[300px] overflow-y-auto p-4 space-y-3">
        {actionItems.length === 0 && (
          <p className="text-gray-600 text-sm text-center py-6">No action items yet</p>
        )}

        {actionItems.map((item, i) => {
          const urgency = item.deadline ? 'border-l-red-400' : 'border-l-purple-500'

          return (
            <div
              key={i}
              className={`border-l-2 ${urgency} bg-white/5 rounded-r-lg px-3 py-2.5 hover:bg-white/10 transition-colors`}
            >
              <p className="text-sm text-gray-200 leading-snug">{item.task_description}</p>
              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                {item.assigned_to_name && (
                  <span className="flex items-center gap-1">
                    <span className="w-4 h-4 rounded-full bg-purple-500/30 flex items-center justify-center text-[10px] text-purple-300">
                      {item.assigned_to_name.charAt(0).toUpperCase()}
                    </span>
                    {item.assigned_to_name}
                  </span>
                )}
                {item.deadline && (
                  <span className="text-amber-400">📅 {item.deadline}</span>
                )}
                {item.confidence != null && (
                  <span className="ml-auto text-gray-600">
                    {(item.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
