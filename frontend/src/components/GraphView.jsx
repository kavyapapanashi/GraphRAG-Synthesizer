import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network/standalone';
import { Filter, Layers, Info, RefreshCw, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { fetchGraph } from '../api';

const COLOR_MAP = {
  'Paper': { bg: '#1D3557', border: '#000000', text: '#FFFFFF', activeBg: 'bg-[#1D3557] text-white' },
  'Model/Method': { bg: '#00A896', border: '#000000', text: '#FFFFFF', activeBg: 'bg-[#00A896] text-white' },
  'Dataset': { bg: '#F4A261', border: '#000000', text: '#000000', activeBg: 'bg-[#F4A261] text-black' },
  'Metric': { bg: '#0077B6', border: '#000000', text: '#FFFFFF', activeBg: 'bg-[#0077B6] text-white' },
  'Limitation': { bg: '#C94A4A', border: '#000000', text: '#FFFFFF', activeBg: 'bg-[#C94A4A] text-white' },
};

export default function GraphView() {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], stats: {} });
  const [selectedFilter, setSelectedFilter] = useState('ALL');
  const [selectedElement, setSelectedElement] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const categories = ['ALL', 'Paper', 'Model/Method', 'Dataset', 'Metric', 'Limitation'];

  const loadGraph = async () => {
    setIsLoading(true);
    try {
      const data = await fetchGraph();
      setGraphData(data);
    } catch (err) {
      console.error("Failed to load graph:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  // Compute category counts
  const categoryCounts = categories.reduce((acc, cat) => {
    if (cat === 'ALL') {
      acc[cat] = graphData.nodes.length;
    } else {
      acc[cat] = graphData.nodes.filter(n => n.type === cat).length;
    }
    return acc;
  }, {});

  useEffect(() => {
    if (!containerRef.current || graphData.nodes.length === 0) return;

    // Filter nodes
    const filteredNodes = selectedFilter === 'ALL'
      ? graphData.nodes
      : graphData.nodes.filter(n => n.type === selectedFilter);

    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));

    // Vis Nodes formatting
    const visNodes = filteredNodes.map(n => {
      const colors = COLOR_MAP[n.type] || { bg: '#FFFFFF', border: '#000000', text: '#000000' };
      return {
        id: n.id,
        label: n.id,
        shape: 'box',
        margin: 10,
        color: {
          background: colors.bg,
          border: colors.border,
          highlight: { background: '#F4D35E', border: '#000000' },
        },
        borderWidth: 2,
        borderWidthSelected: 3,
        shapeProperties: {
          borderRadius: 0, // strict neobrutalist sharp rectangle
        },
        font: {
          color: colors.text,
          face: 'Space Grotesk',
          size: 13,
          bold: true,
        },
        data: n
      };
    });

    // Vis Edges formatting
    const visEdges = graphData.edges
      .filter(e => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target))
      .map((e, idx) => {
        const isConflict = e.relation === 'CONTRADICTS' || e.relation === 'HAS_LIMITATION';
        return {
          id: `edge_${idx}`,
          from: e.source,
          to: e.target,
          label: e.relation.toLowerCase().replace('_', ' '),
          color: {
            color: isConflict ? '#C94A4A' : '#000000',
            highlight: '#00A896',
          },
          width: isConflict ? 2.5 : 1.8,
          dashes: e.relation === 'CONTRADICTS' ? [6, 6] : false,
          arrows: {
            to: { enabled: true, scaleFactor: 0.8 },
          },
          font: {
            face: 'JetBrains Mono',
            size: 10,
            background: '#FFFFFF',
            strokeWidth: 0,
            align: 'horizontal'
          },
          data: e
        };
      });

    const options = {
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -2500,
          centralGravity: 0.25,
          springLength: 130,
          springConstant: 0.05,
          damping: 0.1,
          avoidOverlap: 0.5
        },
        stabilization: { iterations: 100 }
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true,
      }
    };

    let network = null;
    try {
      network = new Network(containerRef.current, { nodes: visNodes, edges: visEdges }, options);
      networkRef.current = network;

      // Force canvas layout adjustment after render
      setTimeout(() => {
        try {
          if (network) {
            network.fit();
            network.redraw();
          }
        } catch (e) {}
      }, 120);

      network.on('click', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const rawNode = graphData.nodes.find(n => n.id === nodeId);
          setSelectedElement({ type: 'node', data: rawNode });
        } else if (params.edges.length > 0) {
          const edgeId = params.edges[0];
          const rawEdge = visEdges.find(e => e.id === edgeId)?.data;
          setSelectedElement({ type: 'edge', data: rawEdge });
        } else {
          setSelectedElement(null);
        }
      });
    } catch (err) {
      console.error("Vis Network initialization error:", err);
    }

    const handleWindowResize = () => {
      try {
        if (networkRef.current) {
          networkRef.current.fit();
          networkRef.current.redraw();
        }
      } catch (e) {}
    };
    window.addEventListener('resize', handleWindowResize);

    return () => {
      window.removeEventListener('resize', handleWindowResize);
      if (network) {
        network.destroy();
      }
    };
  }, [graphData, selectedFilter]);

  return (
    <div className="flex-1 flex flex-col h-full bg-canvas p-6 overflow-hidden">
      {/* Top Header & Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 shrink-0">
        <div>
          <h2 className="font-heading font-bold text-xl tracking-tight text-black">
            TRACEABLE KNOWLEDGE GRAPH CANVAS
          </h2>
          <span className="font-mono text-xs text-gray-600 block">
            {graphData.nodes.length} NODES | {graphData.edges.length} RELATIONAL EDGES WITH CITATIONS
          </span>
        </div>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 bg-white border-2 border-black p-1 shadow-[3px_3px_0px_0px_#000]">
          {categories.map((cat) => {
            const isActive = selectedFilter === cat;
            const count = categoryCounts[cat] || 0;
            const colorDef = COLOR_MAP[cat];
            
            let activeStyle = 'bg-black text-white';
            if (isActive && colorDef && colorDef.activeBg) {
              activeStyle = `${colorDef.activeBg} font-black`;
            }

            return (
              <button
                key={cat}
                onClick={() => setSelectedFilter(cat)}
                className={`px-2.5 py-1 text-[11px] font-heading font-bold border-2 border-black transition-all flex items-center gap-1.5 ${
                  isActive
                    ? `${activeStyle} shadow-[2px_2px_0px_0px_#000]`
                    : 'bg-white text-black hover:bg-canvas'
                }`}
              >
                <span>{cat.toUpperCase()}</span>
                <span className={`text-[10px] px-1 py-0.2 border border-black ${isActive ? 'bg-white text-black' : 'bg-[#FEF08A] text-black'}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <button
          onClick={loadGraph}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border-2 border-black text-xs font-heading font-bold shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5"
          title="Reload Graph"
        >
          <RefreshCw size={13} strokeWidth={2} />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Main Canvas & Inspector Split */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Interactive Canvas */}
        <div className="flex-1 bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] relative overflow-hidden flex flex-col">
          {/* Canvas Floating Controls */}
          <div className="absolute top-3 right-3 flex items-center gap-1.5 z-10">
            <button
              onClick={() => {
                if (networkRef.current) {
                  networkRef.current.moveTo({ scale: networkRef.current.getScale() * 1.3 });
                }
              }}
              className="p-1.5 bg-white hover:bg-[#FEF08A] border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 text-black"
              title="Zoom In"
            >
              <ZoomIn size={14} strokeWidth={2} />
            </button>
            <button
              onClick={() => {
                if (networkRef.current) {
                  networkRef.current.moveTo({ scale: networkRef.current.getScale() * 0.7 });
                }
              }}
              className="p-1.5 bg-white hover:bg-[#FEF08A] border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 text-black"
              title="Zoom Out"
            >
              <ZoomOut size={14} strokeWidth={2} />
            </button>
            <button
              onClick={() => {
                if (networkRef.current) {
                  networkRef.current.fit({ animation: true });
                }
              }}
              className="px-2 py-1 bg-white hover:bg-[#06D6A0] border-2 border-black font-mono font-bold text-[10px] shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 text-black"
              title="Fit Graph to Screen"
            >
              FIT
            </button>
          </div>

          {graphData.nodes.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center font-mono text-xs">
              <Layers size={32} className="mb-3 text-gray-400" />
              <span className="font-bold text-sm block mb-1">NO GRAPH EXTRACTED YET</span>
              <span className="text-gray-500">Upload research PDFs or load sample benchmarks to generate nodes.</span>
            </div>
          ) : (
            <div 
              ref={containerRef} 
              style={{ width: '100%', height: '100%', minHeight: '520px' }}
              className="flex-1 w-full h-full cursor-grab active:cursor-grabbing" 
            />
          )}

          {/* Legend Overlay at bottom-left */}
          <div className="absolute bottom-3 left-3 bg-white border-2 border-black p-2.5 shadow-[2px_2px_0px_0px_#000] text-[10px] font-mono pointer-events-none flex flex-wrap gap-2.5 z-10">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-[#1D3557] border border-black inline-block"></span> PAPER
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-[#00A896] border border-black inline-block"></span> METHOD
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-[#F4A261] border border-black inline-block"></span> DATASET
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-[#0077B6] border border-black inline-block"></span> METRIC
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-[#C94A4A] border border-black inline-block"></span> LIMITATION
            </span>
          </div>
        </div>

        {/* Selected Inspector Card (Right Pane) */}
        <div className="w-72 bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] p-4 flex flex-col justify-between shrink-0 overflow-y-auto">
          <div>
            <div className="border-b-2 border-black pb-2 mb-3">
              <span className="text-[10px] font-mono font-bold uppercase text-gray-500 block">
                ELEMENT INSPECTOR
              </span>
              <h3 className="font-heading font-bold text-sm">
                {selectedElement ? (selectedElement.type === 'node' ? 'ENTITY NODE' : 'FACT RELATION') : 'CLICK TO INSPECT'}
              </h3>
            </div>

            {selectedElement ? (
              selectedElement.type === 'node' ? (
                <div className="space-y-3 font-mono text-xs">
                  <div>
                    <span className="text-[10px] text-gray-500 block uppercase">IDENTIFIER</span>
                    <span className="font-bold text-sm font-heading block">{selectedElement.data.id}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-500 block uppercase">CATEGORY</span>
                    <span className="inline-block bg-[#F4D35E] border border-black px-1.5 py-0.5 font-bold text-[11px]">
                      {selectedElement.data.type}
                    </span>
                  </div>
                  {selectedElement.data.description && (
                    <div>
                      <span className="text-[10px] text-gray-500 block uppercase">DESCRIPTION</span>
                      <p className="font-sans text-xs mt-0.5 text-gray-800">{selectedElement.data.description}</p>
                    </div>
                  )}
                  {selectedElement.data.papers && selectedElement.data.papers.length > 0 && (
                    <div>
                      <span className="text-[10px] text-gray-500 block uppercase">SOURCE PAPERS</span>
                      <div className="flex flex-col gap-1 mt-1">
                        {selectedElement.data.papers.map((p, i) => (
                          <span key={i} className="bg-canvas border border-black px-1.5 py-0.5 text-[10px] truncate">
                            {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3 font-mono text-xs">
                  <div>
                    <span className="text-[10px] text-gray-500 block uppercase">RELATIONSHIP</span>
                    <span className="font-bold text-teal block">{selectedElement.data.relation}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-500 block uppercase">SOURCE &rarr; TARGET</span>
                    <span className="font-bold block">{selectedElement.data.source} &rarr; {selectedElement.data.target}</span>
                  </div>
                  {selectedElement.data.details && (
                    <div>
                      <span className="text-[10px] text-gray-500 block uppercase">EMPIRICAL DETAILS</span>
                      <p className="font-sans text-xs mt-0.5">{selectedElement.data.details}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-[10px] text-gray-500 block uppercase">EXACT CITATION</span>
                    <span className="inline-block bg-[#F4D35E] border border-black px-1.5 py-0.5 font-bold text-[11px] mt-0.5">
                      {selectedElement.data.citation}
                    </span>
                  </div>
                </div>
              )
            ) : (
              <div className="py-12 text-center text-gray-500 font-mono text-xs">
                Select any node or edge in the graph canvas to inspect its exact citations and empirical attributes.
              </div>
            )}
          </div>

          <div className="pt-3 border-t-2 border-black text-[10px] font-mono text-gray-500 text-center">
            GRAPH ENGINE: NETWORKX + VIS-NETWORK
          </div>
        </div>
      </div>
    </div>
  );
}
