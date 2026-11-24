import React from 'react';
import { 
  MessageSquare, 
  Network, 
  Table, 
  GraduationCap, 
  Plus, 
  PanelLeftClose, 
  PanelLeftOpen, 
  FileText, 
  Layers,
  Sparkles
} from 'lucide-react';

export default function Sidebar({ 
  currentTab, 
  setCurrentTab, 
  isOpen, 
  setIsOpen, 
  stats, 
  onNewSession, 
  onLoadSamples,
  isLoading
}) {
  const navItems = [
    { id: 'chat', label: 'CHAT', icon: MessageSquare, activeColor: 'bg-[#FFD166]', hoverBorder: 'hover:border-[#FFD166]' },
    { id: 'graph', label: 'KNOWLEDGE GRAPH', icon: Network, activeColor: 'bg-[#06D6A0]', hoverBorder: 'hover:border-[#06D6A0]' },
    { id: 'matrix', label: 'COMPARISON MATRIX', icon: Table, activeColor: 'bg-[#FF9F1C]', hoverBorder: 'hover:border-[#FF9F1C]' },
    { id: 'quiz', label: 'STUDY QUIZ', icon: GraduationCap, activeColor: 'bg-[#C77DFF]', hoverBorder: 'hover:border-[#C77DFF]' },
  ];

  if (!isOpen) {
    return (
      <div className="bg-white border-r-2 border-black w-14 flex flex-col items-center py-4 justify-between h-full z-20 shrink-0">
        <button
          onClick={() => setIsOpen(true)}
          className="p-2 border-2 border-black bg-white hover:bg-[#FFD166] shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-transform"
          title="Expand Sidebar"
        >
          <PanelLeftOpen size={18} strokeWidth={2} />
        </button>

        <div className="flex flex-col gap-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`p-2.5 border-2 border-black transition-all ${
                  isActive 
                    ? `${item.activeColor} shadow-[3px_3px_0px_0px_#000]` 
                    : 'bg-white hover:bg-canvas'
                }`}
                title={item.label}
              >
                <Icon size={18} strokeWidth={2} />
              </button>
            );
          })}
        </div>

        <button
          onClick={onNewSession}
          disabled={isLoading}
          className="p-2 border-2 border-black bg-[#FF5A5F] text-white shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-transform"
          title="New Session"
        >
          <Plus size={18} strokeWidth={2} />
        </button>
      </div>
    );
  }

  return (
    <aside className="w-64 bg-white border-r-2 border-black flex flex-col justify-between h-full z-20 select-none shrink-0 shadow-[2px_0px_0px_0px_#000]">
      {/* Top Header */}
      <div>
        <div className="p-3.5 bg-[#00A896] text-white border-b-2 border-black flex items-center justify-between shadow-[0px_2px_0px_0px_#000]">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-[#FFD166] border-2 border-black flex items-center justify-center font-bold text-[10px] text-black">
              G
            </div>
            <span className="font-heading font-black text-sm tracking-wider text-black">GRAPHRAG</span>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 border-2 border-black bg-white text-black hover:bg-[#FFD166] active:translate-x-0.5 active:translate-y-0.5 transition-transform"
            title="Collapse Sidebar"
          >
            <PanelLeftClose size={15} strokeWidth={2} />
          </button>
        </div>

        {/* New Session Action */}
        <div className="p-3 border-b-2 border-black bg-[#F4F1EA]">
          <button
            onClick={onNewSession}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 bg-[#FF5A5F] hover:bg-[#E03A3E] text-white border-2 border-black font-heading font-bold py-2.5 px-3 text-xs tracking-wider shadow-[3px_3px_0px_0px_#000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all disabled:opacity-50"
          >
            <Plus size={16} strokeWidth={2} />
            <span>+ NEW SESSION</span>
          </button>
        </div>

        {/* Workspace Navigation */}
        <nav className="p-3 flex flex-col gap-2.5 border-b-2 border-black">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-[10px] font-mono uppercase text-black font-extrabold tracking-wider">
              WORKSPACE NAVIGATION
            </span>
            <span className="w-2 h-2 bg-[#00A896] border border-black inline-block"></span>
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex items-center gap-3 w-full px-3 py-2.5 text-xs font-heading font-bold border-2 border-black text-left transition-all ${
                  isActive
                    ? `${item.activeColor} shadow-[3px_3px_0px_0px_#000] translate-x-[-1px] translate-y-[-1px] text-black`
                    : 'bg-white text-black hover:bg-canvas hover:translate-x-0.5'
                }`}
              >
                <div className={`p-1 border border-black ${isActive ? 'bg-black text-white' : 'bg-canvas text-black'}`}>
                  <Icon size={14} strokeWidth={2} />
                </div>
                <span className="tracking-wide">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Uploaded Sources Section */}
        <div className="p-3 overflow-y-auto max-h-56">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono uppercase text-black font-extrabold tracking-wider">
              SOURCES ({stats.papers.length})
            </span>
            <button
              onClick={onLoadSamples}
              disabled={isLoading}
              className="text-[10px] font-mono font-bold bg-[#06D6A0] hover:bg-[#05b88a] border-2 border-black px-2 py-0.5 text-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50"
              title="Load 3 benchmark research papers"
            >
              + LOAD SAMPLES
            </button>
          </div>

          {stats.papers.length === 0 ? (
            <div className="p-3 border-2 border-dashed border-black bg-canvas text-center">
              <span className="text-[11px] font-mono text-gray-700 block mb-1.5 font-bold">
                NO PAPERS LOADED
              </span>
              <button
                onClick={onLoadSamples}
                disabled={isLoading}
                className="text-[10px] font-mono font-bold bg-[#06D6A0] hover:bg-[#05b88a] text-black border-2 border-black px-2 py-1.5 shadow-[2px_2px_0px_0px_#000] block w-full active:translate-x-0.5 active:translate-y-0.5"
              >
                LOAD 3 BENCHMARKS
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-1.5">
              {stats.papers.map((p, idx) => {
                const badgeColors = ['bg-[#D8F3DC]', 'bg-[#FFE5D9]', 'bg-[#E0AAFF]', 'bg-[#FEF08A]'];
                return (
                  <div
                    key={idx}
                    className={`flex items-center gap-2 p-1.5 border-2 border-black ${badgeColors[idx % badgeColors.length]} text-[11px] font-mono truncate shadow-[2px_2px_0px_0px_#000]`}
                    title={p}
                  >
                    <FileText size={13} strokeWidth={2} className="shrink-0 text-black" />
                    <span className="truncate font-bold text-black">{p}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Monospace Status Footer */}
      <div className="p-3 border-t-2 border-black bg-[#FEF08A] font-mono text-[10px] flex flex-col gap-1.5 text-black font-bold shadow-[0px_-2px_0px_0px_#000]">
        <div className="flex justify-between items-center">
          <span className="bg-white border border-black px-1.5 py-0.5">PAPERS: {stats.papers.length}</span>
          <span className="bg-[#A0C4FF] border border-black px-1.5 py-0.5">PAGES: {stats.total_pages}</span>
        </div>
        <div className="flex justify-between items-center border-t border-black pt-1">
          <span className="bg-[#06D6A0] border border-black px-1.5 py-0.5">NODES: {stats.nodes_count}</span>
          <span className="bg-[#FF9F1C] border border-black px-1.5 py-0.5">EDGES: {stats.edges_count}</span>
        </div>
      </div>
    </aside>
  );
}
