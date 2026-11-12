import React, { useState } from 'react';
import Header from './components/Header';
import CitizenPortal from './components/CitizenPortal';
import AdminDashboard from './components/AdminDashboard';
import CaseTrackerModal from './components/CaseTrackerModal';

export default function App() {
  const [currentView, setCurrentView] = useState('citizen'); // 'citizen' or 'admin'
  const [trackerOpen, setTrackerOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex flex-col font-sans text-[#102A43]">
      {/* Barra de Navegación Institucional */}
      <Header
        currentView={currentView}
        setCurrentView={setCurrentView}
        onOpenTracker={() => setTrackerOpen(true)}
      />

      {/* Franja de Identidad Distrital (Bandera de Barranquilla: Rojo, Amarillo, Verde) */}
      <div className="h-1 w-full bg-gradient-to-r from-[#D92525] via-[#F2B544] to-[#23856D]"></div>

      {/* Vista Activa */}
      <main className="flex-1">
        {currentView === 'citizen' ? (
          <CitizenPortal onOpenTracker={() => setTrackerOpen(true)} />
        ) : (
          <AdminDashboard />
        )}
      </main>

      {/* Modal de Consulta Rápida de Radicados */}
      <CaseTrackerModal
        isOpen={trackerOpen}
        onClose={() => setTrackerOpen(false)}
      />

      {/* Pie de Página Institucional */}
      <footer className="bg-[#102A43] text-white py-8 border-t border-slate-700/60 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-slate-300">
            
            {/* Información Institucional */}
            <div className="space-y-1.5 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start space-x-2">
                <span className="font-bold text-white text-sm">
                  Alcaldía Distrital de Barranquilla
                </span>
                <span className="text-[#F2B544] font-semibold text-xs">
                  • Distrito Especial, Industrial y Portuario
                </span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Sede Central Paseo Bolívar: Calle 34 No. 43-31 | PBX: (605) 370 3300 | Línea de Atención Distrital: 195
              </p>
              <p className="text-slate-400 text-[11px]">
                Horario de Ventanilla Presencial: Lunes a Viernes de 7:00 a.m. a 12:00 m. y de 1:00 p.m. a 5:00 p.m.
              </p>
            </div>

            {/* Garantía Legal y Canales */}
            <div className="flex flex-col items-center md:items-end text-center md:text-right space-y-2">
              <div className="inline-flex items-center space-x-2 bg-white/10 px-3 py-1.5 rounded-full border border-white/15">
                <span className="w-2 h-2 rounded-full bg-[#23856D]"></span>
                <span className="text-white font-semibold text-[11px]">
                  Ventanilla Digital Certificada • Atención 24/7
                </span>
              </div>
              <p className="text-[11px] text-slate-400 max-w-md">
                Trámites y derechos de petición respaldados bajo la Ley 1755 de 2015 y CPACA. Toda radicación cuenta con comprobante digital verificable.
              </p>
            </div>

          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 gap-2">
            <span>© 2026 Alcaldía Distrital de Barranquilla. Todos los derechos reservados.</span>
            <span>Barranquilla, Atlántico — Colombia</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
