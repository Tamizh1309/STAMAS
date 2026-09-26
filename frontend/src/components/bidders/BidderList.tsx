import React, { useState, useEffect } from 'react';
import { Plus, Building, Trash2 } from 'lucide-react';
import type { Bidder } from '../../types';
import { fetchBidders, deleteBidder } from '../../services/api';
import { BidderDetail } from './BidderDetail';
import { AddBidderModal } from './AddBidderModal';

interface BidderListProps {
  tenderId: number;
}

export const BidderList: React.FC<BidderListProps> = ({ tenderId }) => {
  const [bidders, setBidders] = useState<Bidder[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBidderId, setSelectedBidderId] = useState<number | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const loadBidders = async () => {
    try {
      setLoading(true);
      const data = await fetchBidders(tenderId);
      setBidders(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBidders();
  }, [tenderId]);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this bidder and all their documents?')) return;
    try {
      await deleteBidder(id);
      await loadBidders();
    } catch (err) {
      console.error(err);
      alert('Failed to delete bidder');
    }
  };

  if (selectedBidderId) {
    return <BidderDetail tenderId={tenderId} bidderId={selectedBidderId} onBack={() => setSelectedBidderId(null)} />;
  }

  if (loading) return <div className="text-slate-400 text-sm">Loading bidders...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">Bidders</h3>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white text-xs font-bold rounded-xl transition"
        >
          <Plus className="w-4 h-4" />
          <span>Add Bidder</span>
        </button>
      </div>

      {bidders.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
          <Building className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h4 className="text-white font-medium">No bidders added yet</h4>
          <p className="text-slate-400 text-sm mt-1 mb-6">Add a bidder to start evaluating their proposals and documents.</p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 text-xs font-bold rounded-xl transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add First Bidder</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {bidders.map((bidder) => (
            <div key={bidder.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-white font-bold text-base">{bidder.company_name}</h4>
                  <p className="text-slate-400 text-xs">{bidder.bidder_name}</p>
                </div>
                <span className="px-2.5 py-1 text-[10px] font-bold rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  {bidder.status}
                </span>
              </div>
              
              <div className="space-y-2 mb-6">
                <div className="flex items-center text-xs text-slate-400">
                  <span className="w-20 font-medium">Reg No:</span>
                  <span className="text-slate-200">{bidder.registration_number || '-'}</span>
                </div>
                <div className="flex items-center text-xs text-slate-400">
                  <span className="w-20 font-medium">Added:</span>
                  <span className="text-slate-200">{new Date(bidder.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              
              <div className="mt-auto flex items-center space-x-2">
                <button
                  onClick={() => setSelectedBidderId(bidder.id)}
                  className="flex-1 px-3 py-2 bg-cyan-500 text-white text-xs font-bold rounded-lg hover:bg-cyan-400 transition"
                >
                  View Workspace
                </button>
                <button
                  onClick={() => handleDelete(bidder.id)}
                  className="px-3 py-2 bg-red-500/10 text-red-400 text-xs font-bold rounded-lg hover:bg-red-500/20 transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isAddModalOpen && (
        <AddBidderModal
          tenderId={tenderId}
          onClose={() => setIsAddModalOpen(false)}
          onSuccess={() => {
            setIsAddModalOpen(false);
            loadBidders();
          }}
        />
      )}
    </div>
  );
};
