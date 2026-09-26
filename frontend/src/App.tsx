import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { TenderDetailView } from './components/TenderDetailView';
import { CreateTenderModal } from './components/CreateTenderModal';
import { BenchmarkDashboard } from './components/benchmark/BenchmarkDashboard';
import { fetchTenders } from './services/api';
import type { Tender } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'tenders' | 'benchmark'>('dashboard');
  const [selectedTenderId, setSelectedTenderId] = useState<number | null>(null);
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const loadTenders = async () => {
    try {
      const data = await fetchTenders(searchQuery);
      setTenders(data);
    } catch (err) {
      console.error('Failed to load tenders', err);
    }
  };

  useEffect(() => {
    loadTenders();
  }, [searchQuery]);

  const handleSelectTender = (tender: Tender) => {
    setSelectedTenderId(tender.id);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Workspace Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'benchmark' ? (
          <BenchmarkDashboard />
        ) : selectedTenderId ? (
          <TenderDetailView
            tenderId={selectedTenderId}
            onBack={() => setSelectedTenderId(null)}
          />
        ) : (
          <Dashboard
            tenders={tenders}
            onSelectTender={handleSelectTender}
            onCreateNew={() => setIsCreateModalOpen(true)}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>STAMAS — Smart Tender Analysis & Management Assessment System</span>
          <span className="font-mono text-slate-600">SIH26100 GeM Procurement Platform</span>
        </div>
      </footer>

      {/* Modal */}
      <CreateTenderModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={loadTenders}
      />
    </div>
  );
}

export default App;
