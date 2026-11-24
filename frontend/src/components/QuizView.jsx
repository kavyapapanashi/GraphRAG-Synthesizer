import React, { useEffect, useState } from 'react';
import { 
  GraduationCap, 
  RotateCw, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ChevronLeft, 
  ChevronRight, 
  Layers,
  RefreshCw,
  HelpCircle
} from 'lucide-react';
import { fetchQuiz } from '../api';

export default function QuizView({ stats = { papers: [] }, messages = [] }) {
  const [quizData, setQuizData] = useState({ paper: 'ALL', questions: [], flashcards: [] });
  const [selectedPaper, setSelectedPaper] = useState('ALL');
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submittedAnswers, setSubmittedAnswers] = useState({});
  const [score, setScore] = useState(0);
  const [flashcardIdx, setFlashcardIdx] = useState(0);
  const [showFlashcardBack, setShowFlashcardBack] = useState(false);
  const [mode, setMode] = useState('quiz'); // 'quiz' or 'flashcards'
  const [isLoading, setIsLoading] = useState(true);

  const loadQuiz = async (paperOverride) => {
    setIsLoading(true);
    setSelectedAnswers({});
    setSubmittedAnswers({});
    setScore(0);
    setFlashcardIdx(0);
    setShowFlashcardBack(false);

    const paperToFetch = paperOverride !== undefined ? paperOverride : selectedPaper;
    const sessionTopics = messages
      .filter(m => m.role === 'user')
      .map(m => m.content);

    try {
      const data = await fetchQuiz(paperToFetch, sessionTopics);
      setQuizData(data);
    } catch (err) {
      console.error("Failed to load quiz:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQuiz();
  }, []);

  const handleSelectOption = (qIdx, optIdx) => {
    if (submittedAnswers[qIdx] !== undefined) return; // already submitted
    setSelectedAnswers(prev => ({ ...prev, [qIdx]: optIdx }));
  };

  const handleSubmitAnswer = (qIdx) => {
    const selected = selectedAnswers[qIdx];
    if (selected === undefined) return;

    const q = quizData.questions[qIdx];
    const isCorrect = selected === q.correct_index;

    setSubmittedAnswers(prev => ({ ...prev, [qIdx]: isCorrect }));
    if (isCorrect) {
      setScore(prev => prev + 1);
    }
  };

  const nextFlashcard = () => {
    if (quizData.flashcards.length === 0) return;
    setFlashcardIdx((flashcardIdx + 1) % quizData.flashcards.length);
    setShowFlashcardBack(false);
  };

  const prevFlashcard = () => {
    if (quizData.flashcards.length === 0) return;
    setFlashcardIdx((flashcardIdx - 1 + quizData.flashcards.length) % quizData.flashcards.length);
    setShowFlashcardBack(false);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-canvas p-6 overflow-y-auto">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="font-heading font-bold text-xl tracking-tight text-black">
            ACTIVE-RECALL STUDY HUB
          </h2>
          <span className="font-mono text-xs text-gray-600 block">
            REINFORCE GROUNDED KNOWLEDGE & TEST METHODOLOGICAL UNDERSTANDING
          </span>
        </div>

        {/* Mode Switcher & Reload */}
        <div className="flex items-center gap-3">
          <div className="flex border-2 border-black bg-white shadow-[3px_3px_0px_0px_#000]">
            <button
              onClick={() => setMode('quiz')}
              className={`px-3 py-1.5 text-xs font-heading font-bold transition-all ${
                mode === 'quiz' ? 'bg-black text-white' : 'bg-white text-black hover:bg-canvas'
              }`}
            >
              MCQ QUIZ
            </button>
            <button
              onClick={() => setMode('flashcards')}
              className={`px-3 py-1.5 text-xs font-heading font-bold border-l-2 border-black transition-all ${
                mode === 'flashcards' ? 'bg-black text-white' : 'bg-white text-black hover:bg-canvas'
              }`}
            >
              FLASHCARDS
            </button>
          </div>

          <button
            onClick={loadQuiz}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border-2 border-black text-xs font-heading font-bold shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5"
            title="Generate New Quiz Questions"
          >
            <RefreshCw size={13} strokeWidth={2} className={isLoading ? 'animate-spin' : ''} />
            <span>REGENERATE</span>
          </button>
        </div>
      </div>

      {/* Target Paper & Session Focus Bar */}
      <div className="bg-white border-2 border-black p-3.5 mb-6 shadow-[4px_4px_0px_0px_#000]">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
          <span className="font-mono text-[10px] font-black uppercase text-black tracking-wider flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 bg-[#FFD166] border border-black inline-block"></span>
            QUIZ FOCUS (SELECT TARGET PAPER OR SESSION TOPICS):
          </span>
          <span className="font-mono text-[10px] font-bold bg-[#D8F3DC] text-[#006644] border border-black px-2 py-0.5">
            {quizData.questions.length} QUESTIONS GROUNDED IN {selectedPaper.toUpperCase()}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => {
              setSelectedPaper('ALL');
              loadQuiz('ALL');
            }}
            className={`px-3 py-1.5 text-xs font-heading font-black border-2 border-black transition-all ${
              selectedPaper === 'ALL'
                ? 'bg-black text-white shadow-[2px_2px_0px_0px_#000]'
                : 'bg-white text-black hover:bg-canvas'
            }`}
          >
            ALL PAPERS (SYNTHESIS)
          </button>

          {stats.papers && stats.papers.map((p, pIdx) => {
            const isSelected = selectedPaper === p;
            const colors = ['bg-[#00A896]', 'bg-[#FF9F1C]', 'bg-[#06D6A0]', 'bg-[#C77DFF]'];
            const activeColor = colors[pIdx % colors.length];

            return (
              <button
                key={pIdx}
                onClick={() => {
                  setSelectedPaper(p);
                  loadQuiz(p);
                }}
                className={`px-3 py-1.5 text-xs font-heading font-bold border-2 border-black transition-all truncate max-w-[220px] ${
                  isSelected
                    ? `${activeColor} text-white font-black shadow-[2px_2px_0px_0px_#000]`
                    : 'bg-white text-black hover:bg-canvas'
                }`}
                title={`Quiz strictly grounded in ${p}`}
              >
                {p}
              </button>
            );
          })}

          {messages.length > 0 && (
            <button
              onClick={() => {
                setSelectedPaper('SESSION');
                loadQuiz('SESSION');
              }}
              className={`px-3 py-1.5 text-xs font-heading font-bold border-2 border-black transition-all ${
                selectedPaper === 'SESSION'
                  ? 'bg-[#FF5A5F] text-white font-black shadow-[2px_2px_0px_0px_#000]'
                  : 'bg-white text-black hover:bg-canvas'
              }`}
              title="Quiz on topics and queries asked in this chat session"
            >
              CURRENT CHAT SESSION ({messages.filter(m => m.role === 'user').length} QUERIES)
            </button>
          )}
        </div>
      </div>

      {/* MODE 1: MCQ QUIZ */}
      {mode === 'quiz' ? (
        <div className="max-w-2xl mx-auto w-full space-y-6">
          {/* Live Score Counter */}
          <div className="bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-[#00A896] border border-black flex items-center justify-center text-white">
                <GraduationCap size={15} strokeWidth={2} />
              </div>
              <span className="font-heading font-black text-sm tracking-wide">TEST PROGRESS</span>
            </div>
            <div className="font-mono text-xs font-bold flex items-center gap-2">
              <span>SCORE:</span>
              <span className="text-black bg-[#FFD166] border-2 border-black px-2.5 py-0.5 text-sm font-black shadow-[2px_2px_0px_0px_#000]">
                {score} / {quizData.questions.length}
              </span>
            </div>
          </div>

          {quizData.questions.length === 0 ? (
            <div className="bg-white border-2 border-black p-12 text-center font-mono text-xs text-gray-500 shadow-[4px_4px_0px_0px_#000]">
              <HelpCircle size={32} className="mx-auto mb-2 text-gray-400" />
              <span className="font-bold block text-sm">NO QUESTIONS AVAILABLE</span>
              <span>Upload papers or click REGENERATE to construct an active-recall quiz.</span>
            </div>
          ) : (
            quizData.questions.map((q, idx) => {
              const isSubmitted = submittedAnswers[idx] !== undefined;
              const isCorrect = submittedAnswers[idx] === true;
              const selectedOpt = selectedAnswers[idx];

              return (
                <div
                  key={idx}
                  className={`bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] p-6 transition-all ${
                    isSubmitted 
                      ? isCorrect 
                        ? 'border-l-8 border-l-[#00A896]' 
                        : 'border-l-8 border-l-[#C94A4A]'
                      : q.is_limitation_warning
                        ? 'border-l-8 border-l-[#FF9F1C] bg-[#FFFBEB]/30'
                        : ''
                  }`}
                >
                  {/* Question Header & Limitation Tag */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="font-mono text-xs font-bold text-gray-500">
                      QUESTION {idx + 1} OF {quizData.questions.length}
                    </span>
                    {q.is_limitation_warning ? (
                      <span className="bg-[#FFDDD2] text-[#C94A4A] border-2 border-[#C94A4A] px-2 py-0.5 text-[10px] font-mono font-bold flex items-center gap-1 shadow-[1px_1px_0px_0px_#000]">
                        <AlertTriangle size={11} strokeWidth={2} />
                        LIMITATION CAVEAT
                      </span>
                    ) : (
                      <span className="bg-[#D8F3DC] text-[#006644] border border-black px-2 py-0.5 text-[10px] font-mono font-bold">
                        EMPIRICAL FACT
                      </span>
                    )}
                  </div>

                  <h3 className="font-heading font-bold text-base text-black mb-4 leading-snug">
                    {q.question}
                  </h3>

                  {/* Options */}
                  <div className="space-y-2 mb-4">
                    {q.options.map((opt, optIdx) => {
                      const isSelected = selectedOpt === optIdx;
                      let btnStyle = "bg-white border-2 border-black hover:bg-canvas";
                      
                      if (isSubmitted) {
                        if (optIdx === q.correct_index) {
                          btnStyle = "bg-[#D8F3DC] border-2 border-[#006644] font-bold text-[#006644] shadow-[2px_2px_0px_0px_#000]";
                        } else if (isSelected && !isCorrect) {
                          btnStyle = "bg-[#FFDDD2] border-2 border-[#C94A4A] text-[#C94A4A]";
                        } else {
                          btnStyle = "bg-gray-50 border border-gray-300 opacity-60";
                        }
                      } else if (isSelected) {
                        btnStyle = "bg-[#FFD166] border-2 border-black font-bold shadow-[2px_2px_0px_0px_#000]";
                      }

                      return (
                        <button
                          key={optIdx}
                          onClick={() => handleSelectOption(idx, optIdx)}
                          disabled={isSubmitted}
                          className={`w-full text-left p-3 text-xs font-sans flex items-start gap-3 transition-all ${btnStyle}`}
                        >
                          <span className={`font-mono font-bold uppercase w-5 h-5 border border-black flex items-center justify-center shrink-0 ${isSelected ? 'bg-black text-white' : 'bg-white text-black'}`}>
                            {String.fromCharCode(65 + optIdx)}
                          </span>
                          <span className="pt-0.5 font-medium">{opt}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Submit Answer Button */}
                  {!isSubmitted ? (
                    <button
                      onClick={() => handleSubmitAnswer(idx)}
                      disabled={selectedOpt === undefined}
                      className="w-full bg-[#00A896] hover:bg-[#029685] text-white border-2 border-black font-heading font-bold py-2.5 px-4 text-xs tracking-wider shadow-[3px_3px_0px_0px_#000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      SUBMIT ANSWER
                    </button>
                  ) : (
                    /* Explanation & Citations */
                    <div className="pt-3 border-t-2 border-black mt-3 bg-canvas/40 p-3 border-2 border-dashed border-black">
                      <div className="flex items-center gap-1.5 font-heading font-bold text-xs mb-1">
                        {isCorrect ? (
                          <span className="text-[#00A896] font-black flex items-center gap-1">
                            <CheckCircle2 size={15} strokeWidth={2} /> CORRECT ANSWER
                          </span>
                        ) : (
                          <span className="text-[#C94A4A] font-black flex items-center gap-1">
                            <XCircle size={15} strokeWidth={2} /> INCORRECT
                          </span>
                        )}
                      </div>
                      <p className="text-xs font-sans text-gray-900 leading-relaxed">
                        {q.explanation}
                      </p>
                      <div className="mt-2 flex items-center gap-1.5">
                        <span className="text-[10px] font-mono text-gray-700 font-bold uppercase">CITATION:</span>
                        <span className="bg-[#FFD166] text-black border border-black px-2 py-0.5 text-[10px] font-mono font-bold shadow-[1px_1px_0px_0px_#000]">
                          {q.citation}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      ) : (
        /* MODE 2: FLASHCARDS */
        <div className="max-w-md mx-auto w-full my-auto flex flex-col items-center">
          {quizData.flashcards.length === 0 ? (
            <div className="bg-white border-2 border-black p-12 text-center font-mono text-xs text-gray-500 shadow-[4px_4px_0px_0px_#000] w-full">
              <Layers size={32} className="mx-auto mb-2 text-gray-400" />
              <span className="font-bold block text-sm">NO FLASHCARDS AVAILABLE</span>
              <span>Upload research papers to generate concept flashcards.</span>
            </div>
          ) : (
            <div className="w-full">
              {/* Card Indicator */}
              <div className="text-center font-mono text-xs text-gray-600 mb-3 font-bold">
                FLASHCARD {flashcardIdx + 1} OF {quizData.flashcards.length}
              </div>

              {/* Neobrutalist Flashcard Box */}
              {(() => {
                const card = quizData.flashcards[flashcardIdx];
                return (
                  <div className={`border-2 border-black shadow-[6px_6px_0px_0px_#000] p-8 min-h-[280px] flex flex-col justify-between text-center relative mb-6 transition-all ${
                    showFlashcardBack ? 'bg-[#D8F3DC]' : 'bg-[#FEF08A]'
                  }`}>
                    <div>
                      {/* Tag */}
                      <span className={`inline-block border-2 border-black px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase mb-4 shadow-[1px_1px_0px_0px_#000] ${
                        card.tag === 'Limitation' 
                          ? 'bg-[#FFDDD2] text-[#C94A4A]' 
                          : 'bg-white text-black'
                      }`}>
                        {card.tag || 'RESEARCH CONCEPT'}
                      </span>

                      {/* Front Prompt */}
                      <h3 className="font-heading font-black text-lg text-black mb-4 leading-snug">
                        {card.front}
                      </h3>

                      {/* Back Answer (Revealed) */}
                      {showFlashcardBack && (
                        <div className="pt-4 border-t-2 border-dashed border-black mt-4 text-left bg-white p-4 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
                          <span className="text-[10px] font-mono uppercase text-gray-700 font-black block mb-1">
                            GROUNDED SYNTHESIS:
                          </span>
                          <p className="font-sans text-xs text-gray-950 leading-relaxed mb-3">
                            {card.back}
                          </p>
                          <span className="inline-block bg-[#FFD166] text-black border border-black px-2 py-0.5 text-[10px] font-mono font-bold shadow-[1px_1px_0px_0px_#000]">
                            {card.citation}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Reveal Button */}
                    <button
                      onClick={() => setShowFlashcardBack(!showFlashcardBack)}
                      className="mt-6 w-full bg-white border-2 border-black font-heading font-black py-2.5 text-xs tracking-wider shadow-[3px_3px_0px_0px_#000] hover:bg-canvas active:translate-x-0.5 active:translate-y-0.5"
                    >
                      {showFlashcardBack ? "HIDE ANSWER" : "REVEAL ANSWER & CITATION"}
                    </button>
                  </div>
                );
              })()}

              {/* Navigation Controls */}
              <div className="flex items-center justify-between gap-4">
                <button
                  onClick={prevFlashcard}
                  className="flex-1 flex items-center justify-center gap-1.5 bg-white border-2 border-black font-heading font-black py-2.5 text-xs shadow-[3px_3px_0px_0px_#000] hover:bg-canvas active:translate-x-0.5 active:translate-y-0.5"
                >
                  <ChevronLeft size={16} strokeWidth={2} />
                  <span>PREVIOUS</span>
                </button>
                <button
                  onClick={nextFlashcard}
                  className="flex-1 flex items-center justify-center gap-1.5 bg-[#00A896] hover:bg-[#029685] text-white border-2 border-black font-heading font-black py-2.5 text-xs shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5"
                >
                  <span>NEXT</span>
                  <ChevronRight size={16} strokeWidth={2} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
