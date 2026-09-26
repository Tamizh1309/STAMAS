import React, { useState, useEffect } from 'react';
import { 
  Cpu, Sparkles, Plus, Edit2, Trash2, CheckCircle, 
  AlertTriangle, FileText, Check, X, Loader2, Quote
} from 'lucide-react';
import type { Requirement } from '../types';
import { extractRequirements, fetchRequirements, updateRequirement, deleteRequirement, createManualRequirement } from '../services/api';

interface RequirementReviewProps {
  tenderId: number;
  hasExtractedText: boolean;
}

export const RequirementReview: React.FC<RequirementReviewProps> = ({ tenderId, hasExtractedText }) => {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [extracting, setExtracting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Edit Modal State
  const [editingReq, setEditingReq] = useState<Requirement | null>(null);
  const [editText, setEditText] = useState('');
  const [editCategory, setEditCategory] = useState<Requirement['category']>('OTHER');
  const [editMandatory, setEditMandatory] = useState(true);
  const [editStatus, setEditStatus] = useState<Requirement['status']>('CONFIRMED');

  // Add Modal State
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [addText, setAddText] = useState('');
  const [addCategory, setAddCategory] = useState<Requirement['category']>('TECHNICAL');
  const [addMandatory, setAddMandatory] = useState(true);
  const [addSourcePage, setAddSourcePage] = useState<number>(1);
  const [addEvidence, setAddEvidence] = useState('');

  // Evidence Viewer Modal State
  const [viewingEvidence, setViewingEvidence] = useState<Requirement | null>(null);

  const loadRequirements = async (category = activeCategory) => {
    try {
      setLoading(true);
      const data = await fetchRequirements(tenderId, category);
      setRequirements(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load requirements');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequirements(activeCategory);
  }, [tenderId, activeCategory]);

  const handleExtract = async () => {
    try {
      setExtracting(true);
      setError(null);
      setSuccessMsg(null);
      const summary = await extractRequirements(tenderId);
      setSuccessMsg(summary.message);
      await loadRequirements(activeCategory);
    } catch (err: any) {
      setError(err.message || 'Failed to extract requirements');
    } finally {
      setExtracting(false);
    }
  };

  const handleQuickConfirm = async (req: Requirement) => {
    try {
      await updateRequirement(req.id, { status: 'CONFIRMED' });
      setRequirements(prev => prev.map(r => r.id === req.id ? { ...r, status: 'CONFIRMED' } : r));
    } catch (err: any) {
      setError(err.message || 'Failed to confirm requirement');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this requirement?')) return;
    try {
      await deleteRequirement(id);
      setRequirements(prev => prev.filter(r => r.id !== id));
    } catch (err: any) {
      setError(err.message || 'Failed to delete requirement');
    }
  };

  const openEditModal = (req: Requirement) => {
    setEditingReq(req);
    setEditText(req.text);
    setEditCategory(req.category);
    setEditMandatory(req.mandatory);
    setEditStatus(req.status === 'EXTRACTED' ? 'CORRECTED' : req.status);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingReq) return;

    try {
      const updated = await updateRequirement(editingReq.id, {
        text: editText,
        category: editCategory,
        mandatory: editMandatory,
        status: editStatus,
      });
      setRequirements(prev => prev.map(r => r.id === updated.id ? updated : r));
      setEditingReq(null);
    } catch (err: any) {
      setError(err.message || 'Failed to save requirement update');
    }
  };

  const handleSaveAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addText) return;

    try {
      const created = await createManualRequirement(tenderId, {
        text: addText,
        category: addCategory,
        mandatory: addMandatory,
        source_page: addSourcePage,
        evidence_text: addEvidence || addText,
      });
      setRequirements(prev => [...prev, created]);
      setIsAddOpen(false);
      setAddText('');
      setAddEvidence('');
    } catch (err: any) {
      setError(err.message || 'Failed to add manual requirement');
    }
  };

  const getCategoryBadge = (cat: Requirement['category']) => {
    switch (cat) {
      case 'FINANCIAL':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'TECHNICAL':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'ELIGIBILITY':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'DOCUMENT':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const categories = ['ALL', 'ELIGIBILITY', 'TECHNICAL', 'FINANCIAL', 'DOCUMENT', 'OTHER'];

  return (
    <div className="space-y-6">
      
      {/* Top Banner & Trigger Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-bold text-white">Requirement Intelligence Engine</h3>
            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              AI Evidence Extraction
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Extract structured tender requirements into Eligibility, Technical, Financial, and Mandatory Document categories with verbatim source evidence citations.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => setIsAddOpen(true)}
            className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
          >
            <Plus className="w-4 h-4" />
            <span>+ Add Requirement</span>
          </button>

          <button
            onClick={handleExtract}
            disabled={extracting || !hasExtractedText}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/25 transition disabled:opacity-50"
          >
            {extracting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Extraction...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-cyan-200" />
                <span>Extract Requirements</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Category Filter & Metrics Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/60 p-2 rounded-2xl border border-slate-800">
        <div className="flex flex-wrap gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
                activeCategory === cat
                  ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="text-xs text-slate-400 font-mono pr-2">
          Total Listed: <strong className="text-cyan-400">{requirements.length}</strong>
        </div>
      </div>

      {/* Requirements Table */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        </div>
      ) : requirements.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center">
          <Cpu className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h4 className="text-base font-bold text-white mb-1">No Requirements Extracted</h4>
          <p className="text-xs text-slate-400 mb-4 max-w-md mx-auto">
            Click "Extract Requirements" above to run AI intelligence over the tender document text and structure rules.
          </p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300 border-collapse">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Req ID</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4 min-w-[280px]">Requirement Description</th>
                  <th className="py-3.5 px-4 text-center">Mandatory</th>
                  <th className="py-3.5 px-4 text-center">Source Page</th>
                  <th className="py-3.5 px-4 text-center">Confidence</th>
                  <th className="py-3.5 px-4 text-center">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {requirements.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-800/40 transition">
                    
                    {/* Req ID */}
                    <td className="py-3.5 px-4 font-mono text-cyan-400 font-bold whitespace-nowrap">
                      {req.req_code}
                    </td>

                    {/* Category */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className={`inline-block px-2.5 py-1 rounded-lg text-[11px] font-bold border ${getCategoryBadge(req.category)}`}>
                        {req.category}
                      </span>
                    </td>

                    {/* Requirement Text */}
                    <td className="py-3.5 px-4">
                      <p className="text-slate-100 font-medium leading-relaxed mb-1">{req.text}</p>
                      {req.evidence_text && (
                        <div className="flex items-center space-x-1.5 text-[11px] text-slate-400">
                          <Quote className="w-3 h-3 text-cyan-400 shrink-0" />
                          <span className="truncate max-w-md italic font-mono text-slate-400">
                            "{req.evidence_text}"
                          </span>
                        </div>
                      )}
                    </td>

                    {/* Mandatory */}
                    <td className="py-3.5 px-4 text-center whitespace-nowrap">
                      {req.mandatory ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          YES
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
                          NO
                        </span>
                      )}
                    </td>

                    {/* Source Page */}
                    <td className="py-3.5 px-4 text-center whitespace-nowrap">
                      <button
                        onClick={() => setViewingEvidence(req)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-mono font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                      >
                        <FileText className="w-3 h-3 text-cyan-400" />
                        <span>Page {req.source_page || 1}</span>
                      </button>
                    </td>

                    {/* Confidence */}
                    <td className="py-3.5 px-4 text-center whitespace-nowrap font-mono text-xs">
                      {Math.round(req.confidence * 100)}%
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-4 text-center whitespace-nowrap">
                      {req.status === 'REVIEW' ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          <AlertTriangle className="w-3 h-3" />
                          <span>REVIEW</span>
                        </span>
                      ) : req.status === 'CONFIRMED' ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle className="w-3 h-3" />
                          <span>CONFIRMED</span>
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-cyan-400 border border-slate-700">
                          {req.status}
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end space-x-1.5">
                        {req.status !== 'CONFIRMED' && (
                          <button
                            onClick={() => handleQuickConfirm(req)}
                            title="Confirm Requirement"
                            className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => openEditModal(req)}
                          title="Edit Requirement"
                          className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(req.id)}
                          title="Delete Requirement"
                          className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Edit Requirement Modal */}
      {editingReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
            
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
              <div className="flex items-center space-x-2">
                <Edit2 className="w-4 h-4 text-cyan-400" />
                <h4 className="text-base font-bold text-white">Edit Requirement ({editingReq.req_code})</h4>
              </div>
              <button onClick={() => setEditingReq(null)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Category
                </label>
                <select
                  value={editCategory}
                  onChange={(e) => setEditCategory(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="ELIGIBILITY">ELIGIBILITY</option>
                  <option value="TECHNICAL">TECHNICAL</option>
                  <option value="FINANCIAL">FINANCIAL</option>
                  <option value="DOCUMENT">DOCUMENT</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Requirement Text
                </label>
                <textarea
                  rows={3}
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Mandatory Requirement
                  </label>
                  <select
                    value={editMandatory ? 'true' : 'false'}
                    onChange={(e) => setEditMandatory(e.target.value === 'true')}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="true">YES (Mandatory)</option>
                    <option value="false">NO (Non-mandatory)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Status
                  </label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="CONFIRMED">CONFIRMED</option>
                    <option value="CORRECTED">CORRECTED</option>
                    <option value="REVIEW">REVIEW</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingReq(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-cyan-500 hover:bg-cyan-400 shadow-md shadow-cyan-500/20"
                >
                  Save Changes
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

      {/* Add Manual Requirement Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
            
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
              <div className="flex items-center space-x-2">
                <Plus className="w-4 h-4 text-cyan-400" />
                <h4 className="text-base font-bold text-white">Add Manual Requirement</h4>
              </div>
              <button onClick={() => setIsAddOpen(false)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveAdd} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Category
                </label>
                <select
                  value={addCategory}
                  onChange={(e) => setAddCategory(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="ELIGIBILITY">ELIGIBILITY</option>
                  <option value="TECHNICAL">TECHNICAL</option>
                  <option value="FINANCIAL">FINANCIAL</option>
                  <option value="DOCUMENT">DOCUMENT</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Requirement Text
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Bidder must possess valid ISO 9001:2015 certification"
                  value={addText}
                  onChange={(e) => setAddText(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Mandatory
                  </label>
                  <select
                    value={addMandatory ? 'true' : 'false'}
                    onChange={(e) => setAddMandatory(e.target.value === 'true')}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="true">YES</option>
                    <option value="false">NO</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Source Page Number
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={addSourcePage}
                    onChange={(e) => setAddSourcePage(parseInt(e.target.value) || 1)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Verbatim Evidence Snippet
                </label>
                <textarea
                  rows={2}
                  placeholder="Exact quotation from tender document"
                  value={addEvidence}
                  onChange={(e) => setAddEvidence(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-cyan-500 hover:bg-cyan-400 shadow-md shadow-cyan-500/20"
                >
                  Add Requirement
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

      {/* Evidence Viewer Modal */}
      {viewingEvidence && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Quote className="w-5 h-5 text-cyan-400" />
                <h4 className="text-sm font-bold text-white">Source Evidence ({viewingEvidence.req_code})</h4>
              </div>
              <button onClick={() => setViewingEvidence(null)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
              "{viewingEvidence.evidence_text || viewingEvidence.text}"
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Source Document: <strong className="text-cyan-300 font-mono">{viewingEvidence.source_document}</strong></span>
              <span>Source Page: <strong className="text-white font-mono">Page {viewingEvidence.source_page || 1}</strong></span>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setViewingEvidence(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700"
              >
                Close Evidence
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
