import React, { useState, useEffect } from 'react';
import { ArrowLeft, Copy, Check } from 'lucide-react';
import type { BidderDocument } from '../../types';
import { fetchBidderDocumentDetail } from '../../services/api';

interface BidderDocumentViewerProps {
  bidderId: number;
  documentId: number;
  initialPageNumber?: number;
  onBack: () => void;
}

export const BidderDocumentViewer: React.FC<BidderDocumentViewerProps> = ({
  bidderId,
  documentId,
  initialPageNumber = 1,
  onBack
}) => {
  const [doc, setDoc] = useState<BidderDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPageNum, setSelectedPageNum] = useState(initialPageNumber);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const loadDetail = async () => {
      try {
        const data = await fetchBidderDocumentDetail(bidderId, documentId);
        setDoc(data);
        if (initialPageNumber && data.pages?.some(p => p.page_number === initialPageNumber)) {
          setSelectedPageNum(initialPageNumber);
        } else if (data.pages && data.pages.length > 0) {
          setSelectedPageNum(data.pages[0].page_number);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }

    };
    loadDetail();
  }, [bidderId, documentId, initialPageNumber]);


  const currentPage = doc?.pages?.find(p => p.page_number === selectedPageNum);

  const handleCopy = () => {
    if (currentPage?.extracted_text) {
      navigator.clipboard.writeText(currentPage.extracted_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) return <div className="text-slate-400 text-sm">Loading document...</div>;
  if (!doc) return <div className="text-red-400 text-sm">Document not found</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 px-3.5 py-2 rounded-xl transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Documents</span>
        </button>

        <div className="flex items-center space-x-3">
          <span className="text-xs text-slate-400 hidden sm:inline">
            Category: <strong className="text-slate-200">{doc.category}</strong>
          </span>
          <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-950/80 px-3 py-1.5 rounded-lg border border-emerald-800/40">
            {doc.filename}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-4">
          <h3 className="text-white text-sm font-bold border-b border-slate-800 pb-2">Pages ({doc.page_count})</h3>
          <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
            {doc.pages?.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedPageNum(p.page_number)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition ${
                  selectedPageNum === p.page_number
                    ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30 font-bold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <span>Page {p.page_number}</span>
                <span className="opacity-50 text-[10px]">{p.extraction_status}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col h-[650px]">
          {currentPage ? (
            <>
              <div className="flex justify-between items-center mb-4 border-b border-slate-800/80 pb-4">
                <h3 className="text-lg font-bold text-white">
                  Page <span className="text-blue-400">{currentPage.page_number}</span>
                </h3>
                <button
                  onClick={handleCopy}
                  className="flex items-center space-x-2 text-xs font-bold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg transition"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  <span>{copied ? 'Copied!' : 'Copy Text'}</span>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto bg-slate-950 rounded-xl p-6 border border-slate-800/50 mb-4">
                <pre className="font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {currentPage.extracted_text || 'No text extracted from this page.'}
                </pre>
              </div>

              <div className="flex items-center justify-between border-t border-slate-800/80 pt-4">
                <div className="flex space-x-4 text-xs">
                  <div>
                    <span className="text-slate-400">Extraction Quality:</span>{' '}
                    <span className={`font-bold ${currentPage.extraction_quality === 'HIGH' ? 'text-emerald-400' : currentPage.extraction_quality === 'MEDIUM' ? 'text-amber-400' : 'text-red-400'}`}>
                      {currentPage.extraction_quality}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Extraction Method:</span>{' '}
                    <span className="font-bold text-cyan-400">
                      {currentPage.extraction_method}
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedPageNum(Math.max(1, selectedPageNum - 1))}
                    disabled={selectedPageNum === 1}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-xs font-bold text-white rounded-lg transition"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setSelectedPageNum(Math.min(doc.page_count, selectedPageNum + 1))}
                    disabled={selectedPageNum === doc.page_count}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-xs font-bold text-white rounded-lg transition"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
              <p>Select a page to view extracted text</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
