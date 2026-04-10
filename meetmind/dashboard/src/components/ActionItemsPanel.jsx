export default function ActionItemsPanel({ actionItems }) {
  return (
    <div className="bg-white rounded-sm border border-gray-300 overflow-hidden font-mono text-gray-800">
      <div className="px-5 py-4 border-b border-gray-300 flex items-center gap-2 bg-gray-50">
        <h2 className="text-sm font-bold uppercase tracking-widest text-gray-700">Action Items</h2>
        <span className="ml-auto bg-gray-200 text-gray-700 text-xs px-2 py-0.5 border border-gray-300">
          {actionItems.length}
        </span>
      </div>

      <div className="max-h-[300px] overflow-y-auto p-4 space-y-3">
        {actionItems.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-6 uppercase font-bold">No action items yet</p>
        )}

        {actionItems.map((item, i) => {
          const urgency = item.deadline ? 'border-gray-700' : 'border-gray-300'

          return (
            <div
              key={i}
              className={`border-l-4 ${urgency} bg-white border border-gray-200 rounded-sm px-3 py-2.5 hover:bg-gray-50 transition-colors`}
            >
              <p className="text-sm text-gray-800 leading-snug font-medium">{item.task_description}</p>
              <div className="flex items-center gap-3 mt-2 text-xs text-gray-600 font-bold uppercase tracking-wide">
                {item.assigned_to_name && (
                  <span className="flex items-center gap-1">
                    <span className="w-5 h-5 flex items-center justify-center text-[10px] text-white bg-gray-600 rounded-full uppercase">
                      {item.assigned_to_name.charAt(0)}
                    </span>
                    {item.assigned_to_name}
                  </span>
                )}
                {item.deadline && (
                  <span className="text-gray-700 border border-gray-300 px-1.5 py-0.5 rounded-sm">DUE: {item.deadline}</span>
                )}
                {item.confidence != null && (
                  <span className="ml-auto text-gray-500 tracking-widest">
                    CONFIDENCE: {(item.confidence * 100).toFixed(0)}%
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
