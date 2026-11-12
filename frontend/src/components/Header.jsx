import React from 'react';
import { Building2, User, LayoutDashboard, Search, CheckCircle2, PhoneCall } from 'lucide-react';

export default function Header({ currentView, setCurrentView, onOpenTracker }) {
  return (
    <header className="bg-[#102A43] text-white shadow-md sticky top-0 z-40 border-b border-[#20A4C8]/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo y Membrete Oficial */}
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#1769AA] to-[#20A4C8] flex items-center justify-center shadow-lg border border-white/25 shrink-0">
              <Building2 className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] uppercase tracking-wider font-bold text-[#F2B544]">
                  Distrito de Barranquilla
                </span>
                <span className="bg-[#23856D]/30 text-[#68D391] text-[10px] font-bold px-2 py-0.5 rounded-full border border-[#23856D]/50 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#68D391] animate-pulse"></span>
                  Canal Oficial
                </span>
              </div>
              <h1 className="text-lg sm:text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Alcaldía Distrital
                <span className="text-xs sm:text-sm font-normal text-blue-200 hidden sm:inline">
                  | Ventanilla Virtual Ciudadana
                </span>
              </h1>
            </div>
          </div>

          {/* Acciones y Switch de Vistas */}
          <div className="flex items-center space-x-3">
            {/* Botón de Consulta de Radicado */}
            <button
              onClick={onOpenTracker}
              className="hidden md:flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white/10 hover:bg-white/20 text-white transition border border-white/10 shadow-xs"
              title="Consultar número de radicado distrital"
            >
              <Search className="w-4 h-4 text-[#20A4C8]" />
              <span>Consultar Radicado</span>
            </button>

            {/* Selector de Vistas: Ciudadano vs Consola Administrativa */}
            <div className="bg-[#0b1c2e] p-1 rounded-2xl flex items-center border border-white/10 shadow-inner">
              <button
                onClick={() => setCurrentView('citizen')}
                className={`flex items-center space-x-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-semibold transition ${
                  currentView === 'citizen'
                    ? 'bg-[#1769AA] text-white shadow-sm'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                <User className="w-4 h-4" />
                <span>Portal Ciudadano</span>
              </button>

              <button
                onClick={() => setCurrentView('admin')}
                className={`flex items-center space-x-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-semibold transition ${
                  currentView === 'admin'
                    ? 'bg-[#1769AA] text-white shadow-sm'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span className="hidden sm:inline">Consola Distrital</span>
                <span className="sm:hidden">Gestión</span>
              </button>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
}
