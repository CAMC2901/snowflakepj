import React from 'react';
import { X, Printer, CheckCircle2, Building2, Calendar, MapPin, Clock, ShieldCheck } from 'lucide-react';

export default function ComprobanteModal({ isOpen, onClose, data }) {
  if (!isOpen || !data) return null;

  const handlePrint = () => {
    window.print();
  };

  const comp = data.comprobante || {
    radicado: data.radicado || "BQL-2026-00000",
    codigo_verificacion: "VERIF-9921",
    fecha_radicacion: new Date().toLocaleDateString('es-CO'),
    entidad: "Alcaldía Distrital de Barranquilla",
    dependencia: data.department_name || "Secretaría Distrital",
    plazo_dias_habiles: data.sla_days || 15,
    fecha_limite_sla: data.sla_due_date || "Pendiente",
    ciudadano: "Ciudadano Solicitante",
    ubicacion: "Barranquilla, Atlántico",
    proximos_pasos: [
      "Su caso fue asignado formalmente a la dependencia competente.",
      "Se realizará la revisión técnica en el término legal establecido.",
      "Puede consultar el avance en este portal con su número de radicado."
    ]
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-xl w-full overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
        
        {/* Cabecera del Comprobante */}
        <div className="bg-[#102A43] text-white p-6 flex items-center justify-between border-b border-[#20A4C8]/30">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#1769AA] flex items-center justify-center text-white shadow-xs">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#F2B544] block">
                Distrito de Barranquilla
              </span>
              <h3 className="font-bold text-lg text-white">Comprobante Oficial de Radicación</h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-xl text-slate-300 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido Imprimible */}
        <div id="printable-comprobante" className="p-6 space-y-5 bg-white text-slate-800 text-xs">
          
          {/* Tarjeta de Radicado Principal */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase block">Número Único de Radicado</span>
              <span className="text-xl font-mono font-bold text-[#1769AA] tracking-tight">{comp.radicado}</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase block">Código Digital</span>
              <span className="font-mono text-xs font-bold text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                {comp.codigo_verificacion}
              </span>
            </div>
          </div>

          {/* Datos del Trámite */}
          <div className="grid grid-cols-2 gap-3 p-4 rounded-2xl bg-[#F2F6FA] border border-slate-200/80">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Dependencia Responsable</span>
              <span className="font-semibold text-slate-800 text-xs">{comp.dependencia}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Fecha de Radicación</span>
              <span className="font-semibold text-slate-800 text-xs">{comp.fecha_radicacion}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Plazo Legal de Atención</span>
              <span className="font-semibold text-emerald-700 text-xs">{comp.plazo_dias_habiles} días hábiles (Ley 1755)</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Fecha Límite Estimada</span>
              <span className="font-semibold text-slate-800 text-xs">{comp.fecha_limite_sla}</span>
            </div>
          </div>

          {/* Próximos Pasos */}
          <div>
            <h5 className="font-bold text-slate-900 uppercase text-[11px] mb-2 flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-[#23856D]" />
              <span>Próximas Actuaciones Institucionales</span>
            </h5>
            <ul className="space-y-1.5 text-slate-600 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              {comp.proximos_pasos?.map((paso, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-[#1769AA] font-bold">•</span>
                  <span>{paso}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Aviso Institucional */}
          <div className="p-3 rounded-xl bg-blue-50 border border-blue-100 flex items-center space-x-2.5 text-[11px] text-blue-900">
            <ShieldCheck className="w-5 h-5 text-[#1769AA] shrink-0" />
            <p>
              Este comprobante certifica la recepción de su requerimiento ante la Alcaldía Distrital de Barranquilla. Puede consultar el estado en cualquier momento con su número de radicado.
            </p>
          </div>

        </div>

        {/* Footer y Acciones */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">Ventanilla Única Virtual</span>
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-[#1769AA] hover:bg-[#102A43] text-white font-semibold rounded-xl text-xs transition flex items-center space-x-1.5 shadow-xs"
            >
              <Printer className="w-4 h-4" />
              <span>Imprimir Comprobante</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-slate-600 hover:text-slate-900 font-medium text-xs transition"
            >
              Cerrar
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
