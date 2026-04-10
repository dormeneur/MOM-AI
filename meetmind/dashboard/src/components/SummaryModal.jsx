export default function SummaryModal({ onClose }) {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 font-mono">
      <div className="bg-white border-2 border-gray-800 w-full max-w-2xl text-gray-800 shadow-2xl rounded-sm">
        <div className="px-6 py-4 border-b border-gray-300 bg-gray-50 flex justify-between items-center">
          <h2 className="text-lg font-bold tracking-widest uppercase">Demo Complete</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800 font-bold px-2">X</button>
        </div>
        <div className="p-6 space-y-6">
          <div className="bg-gray-100 border border-gray-400 text-gray-800 px-4 py-3 text-sm font-bold uppercase rounded-sm border-l-4 border-l-gray-800 tracking-wide">
            ✓ Success: Personalized Minutes of Meeting (MOM) have been generated and sent to all participants via SMTP.
          </div>

          <div>
            <h3 className="text-sm font-bold uppercase border-b border-gray-300 pb-2 mb-4 tracking-widest text-gray-500">Pipeline Architecture Overview</h3>
            <ul className="space-y-5 text-sm">
              <li className="border border-gray-200 p-3 bg-white rounded-sm">
                <span className="font-bold block uppercase tracking-wider mb-1">1. Intent Classification</span>
                <span className="font-bold">Model:</span> Multi-Layer Perceptron (MLP)<br/>
                <span className="font-bold">Feature Space:</span> 517-Dimensional Space (512 TF-IDF unigrams/bigrams + 5 custom linguistic heuristics like modals, imperatives, and deadlines).<br/>
                <span className="font-bold">Result:</span> ~85% Accuracy (outperforming baseline Perceptron & KNN).
              </li>
              <li className="border border-gray-200 p-3 bg-white rounded-sm">
                <span className="font-bold block uppercase tracking-wider mb-1">2. NER Task Extraction</span>
                <span className="font-bold">Model:</span> <code className="bg-gray-100 border border-gray-300 px-1 py-0.5 rounded-sm">dslim/bert-base-NER</code> (Pre-trained BERT)<br/>
                <span className="font-bold">Mechanism:</span> Transfer learning used to extract Assignee (PER) and Deadline (DATE).<br/>
                <span className="font-bold">Innovation:</span> Augmented with deterministic rule-based fallback logic to handle implicit assignments (e.g., "I will", "We should") when neural network confidence is low.
              </li>
              <li className="border border-gray-200 p-3 bg-white rounded-sm">
                <span className="font-bold block uppercase tracking-wider mb-1">3. Abstractive Summarisation</span>
                <span className="font-bold">Model:</span> <code className="bg-gray-100 border border-gray-300 px-1 py-0.5 rounded-sm">sshleifer/distilbart-cnn-12-6</code> (Distilled Seq2Seq)<br/>
                <span className="font-bold">Mechanism:</span> Lightweight CPU-viable inference using beam-search decoding.<br/>
                <span className="font-bold">Innovation:</span> Custom Two-Pass Chunking strategy handles infinite-length transcripts without exceeding the model's memory context window limits.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
