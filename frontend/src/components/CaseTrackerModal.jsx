import React, { useState } from 'react';
import { Search, X, CheckCircle, Clock, AlertTriangle, Building, FileText, ArrowRight } from 'lucide-react';

export default function CaseTrackerModal({ isOpen, onClose }) {
  const [radicado, setRadicado] = useState('');
  const [loading, setLoading] = useState(false);
  const [caseData, setCaseData] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!radicado.trim()) return;

    setLoading(true);
    setError(null);
    setCaseData(null);

    try {
      const res = await fetch(`/api/cases/${encodeURIComponent(radicado.trim())}`);
      if (!res.ok) {
        throw new Error('No se encontró ningún caso con ese número de radicado.');
      }
      const data = await res.json();
      setCaseData(data);
    } catch (err) {
      setError(err.message || 'Error al consultar el caso.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-slate-200">
        
        {/* Modal Header */}
        <div className="bg-[#102A43] text-white p-5 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-[#1769AA] rounded-lg">
              <Search className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Consulta Oficial de Solicitud</h3>
              <p className="text-xs text-blue-200">Seguimiento en línea con radicado distrital</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg transition text-slate-300 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-5 border-b border-slate-100 bg-[#F2F6FA]">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              placeholder="Ingresa tu radicado (ej. BQL-2026-00101)..."
              value={radicado}
              onChange={(e) => setRadicado(e.target.value)}
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-[#1769AA] bg-white text-sm"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-[#1769AA] hover:bg-[#102A43] text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition flex items-center space-x-1.5 disabled:opacity-50"
            >
              {loading ? <span>Buscando...</span> : <span>Consultar</span>}
            </button>
          </form>
          <div className="mt-2 text-xs text-slate-500 flex gap-2">
            <span>Ejemplos rápidos:</span>
            <button type="button" onClick={() => setRadicado('BQL-2026-00101')} className="text-[#1769AA] hover:underline font-mono">BQL-2026-00101</button>
            <button type="button" onClick={() => setRadicado('BQL-2026-00103')} className="text-[#1769AA] hover:underline font-mono">BQL-2026-00103</button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto flex-1">
          {error && (
            <div className="p-4 rounded-xl bg-red-50 text-[#B54747] text-sm border border-red-200 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Búsqueda sin resultados</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          {caseData && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-[#1769AA] bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
                    {caseData.radicado}
                  </span>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    caseData.status === 'RESUELTO' ? 'bg-green-100 text-[#23856D]' :
                    caseData.status === 'ESCALADO_HUMANO' ? 'bg-amber-100 text-amber-800' :
                    'bg-blue-100 text-[#1769AA]'
                  }`}>
                    {caseData.status}
                  </span>
                </div>
                <h4 className="font-bold text-slate-800 text-sm mb-1">{caseData.title}</h4>
                <p className="text-xs text-slate-600 mb-2">{caseData.description}</p>
                
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 pt-2 border-t border-slate-200">
                  <div>
                    <span className="text-slate-400 block">Dependencia:</span>
                    <span className="font-medium text-slate-800">{caseData.assigned_to}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Fecha Límite (SLA):</span>
                    <span className="font-medium text-slate-800">{caseData.sla_due_date || 'No asignada'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Ubicación:</span>
                    <span className="font-medium text-slate-800">{caseData.address} - {caseData.neighborhood}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Prioridad:</span>
                    <span className="font-semibold text-slate-800">{caseData.priority}</span>
                  </div>
                </div>
              </div>

              {/* Eventos / Historial */}
              <div>
                <h5 className="font-bold text-xs uppercase tracking-wider text-slate-500 mb-3 flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Línea de Tiempo del Trámite</span>
                </h5>
                <div className="relative pl-6 space-y-3 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                  {caseData.events && caseData.events.map((ev, i) => (
                    <div key={ev.id || i} className="relative text-xs">
                      <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-[#1769AA] border-2 border-white shadow-xs"></div>
                      <div className="font-semibold text-slate-800 flex items-center justify-between">
                        <span>{ev.event_type}</span>
                        <span className="text-[10px] text-slate-400 font-normal">{ev.timestamp}</span>
                      </div>
                      <p className="text-slate-600 mt-0.5">{ev.description}</p>
                      <span className="text-[10px] text-blue-600 font-mono">Por: {ev.actor} ({ev.actor_role})</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {!caseData && !error && (
            <div className="text-center py-8 text-slate-400">
              <FileText className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="text-sm">Escribe tu número de radicado arriba para visualizar el estado oficial del caso.</p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 font-medium transition"
          >
            Cerrar
          </button>
        </div>

      </div>
    </div>
  );
}
