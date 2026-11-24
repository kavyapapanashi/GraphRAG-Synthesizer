import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import GraphView from './components/GraphView';
import MatrixView from './components/MatrixView';
import QuizView from './components/QuizView';
import { 
  fetchStats, 
  sendChatQuery, 
  ingestFiles, 
  loadSamplePapers, 
  resetSession 
} from './api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [stats, setStats] = useState({
    papers: [],
    total_pages: 0,
    chunks_count: 0,
    nodes_count: 0,
    edges_count: 0,
  });
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');

  // Initial stats load
  const refreshStats = async (initial = false) => {
    try {
      const data = await fetchStats();
      setStats(data);
      if (initial && data.papers && data.papers.length > 0) {
        setMessages([
          {
            role: 'assistant',
            content: `### Welcome to GraphRAG Multi-Paper Synthesizer!\n\nPre-indexed **${data.papers.length} academic benchmark papers** (${data.papers.join(', ')}). Extracted **${data.chunks_count} text passages** in ChromaDB and constructed an academic Knowledge Graph with **${data.nodes_count} verified nodes** and **${data.edges_count} relational edges** with exact page citations.\n\nAsk any research question below, or explore the **Knowledge Graph**, **Comparison Matrix**, and **Active-Recall Study Hub** in the left sidebar!`,
            citations: ['[GraphRAG_Reasoning, p. 1]', '[DenseRetriever_Scale, p. 1]', '[HybridSearch_Fusion, p. 1]'],
          }
        ]);
      }
    } catch (err) {
      console.error("Stats refresh error:", err);
    }
  };

  useEffect(() => {
    refreshStats(true);
  }, []);

  // Handle Chat Query
  const handleSendMessage = async (queryText) => {
    if (!queryText.trim() || isLoading) return;

    // Append user message
    const userMsg = {
      role: 'user',
      content: queryText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await sendChatQuery(queryText);
      const aiMsg = {
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
        graph_paths: res.graph_paths || [],
        triples: res.triples || [],
        chunks: res.chunks || [],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMsg = {
        role: 'assistant',
        content: "Error executing hybrid GraphRAG retrieval. Please ensure the backend is running and papers are indexed.",
        citations: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle File Upload
  const handleFileUpload = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    setIsUploading(true);
    setUploadProgress(`PARSING ${fileList.length} PDF(S)...`);

    try {
      const res = await ingestFiles(fileList);
      await refreshStats();
      setUploadProgress('INGESTION COMPLETE');

      // Add system confirmation message in chat
      const sysMsg = {
        role: 'assistant',
        content: `Successfully ingested **${res.papers.length}** research paper(s). Extracted **${res.chunks_count}** chunks and constructed an academic Knowledge Graph with **${res.nodes_count}** nodes and **${res.edges_count}** relational edges.`,
        citations: [],
      };
      setMessages((prev) => [...prev, sysMsg]);
    } catch (err) {
      console.error("Upload error:", err);
      alert(`Ingestion failed: ${err.message}`);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(''), 3000);
    }
  };

  // Handle Loading 3 Benchmark Sample Papers
  const handleLoadSamples = async () => {
    setIsUploading(true);
    setUploadProgress('LOADING 3 BENCHMARK PAPERS...');

    try {
      const res = await loadSamplePapers();
      await refreshStats();
      setUploadProgress('BENCHMARKS LOADED');

      const sysMsg = {
        role: 'assistant',
        content: `Loaded 3 academic benchmark papers (**GraphRAG**, **DenseRetriever**, **HybridSearch**). Total **${res.chunks_count}** chunks indexed in ChromaDB and **${res.nodes_count}** nodes assembled in the Knowledge Graph with exact cross-paper citations.`,
        citations: ['[GraphRAG_Reasoning, p. 1]', '[DenseRetriever_Scale, p. 1]', '[HybridSearch_Fusion, p. 1]'],
      };
      setMessages((prev) => [...prev, sysMsg]);
    } catch (err) {
      console.error("Sample papers load error:", err);
      alert(`Failed to load benchmark papers: ${err.message}`);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(''), 3000);
    }
  };

  // Handle Resetting / Creating New Session
  const handleNewSession = async () => {
    setIsLoading(true);
    try {
      await resetSession();
      setMessages([]);
      setCurrentTab('chat');
      await refreshStats(false);
    } catch (err) {
      console.error("New session creation error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-canvas font-sans text-black">
      {/* Collapsible Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
        stats={stats}
        onNewSession={handleNewSession}
        onLoadSamples={handleLoadSamples}
        isLoading={isLoading || isUploading}
      />

      {/* Main Workspace View */}
      <main className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        {currentTab === 'chat' && (
          <ChatView
            messages={messages}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            isLoading={isLoading}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            stats={stats}
            onNavigateTab={setCurrentTab}
          />
        )}

        {currentTab === 'graph' && <GraphView />}

        {currentTab === 'matrix' && <MatrixView />}

        {currentTab === 'quiz' && <QuizView stats={stats} messages={messages} />}
      </main>
    </div>
  );
}
