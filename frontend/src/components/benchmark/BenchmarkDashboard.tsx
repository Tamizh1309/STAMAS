import React, { useState, useEffect } from 'react';
import { runBenchmarkEvaluation } from '../../services/api';
import type { BenchmarkEvaluationResponse } from '../../types';

export const BenchmarkDashboard: React.FC = () => {
  const [data, setData] = useState<BenchmarkEvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const executeEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runBenchmarkEvaluation();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to execute benchmark evaluation suite.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeEvaluation();
  }, []);

  return (
    <div style={{ padding: '24px', maxWidth: '1280px', margin: '0 auto', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        borderRadius: '16px',
        padding: '28px',
        color: '#ffffff',
        marginBottom: '24px',
        boxShadow: '0 10px 25px -5px rgba(15, 23, 42, 0.25)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <span style={{ backgroundColor: '#38bdf8', color: '#0f172a', padding: '4px 10px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.5px' }}>PHASE 11 EVALUATION</span>
            <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>SIH26100 GeM Procurement Platform</span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.875rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
            STAMAS System Evaluation & Benchmarking Dashboard
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
            Empirical accuracy validation, retrieval precision, decision confusion matrix, & latency performance metrics computed from Ground Truth datasets.
          </p>
        </div>
        <button
          onClick={executeEvaluation}
          disabled={loading}
          style={{
            backgroundColor: loading ? '#64748b' : '#0284c7',
            color: '#ffffff',
            border: 'none',
            borderRadius: '10px',
            padding: '12px 24px',
            fontWeight: 700,
            fontSize: '0.95rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)',
            transition: 'all 0.2s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          {loading ? 'Executing Suite...' : 'Re-Run Evaluation'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', color: '#991b1b', marginBottom: '24px' }}>
          <strong>Evaluation Error:</strong> {error}
        </div>
      )}

      {loading && !data && (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#64748b' }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '8px' }}>Executing Benchmark Pipeline...</div>
          <div>Evaluating Ground Truth requirements, retrieval accuracy, and compliance decision matrices.</div>
        </div>
      )}

      {data && (
        <>
          {/* Metadata Bar */}
          <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px 16px', fontSize: '0.85rem' }}>
              <strong>Benchmark ID:</strong> <span style={{ fontFamily: 'monospace', color: '#0284c7' }}>{data.benchmark_id}</span>
            </div>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px 16px', fontSize: '0.85rem' }}>
              <strong>Evaluated Cases:</strong> {data.total_cases_evaluated} Ground Truth Cases
            </div>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px 16px', fontSize: '0.85rem' }}>
              <strong>Environment:</strong> {data.environment}
            </div>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px 16px', fontSize: '0.85rem' }}>
              <strong>Timestamp:</strong> {new Date(data.timestamp).toLocaleString()}
            </div>
          </div>

          {/* Metric KPI Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '28px' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.03)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Requirement F1 Score</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#0f172a', margin: '4px 0' }}>
                {(data.requirement_extraction_metrics.f1_score * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 600 }}>Precision: {(data.requirement_extraction_metrics.precision * 100).toFixed(1)}%</div>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.03)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Evidence Top-1 Recall</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#0284c7', margin: '4px 0' }}>
                {(data.evidence_matching_metrics.top1_recall * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.8rem', color: '#0284c7', fontWeight: 600 }}>Top-3 Recall: {(data.evidence_matching_metrics.top3_recall * 100).toFixed(1)}%</div>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.03)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Rule Engine Accuracy</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#8b5cf6', margin: '4px 0' }}>
                {(data.rule_engine_metrics.accuracy * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.8rem', color: '#8b5cf6', fontWeight: 600 }}>Satisfied Ratio: {(data.rule_engine_metrics.satisfied_ratio * 100).toFixed(1)}%</div>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.03)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Decision Engine Accuracy</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#16a34a', margin: '4px 0' }}>
                {(data.decision_engine_metrics.accuracy * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 600 }}>F1 Score: {(data.decision_engine_metrics.f1_score * 100).toFixed(1)}%</div>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.03)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Average Pipeline Latency</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#ea580c', margin: '4px 0' }}>
                {data.latency_metrics_ms.average_ms} ms
              </div>
              <div style={{ fontSize: '0.8rem', color: '#ea580c', fontWeight: 600 }}>P95 Latency: {data.latency_metrics_ms.p95_ms} ms</div>
            </div>
          </div>

          {/* Detailed Section Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '24px', marginBottom: '28px' }}>
            
            {/* Confusion Matrix Card */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                System Decision Confusion Matrix (Ground Truth vs Predicted)
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '16px' }}>
                Rows indicate expected ground-truth decision state; columns indicate actual STAMAS system output decision.
              </p>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ background: '#f1f5f9' }}>
                    <th style={{ padding: '10px', border: '1px solid #cbd5e1', textAlign: 'left' }}>Actual \ Predicted</th>
                    <th style={{ padding: '10px', border: '1px solid #cbd5e1', color: '#16a34a' }}>PASS</th>
                    <th style={{ padding: '10px', border: '1px solid #cbd5e1', color: '#dc2626' }}>FAIL</th>
                    <th style={{ padding: '10px', border: '1px solid #cbd5e1', color: '#d97706' }}>REVIEW</th>
                  </tr>
                </thead>
                <tbody>
                  {['PASS', 'FAIL', 'REVIEW'].map((rowKey) => (
                    <tr key={rowKey}>
                      <td style={{ padding: '10px', border: '1px solid #cbd5e1', fontWeight: 700, textAlign: 'left', background: '#f8fafc' }}>
                        {rowKey}
                      </td>
                      {['PASS', 'FAIL', 'REVIEW'].map((colKey) => {
                        const count = data.decision_engine_metrics.matrix[rowKey]?.[colKey] || 0;
                        const isMatch = rowKey === colKey;
                        return (
                          <td
                            key={colKey}
                            style={{
                              padding: '12px',
                              border: '1px solid #cbd5e1',
                              fontWeight: isMatch ? 800 : 400,
                              background: isMatch && count > 0 ? '#f0fdf4' : '#ffffff',
                              color: isMatch ? '#16a34a' : '#475569'
                            }}
                          >
                            {count}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Error Taxonomy & Latency Breakdown */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                Error Taxonomy & Latency Profile
              </h3>
              
              <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#475569' }}>Error Classification Breakdown:</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '20px' }}>
                {Object.entries(data.error_taxonomy).map(([errKey, count]) => (
                  <div key={errKey} style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.85rem' }}>
                    <div style={{ color: '#64748b', fontSize: '0.75rem', fontWeight: 600 }}>{errKey}</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700, color: count > 0 ? '#dc2626' : '#16a34a' }}>{count}</div>
                  </div>
                ))}
              </div>

              <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#475569' }}>Latency Percentiles (ms):</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center' }}>
                <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>AVG</div>
                  <div style={{ fontWeight: 700 }}>{data.latency_metrics_ms.average_ms}</div>
                </div>
                <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>P50</div>
                  <div style={{ fontWeight: 700 }}>{data.latency_metrics_ms.p50_ms}</div>
                </div>
                <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>P95</div>
                  <div style={{ fontWeight: 700 }}>{data.latency_metrics_ms.p95_ms}</div>
                </div>
                <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>MAX</div>
                  <div style={{ fontWeight: 700 }}>{data.latency_metrics_ms.max_ms}</div>
                </div>
              </div>
            </div>

          </div>

          {/* Scientific Limitations & Disclosures */}
          <div style={{ background: '#fffbebfb', border: '1px solid #fef3c7', borderRadius: '12px', padding: '20px', color: '#92400e' }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '0.95rem', fontWeight: 700 }}>
              Evaluation Methodology & Environment Limitations Disclosures
            </h4>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.85rem', lineHeight: '1.5' }}>
              {data.limitations.map((lim, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{lim}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};
