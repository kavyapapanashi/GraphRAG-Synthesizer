import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Send, 
  Plus, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  Loader2, 
  Layers, 
  AlertCircle,
  Sparkles
} from 'lucide-react';

export default function ChatView({ 
  messages, 
  onSendMessage, 
  onFileUpload, 
  isLoading, 
  isUploading, 
  uploadProgress,
  stats,
  onNavigateTab
}) {
  const [input, setInput] = useState('');
  const [expandedTriples, setExpandedTriples] = useState({});
  const [expandedChunks, setExpandedChunks] = useState({});
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const suggestionCards = [
    {
      tag: "METHODOLOGY",
      tagColor: "bg-[#2D6A4F] text-white",
      title: "Compare methodologies across uploaded papers",
      desc: "Analyze architectural trade-offs between dual-encoders and knowledge graphs",
      bg: "bg-[#D8F3DC] hover:bg-[#B7E4C7]",
    },
    {
      tag: "LIMITATIONS",
      tagColor: "bg-[#C94A4A] text-white",
      title: "Extract shared limitations and computational bottlenecks",
      desc: "Surface memory overhead, latency ceilings, and context length boundaries",
      bg: "bg-[#FFE5D9] hover:bg-[#F8B4A4]",
    },
    {
      tag: "BENCHMARKS",
      tagColor: "bg-[#B45309] text-white",
      title: "Which architecture achieves highest Recall on benchmarks?",
      desc: "Synthesize quantitative Recall@10, MRR@10, and F1-score comparisons",
      bg: "bg-[#FEF08A] hover:bg-[#FDE047]",
    },
    {
      tag: "CONTRADICTIONS",
      tagColor: "bg-[#7B2CBF] text-white",
      title: "Identify empirical contradictions or outperformance claims",
      desc: "Highlight where methods contradict previous findings or surpass baselines",
      bg: "bg-[#E0AAFF] hover:bg-[#D08CFF]",
    }
  ];

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files);
      e.target.value = null; // reset
    }
  };

  const toggleTriples = (idx) => {
    setExpandedTriples(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const toggleChunks = (idx) => {
    setExpandedChunks(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const renderMessageContent = (text) => {
    const parts = [];
    const citationRegex = /\[([^\[\]]+,\s*p\.\s*\d+)\]/g;
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      parts.push(
        `<span class="inline-block bg-[#FFD166] text-black border-2 border-black px-2 py-0.5 text-[11px] font-mono font-bold mx-0.5 shadow-[2px_2px_0px_0px_#000] select-all">${match[0]}</span>`
      );
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    const processedHtml = parts.join('');

    return (
      <div 
        className="prose prose-sm max-w-none text-black font-sans leading-relaxed space-y-3"
        dangerouslySetInnerHTML={{ __html: processedHtml.replace(/\n/g, '<br/>') }}
      />
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-canvas">
      {/* Scrollable Conversation Canvas */}
      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-3xl mx-auto w-full">
          {messages.length === 0 ? (
            /* Empty State */
            <div className="py-8 flex flex-col items-center justify-center text-center">
              <div className="w-14 h-14 bg-[#F4D35E] border-2 border-black flex items-center justify-center mb-5 shadow-[4px_4px_0px_0px_#000]">
                <Layers size={28} strokeWidth={2} className="text-black" />
              </div>
              
              <h2 className="font-heading font-bold text-2xl tracking-tight text-black mb-2">
                WHAT ARE WE RESEARCHING TODAY?
              </h2>
              <p className="font-mono text-xs text-gray-700 mb-8 max-w-md font-medium">
                Hybrid GraphRAG workspace combining Knowledge Graph traversals with ChromaDB semantic search and strict inline citations.
              </p>

              {/* Colorful Neobrutalist Suggestion Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-xl text-left">
                {suggestionCards.map((card, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSendMessage(card.title)}
                    className={`p-4 border-2 border-black shadow-[4px_4px_0px_0px_#000] ${card.bg} active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all flex flex-col justify-between text-left`}
                  >
                    <div>
                      <span className={`inline-block px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase mb-2 border border-black shadow-[1px_1px_0px_0px_#000] ${card.tagColor}`}>
                        {card.tag}
                      </span>
                      <span className="font-heading font-black text-xs text-black block mb-1 leading-snug">
                        {card.title}
                      </span>
                      <span className="text-[11px] font-sans text-gray-900 block leading-tight">
                        {card.desc}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-black font-extrabold mt-3.5 block flex items-center gap-1">
                      <span>&rarr; RUN GROUNDED QUERY</span>
                    </span>
                  </button>
                ))}
              </div>

              {stats.papers.length === 0 && (
                <div className="mt-8 p-3.5 border-2 border-black bg-[#FFFBEB] shadow-[3px_3px_0px_0px_#000] max-w-md flex items-center gap-3 text-left">
                  <AlertCircle size={22} strokeWidth={2} className="text-[#C94A4A] shrink-0" />
                  <span className="text-xs font-mono font-medium text-black">
                    No papers loaded yet. Click <b>+ LOAD SAMPLES</b> in the sidebar or upload your research PDFs below!
                  </span>
                </div>
              )}
            </div>
          ) : (
            /* Conversation Thread */
            <div className="space-y-6 pb-4">
              {messages.map((msg, idx) => (
                <div key={idx} className="flex flex-col">
                  {msg.role === 'user' ? (
                    /* User Message */
                    <div className="self-end max-w-xl">
                      <div className="bg-[#00A896] text-white border-2 border-black shadow-[4px_4px_0px_0px_#000] p-4 text-sm font-medium">
                        {msg.content}
                      </div>
                      <span className="font-mono text-[10px] text-gray-700 mt-1 block text-right font-bold">
                        YOU
                      </span>
                    </div>
                  ) : (
                    /* AI Response */
                    <div className="w-full">
                      <div className="bg-white border-2 border-black shadow-[5px_5px_0px_0px_#000] overflow-hidden">
                        {/* Header Banner */}
                        <div className="bg-[#00A896] text-white border-b-2 border-black p-3 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3.5 h-3.5 bg-[#FFD166] border-2 border-black"></div>
                            <span className="font-heading font-bold text-xs tracking-wider text-black">
                              GROUNDED RESEARCH SYNTHESIS
                            </span>
                          </div>
                          {msg.citations && msg.citations.length > 0 && (
                            <span className="text-[10px] font-mono bg-[#FFD166] text-black border border-black px-2 py-0.5 font-bold shadow-[1px_1px_0px_0px_#000]">
                              {msg.citations.length} VERIFIED CITATIONS
                            </span>
                          )}
                        </div>

                        {/* Content Area */}
                        <div className="p-6 text-black">
                          {renderMessageContent(msg.content)}

                          {/* Citation Badges Footer */}
                          {msg.citations && msg.citations.length > 0 && (
                            <div className="mt-5 pt-4 border-t-2 border-black">
                              <span className="text-[10px] font-mono uppercase text-gray-700 block mb-1.5 font-bold">
                                EXACT SOURCE CITATIONS:
                              </span>
                              <div className="flex flex-wrap gap-2">
                                {msg.citations.map((c, cIdx) => (
                                  <span
                                    key={cIdx}
                                    className="text-[11px] font-mono bg-[#FFD166] text-black border-2 border-black px-2 py-0.5 font-bold shadow-[2px_2px_0px_0px_#000]"
                                  >
                                    {c}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Retrieved Graph Paths Drawer */}
                          {msg.triples && msg.triples.length > 0 && (
                            <div className="mt-4 pt-3 border-t-2 border-black">
                              <div className="flex items-center justify-between gap-2 mb-1.5">
                                <button
                                  onClick={() => toggleTriples(idx)}
                                  className="flex-1 flex items-center justify-between text-xs font-mono font-bold bg-[#D8F3DC] border-2 border-black p-2 hover:bg-[#B7E4C7] shadow-[2px_2px_0px_0px_#000]"
                                >
                                  <div className="flex items-center gap-2">
                                    <span className="w-2.5 h-2.5 bg-[#00A896] border border-black inline-block"></span>
                                    <span>RETRIEVED KNOWLEDGE GRAPH ({msg.triples.length} RELATIONAL TRIPLES)</span>
                                  </div>
                                  {expandedTriples[idx] === false ? (
                                    <ChevronDown size={16} strokeWidth={2} />
                                  ) : (
                                    <ChevronUp size={16} strokeWidth={2} />
                                  )}
                                </button>
                                {onNavigateTab && (
                                  <button
                                    onClick={() => onNavigateTab('graph')}
                                    className="bg-[#06D6A0] hover:bg-[#05b88a] text-black border-2 border-black px-2.5 py-2 text-[10px] font-mono font-bold shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 whitespace-nowrap"
                                    title="Open interactive NetworkX canvas"
                                  >
                                    EXPLORE IN GRAPH &rarr;
                                  </button>
                                )}
                              </div>

                              {expandedTriples[idx] !== false && (
                                <div className="mt-2 bg-canvas border-2 border-black p-3 space-y-2 text-xs font-mono max-h-56 overflow-y-auto">
                                  {msg.triples.map((t, tIdx) => (
                                    <div key={tIdx} className="border-b border-gray-300 pb-1.5 flex flex-wrap items-center gap-1.5">
                                      <span className="font-bold text-black bg-white px-1.5 py-0.5 border border-black">{t.source}</span>
                                      <span className="text-[#00A896] font-bold">&rarr; {t.relation} &rarr;</span>
                                      <span className="font-bold text-black bg-white px-1.5 py-0.5 border border-black">{t.target}</span>
                                      {t.details && <span className="text-gray-700 ml-1">({t.details})</span>}
                                      <span className="ml-auto bg-[#FFD166] border border-black px-1.5 py-0.5 text-[10px] font-bold">
                                        {t.citation}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Retrieved Chroma Chunks Drawer */}
                          {msg.chunks && msg.chunks.length > 0 && (
                            <div className="mt-2 pt-1">
                              <button
                                onClick={() => toggleChunks(idx)}
                                className="flex items-center justify-between w-full text-xs font-mono font-bold bg-[#E0F7FA] border-2 border-black p-2 hover:bg-[#B2EBF2] shadow-[2px_2px_0px_0px_#000]"
                              >
                                <span>VIEW RAW TEXT EVIDENCE ({msg.chunks.length} PASSAGES)</span>
                                {expandedChunks[idx] ? (
                                  <ChevronUp size={16} strokeWidth={2} />
                                ) : (
                                  <ChevronDown size={16} strokeWidth={2} />
                                )}
                              </button>

                              {expandedChunks[idx] && (
                                <div className="mt-2 bg-canvas border-2 border-black p-3 space-y-2 text-xs font-mono max-h-56 overflow-y-auto">
                                  {msg.chunks.map((c, cIdx) => (
                                    <div key={cIdx} className="border-b border-gray-300 pb-2">
                                      <div className="flex justify-between font-bold text-[10px] mb-1">
                                        <span className="bg-black text-white px-1.5 py-0.5">{c.citation}</span>
                                        <span className="font-mono text-gray-700">DIST: {c.distance ? c.distance.toFixed(3) : '0.000'}</span>
                                      </div>
                                      <p className="text-gray-900 italic font-sans text-xs bg-white p-2 border border-black">"{c.text}"</p>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                      <span className="font-mono text-[10px] text-gray-700 mt-1 block font-bold">
                        SYNTHESIZER (GRAPHRAG + GEMINI 2.5 FLASH)
                      </span>
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="bg-[#FEF08A] border-2 border-black shadow-[4px_4px_0px_0px_#000] p-4 flex items-center gap-3">
                  <Loader2 size={18} strokeWidth={2} className="animate-spin text-black" />
                  <span className="font-mono text-xs font-bold text-black">
                    TRAVERSING 1-2 HOP KNOWLEDGE GRAPH & SYNTHESIZING GROUNDED ANSWER...
                  </span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Docked Bottom Prompt Bar */}
      <div className="px-4 pb-6 pt-2 shrink-0">
        <div className="max-w-3xl mx-auto w-full">
          {isUploading && (
            <div className="mb-2 p-2.5 bg-[#FEF08A] border-2 border-black shadow-[3px_3px_0px_0px_#000] flex items-center justify-between text-xs font-mono">
              <span className="font-bold flex items-center gap-2 text-black">
                <Loader2 size={15} className="animate-spin text-black" />
                INDEXING PDF CHUNKS & EXTRACTING TRIPLES...
              </span>
              <span className="font-bold text-black bg-white border border-black px-2 py-0.5">{uploadProgress || 'IN PROGRESS'}</span>
            </div>
          )}

          <div className="bg-white border-2 border-black shadow-[5px_5px_0px_0px_#000] flex items-center p-2.5 gap-2.5">
            {/* Attach PDF button in vibrant Sunny Ochre */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              multiple
              accept=".pdf"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isLoading}
              className="w-10 h-10 border-2 border-black bg-[#FFD166] hover:bg-[#F4C430] active:translate-x-0.5 active:translate-y-0.5 shadow-[2px_2px_0px_0px_#000] flex items-center justify-center transition-all disabled:opacity-50 shrink-0"
              title="Upload 1–5 Academic PDFs"
            >
              <Plus size={20} strokeWidth={2} />
            </button>

            {/* Prompt Input */}
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder={
                stats.papers.length === 0
                  ? "Load or upload papers first to query..."
                  : "Ask across your uploaded papers (e.g. compare limitations)..."
              }
              className="flex-1 bg-transparent px-3 py-2 text-sm font-sans focus:outline-none placeholder-gray-500 font-medium"
            />

            {stats.papers.length > 0 && (
              <span className="hidden sm:inline-block bg-[#D8F3DC] text-[#006644] border border-black px-2 py-0.5 text-[10px] font-mono font-bold shrink-0 shadow-[1px_1px_0px_0px_#000]">
                {stats.papers.length} PAPERS INDEXED
              </span>
            )}

            {/* Send Button in Electric Teal */}
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="bg-[#00A896] hover:bg-[#029685] text-white border-2 border-black font-heading font-bold px-5 py-2 text-xs tracking-wider shadow-[3px_3px_0px_0px_#000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 shrink-0"
            >
              <span>SEND</span>
              <Send size={13} strokeWidth={2} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
