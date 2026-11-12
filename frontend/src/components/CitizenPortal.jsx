import React, { useState, useRef, useEffect } from 'react';
import {
  Send, Bot, User, BookOpen, ExternalLink, CheckCircle2, AlertCircle,
  Clock, ShieldAlert, Sparkles, ChevronRight, RefreshCw, FileCheck, Printer,
  HelpCircle, MessageSquare
} from 'lucide-react';
import ComprobanteModal from './ComprobanteModal';

// Formateador limpio y profesional para las respuestas de la IA
function FormattedMessage({ content, isUser }) {
  if (!content) return null;
  if (isUser) {
    return <p className="leading-relaxed whitespace-pre-wrap">{content}</p>;
  }

  // 1. Limpieza de cualquier residuo de símbolos markdown
  const cleaned = content
    .replace(/^[ \t]*#{1,6}[ \t]*/gm, '')
    .replace(/^[ \t]*[-*_]{3,}[ \t]*$/gm, '')
    .replace(/^[ \t]*>[ \t]*/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/`(.*?)`/g, '$1')
    .replace(/```/g, '');

  // 2. Separar por bloques de párrafos
  const paragraphs = cleaned.split(/\n\n+/);

  return (
    <div className="space-y-3 text-slate-800 text-xs sm:text-sm leading-relaxed">
      {paragraphs.map((para, pIdx) => {
        const lines = para.split('\n').filter(l => l.trim().length > 0);
        if (lines.length === 0) return null;

        // Comprobar si todas las líneas son viñetas
        const isAllBullets = lines.every(l => l.trim().startsWith('•') || l.trim().startsWith('-') || l.trim().startsWith('*'));
        // Comprobar si todas las líneas son pasos numerados
        const isAllNumbered = lines.every(l => /^\d+[\.\)]\s/.test(l.trim()));

        if (isAllBullets) {
          return (
            <div key={pIdx} className="space-y-1.5 pl-1 my-2">
              {lines.map((line, lIdx) => {
                const text = line.replace(/^[•\-*]\s*/, '').trim();
                const colonIdx = text.indexOf(':');
                if (colonIdx > 0 && colonIdx < 40) {
                  const label = text.substring(0, colonIdx);
                  const val = text.substring(colonIdx + 1);
                  return (
                    <div key={lIdx} className="flex items-start gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#1769AA] shrink-0 mt-2"></span>
                      <div>
                        <span className="font-bold text-[#102A43]">{label}:</span>
                        <span className="text-slate-700 ml-1.5">{val}</span>
                      </div>
                    </div>
                  );
                }
                return (
                  <div key={lIdx} className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1769AA] shrink-0 mt-2"></span>
                    <span className="text-slate-700">{text}</span>
                  </div>
                );
              })}
            </div>
          );
        }

        if (isAllNumbered) {
          return (
            <div key={pIdx} className="space-y-2 my-2">
              {lines.map((line, lIdx) => {
                const match = line.trim().match(/^(\d+)[\.\)]\s*(.*)$/);
                const num = match ? match[1] : (lIdx + 1);
                const stepText = match ? match[2] : line;
                return (
                  <div key={lIdx} className="flex items-start gap-3 bg-blue-50/50 p-3 rounded-2xl border border-blue-100/70">
                    <span className="w-5 h-5 rounded-full bg-[#102A43] text-white font-bold text-[11px] flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                      {num}
                    </span>
                    <span className="text-slate-700 font-medium">{stepText}</span>
                  </div>
                );
              })}
            </div>
          );
        }

        // Párrafo mixto o con encabezados suaves
        return (
          <div key={pIdx} className="space-y-1.5">
            {lines.map((line, lIdx) => {
              const trimmed = line.trim();

              // Viñeta individual dentro de párrafo
              if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
                const text = trimmed.replace(/^[•\-*]\s*/, '').trim();
                const colonIdx = text.indexOf(':');
                if (colonIdx > 0 && colonIdx < 40) {
                  const label = text.substring(0, colonIdx);
                  const val = text.substring(colonIdx + 1);
                  return (
                    <div key={lIdx} className="flex items-start gap-2.5 pl-1 my-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#1769AA] shrink-0 mt-2"></span>
                      <div>
                        <span className="font-bold text-[#102A43]">{label}:</span>
                        <span className="text-slate-700 ml-1.5">{val}</span>
                      </div>
                    </div>
                  );
                }
                return (
                  <div key={lIdx} className="flex items-start gap-2.5 pl-1 my-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1769AA] shrink-0 mt-2"></span>
                    <span className="text-slate-700">{text}</span>
                  </div>
                );
              }

              // Paso numerado individual
              const numMatch = trimmed.match(/^(\d+)[\.\)]\s*(.*)$/);
              if (numMatch) {
                return (
                  <div key={lIdx} className="flex items-start gap-3 bg-blue-50/50 p-2.5 rounded-2xl border border-blue-100/70 my-1">
                    <span className="w-5 h-5 rounded-full bg-[#102A43] text-white font-bold text-[11px] flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                      {numMatch[1]}
                    </span>
                    <span className="text-slate-700 font-medium">{numMatch[2]}</span>
                  </div>
                );
              }

              // Encabezado de sección
              const isHeader = (trimmed.endsWith(':') && trimmed.length < 65) ||
                               trimmed.toLowerCase().includes('solicitud radicada') ||
                               trimmed.toLowerCase().includes('estado oficial') ||
                               trimmed.toLowerCase().includes('revisión especial') ||
                               trimmed.toLowerCase().includes('próximos pasos') ||
                               trimmed.toLowerCase().includes('trámites y servicios');
              if (isHeader) {
                return (
                  <div key={lIdx} className="font-bold text-[#102A43] text-xs uppercase tracking-wider pt-2 pb-1 flex items-center gap-2 border-b border-slate-100">
                    <span className="w-2 h-2 rounded-full bg-[#20A4C8]"></span>
                    <span>{trimmed.replace(/:$/, '')}</span>
                  </div>
                );
              }

              // Destacado para Radicado o Código
              const radMatch = trimmed.match(/^([A-Za-zÁ-ú\s]+):\s*(BQL-\d{4}-\d+|[A-Z0-9]{8,14})/);
              if (radMatch) {
                return (
                  <div key={lIdx} className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-xl my-1">
                    <span className="text-xs font-bold text-[#102A43]">{radMatch[1]}:</span>
                    <span className="font-mono font-bold text-[#1769AA] text-sm">{radMatch[2]}</span>
                  </div>
                );
              }

              // Párrafo estándar
              return (
                <p key={lIdx} className="text-slate-700 leading-relaxed">
                  {trimmed}
                </p>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

export default function CitizenPortal({ onOpenTracker }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '¡Hola! Te damos la bienvenida a la Ventanilla Virtual de la Alcaldía Distrital de Barranquilla.\n\nEstoy aquí para orientarte sobre trámites distritales, ayudarte a reportar averías en alumbrado público, conocer los descuentos del impuesto predial 2026, consultar requisitos del Sisbén IV o radicar quejas de espacio público y salud ambiental.\n\n¿En qué podemos servirte hoy?',
      thoughts: [],
      citations: [],
      status: 'SUCCESS'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeThoughts, setActiveThoughts] = useState([]);
  const [activeSidebarTab, setActiveSidebarTab] = useState('faq'); // 'faq' | 'thoughts'
  const [comprobanteData, setComprobanteData] = useState(null);
  const [comprobanteOpen, setComprobanteOpen] = useState(false);
  const chatEndRef = useRef(null);

  // Lista de 6 Preguntas Frecuentes institucionales oficiales
  const faqList = [
    {
      icon: "💰",
      category: "Hacienda Distrital",
      title: "Descuentos Predial 2026",
      desc: "Fechas y porcentajes de pronto pago",
      prompt: "¿Cuáles son las fechas y porcentajes de descuento por pronto pago del Impuesto Predial Unificado 2026 en Barranquilla?"
    },
    {
      icon: "📋",
      category: "Gestión Social",
      title: "Requisitos Sisbén IV",
      desc: "Documentos para nueva encuesta",
      prompt: "¿Qué documentos y requisitos necesito para solicitar una nueva encuesta del Sisbén IV en Barranquilla?"
    },
    {
      icon: "📄",
      category: "Hacienda Distrital",
      title: "Paz y Salvo Predial",
      desc: "Cómo descargarlo por internet",
      prompt: "¿Cómo consultar y descargar el certificado de Paz y Salvo del Impuesto Predial Unificado en línea?"
    },
    {
      icon: "💡",
      category: "Alumbrado K-YENA",
      title: "Luminarias y Alumbrado",
      desc: "Canales y pasos para reporte",
      prompt: "¿Qué procedimiento y canales existen para reportar una luminaria o falla de alumbrado público a K-YENA?"
    },
    {
      icon: "⚠️",
      category: "Control Urbano",
      title: "Invasión de Andenes",
      desc: "Normas y denuncias de espacio público",
      prompt: "¿Cuáles son las normas y cómo denunciar la invasión indebida de andenes peatonales y espacio público?"
    },
    {
      icon: "🦟",
      category: "Salud Pública",
      title: "Prevención de Dengue",
      desc: "Inspección comunitaria y control",
      prompt: "¿Cómo solicitar inspección sanitaria y control de criaderos del mosquito del dengue en mi barrio?"
    }
  ];

  // Trámites rápidos para radicación directa
  const filingPrompts = [
    {
      title: "💡 Radicar Luminaria Apagada",
      desc: "Alumbrado Público / K-YENA",
      prompt: "Quiero reportar que la luminaria frente a la Carrera 53 # 79-112 en el barrio Alto Prado está apagada. Mi celular es 3004567890."
    },
    {
      title: "⚠️ Radicar Denuncia Espacio Público",
      desc: "Control Urbano / Andenes",
      prompt: "Denuncio que un taller mecánico colocó escombros y carros dañados sobre todo el andén peatonal en la Calle 45 # 21B-40 en San José impidiendo el paso."
    }
  ];

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, activeThoughts, loading]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || loading) return;

    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setLoading(true);
    setActiveThoughts([
      { step_name: 'Recepción', action: 'Iniciando Atención', detail: 'Recibiendo requerimiento en la ventanilla virtual...', status: 'RUNNING', timestamp: 'En proceso' }
    ]);
    setActiveSidebarTab('thoughts'); // Mostrar pasos de trámite mientras procesa

    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: 'citizen-session-web'
        })
      });

      if (!res.ok) {
        throw new Error('Error en el servicio de atención.');
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
          thoughts: data.thoughts || [],
          citations: data.citations || [],
          case_result: data.case_result,
          status: data.status,
          requires_human_approval: data.requires_human_approval
        }
      ]);
      setActiveThoughts(data.thoughts || []);

      // Si se generó un nuevo radicado, preparar el comprobante y sincronizar con la consola en tiempo real
      if (data.case_result && data.case_result.radicado) {
        setComprobanteData(data.case_result);
        window.dispatchEvent(new CustomEvent('bql_case_created', { detail: data.case_result }));
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Ocurrió un inconveniente temporal en la comunicación con el servidor institucional. Por favor intenta nuevamente en unos momentos.',
          status: 'ERROR'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Columna Principal del Chat (8 cols) */}
        <div className="lg:col-span-8 flex flex-col h-[78vh] bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
          
          {/* Banner Superior Institucional */}
          <div className="px-6 py-3.5 bg-[#F2F6FA] border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <div className="flex items-center space-x-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#23856D] animate-pulse"></span>
              <span className="font-bold text-[#102A43]">Ventanilla Virtual de Atención al Ciudadano</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-500 font-medium">Alcaldía de Barranquilla</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setActiveSidebarTab('faq')}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition ${
                  activeSidebarTab === 'faq' ? 'bg-[#1769AA] text-white' : 'text-slate-600 hover:text-[#102A43]'
                }`}
              >
                Preguntas Frecuentes
              </button>
              <button
                onClick={() => setActiveSidebarTab('thoughts')}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition ${
                  activeSidebarTab === 'thoughts' ? 'bg-[#1769AA] text-white' : 'text-slate-600 hover:text-[#102A43]'
                }`}
              >
                Pasos de Trámite
              </button>
            </div>
          </div>

          {/* Área de Mensajes */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-white">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-9 h-9 rounded-xl bg-[#102A43] text-white flex items-center justify-center shrink-0 mt-1 shadow-sm">
                    <Bot className="w-5 h-5 text-[#20A4C8]" />
                  </div>
                )}

                <div className={`max-w-[85%] rounded-3xl p-5 text-sm leading-relaxed shadow-xs ${
                  msg.role === 'user'
                    ? 'bg-[#1769AA] text-white rounded-br-xs'
                    : 'bg-[#F2F6FA] text-[#243746] border border-slate-200/70 rounded-bl-xs'
                }`}>
                  {/* Formateador Limpio de Respuestas */}
                  <FormattedMessage content={msg.content} isUser={msg.role === 'user'} />

                  {/* Tarjetas Visuales de Fuentes Oficiales */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3.5 border-t border-slate-200/80">
                      <p className="text-xs font-bold text-slate-700 flex items-center space-x-1.5 mb-2.5">
                        <BookOpen className="w-4 h-4 text-[#1769AA]" />
                        <span>Fundamentación Institucional Verificada:</span>
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {msg.citations.map((c, i) => (
                          <div
                            key={i}
                            className="bg-white p-3 rounded-2xl border border-slate-200 text-xs shadow-xs hover:border-[#1769AA] transition"
                          >
                            <p className="font-bold text-slate-900 line-clamp-1">{c.title}</p>
                            <p className="text-[11px] text-slate-500 mt-0.5">{c.article_reference}</p>
                            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-[10px]">
                              <span className="text-slate-500 font-medium">{c.authority}</span>
                              {c.source_url && (
                                <a
                                  href={c.source_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-[#1769AA] font-bold flex items-center gap-1 hover:underline"
                                >
                                  <span>Portal distrital</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Acciones para Solicitudes Radicadas */}
                  {msg.case_result && msg.case_result.radicado && (
                    <div className="mt-4 p-4 bg-white rounded-2xl border border-blue-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase block font-semibold">Número de Radicado Oficial</span>
                        <span className="text-base font-mono font-bold text-[#1769AA]">{msg.case_result.radicado}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            setComprobanteData(msg.case_result);
                            setComprobanteOpen(true);
                          }}
                          className="px-3 py-2 bg-[#23856D] hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition flex items-center space-x-1.5 shadow-xs"
                        >
                          <Printer className="w-3.5 h-3.5" />
                          <span>Descargar Comprobante</span>
                        </button>
                        <button
                          onClick={onOpenTracker}
                          className="px-3 py-2 bg-[#1769AA] hover:bg-[#102A43] text-white text-xs font-bold rounded-xl transition flex items-center space-x-1 shadow-xs"
                        >
                          <span>Seguimiento</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-9 h-9 rounded-xl bg-[#20A4C8] text-white flex items-center justify-center shrink-0 mt-1 shadow-sm">
                    <User className="w-5 h-5" />
                  </div>
                )}
              </div>
            ))}

            {/* Spinner de Carga Institucional */}
            {loading && (
              <div className="flex items-center space-x-3 text-slate-600 text-xs p-3.5 bg-slate-50 rounded-2xl w-fit border border-slate-200 shadow-xs">
                <RefreshCw className="w-4 h-4 text-[#1769AA] animate-spin" />
                <span>Consultando normatividad oficial y organizando respuesta institucional...</span>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Formulario de Entrada */}
          <div className="p-4 bg-white border-t border-slate-200">
            {/* Accesos Rápidos Frecuentes (1 Clic) */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2.5 mb-1 text-xs">
              <span className="text-[11px] font-bold text-slate-500 shrink-0">Preguntas Frecuentes:</span>
              <button
                type="button"
                onClick={() => handleSendMessage("¿Cuáles son las fechas y porcentajes de descuento por pronto pago del Impuesto Predial Unificado 2026 en Barranquilla?")}
                disabled={loading}
                className="shrink-0 bg-blue-50 hover:bg-blue-100 text-[#1769AA] px-3 py-1 rounded-full font-semibold transition border border-blue-200 text-[11px]"
              >
                💰 Descuentos Predial 10%
              </button>
              <button
                type="button"
                onClick={() => handleSendMessage("¿Qué documentos y requisitos necesito para solicitar una nueva encuesta del Sisbén IV en Barranquilla?")}
                disabled={loading}
                className="shrink-0 bg-blue-50 hover:bg-blue-100 text-[#1769AA] px-3 py-1 rounded-full font-semibold transition border border-blue-200 text-[11px]"
              >
                📋 Requisitos Sisbén IV
              </button>
              <button
                type="button"
                onClick={() => handleSendMessage("¿Cómo consultar y descargar el certificado de Paz y Salvo del Impuesto Predial Unificado en línea?")}
                disabled={loading}
                className="shrink-0 bg-blue-50 hover:bg-blue-100 text-[#1769AA] px-3 py-1 rounded-full font-semibold transition border border-blue-200 text-[11px]"
              >
                📄 Paz y Salvo en línea
              </button>
              <button
                type="button"
                onClick={() => handleSendMessage("Quiero reportar que la luminaria frente a la Carrera 53 # 79-112 en Alto Prado está apagada. Mi celular es 3004567890.")}
                disabled={loading}
                className="shrink-0 bg-emerald-50 hover:bg-emerald-100 text-[#23856D] px-3 py-1 rounded-full font-semibold transition border border-emerald-200 text-[11px]"
              >
                💡 Reportar Alumbrado
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                placeholder="Escribe tu consulta distrital, solicitud o reporte en Barranquilla..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={loading}
                className="flex-1 px-4 py-3.5 rounded-2xl border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-[#1769AA] text-sm bg-[#F2F6FA]/60 text-slate-800 placeholder-slate-400"
              />
              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="bg-[#1769AA] hover:bg-[#102A43] text-white px-6 py-3.5 rounded-2xl font-bold transition flex items-center space-x-2 disabled:opacity-50 shadow-xs shrink-0"
              >
                <span>Enviar</span>
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>

        </div>

        {/* Columna Lateral: FAQs, Pasos de Atención y Accesos Rápidos (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Panel con Pestañas: FAQ vs Pasos de Atención */}
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                {activeSidebarTab === 'faq' ? (
                  <HelpCircle className="w-4 h-4 text-[#1769AA]" />
                ) : (
                  <Sparkles className="w-4 h-4 text-[#20A4C8]" />
                )}
                <h3 className="font-bold text-sm text-[#102A43]">
                  {activeSidebarTab === 'faq' ? 'Preguntas Frecuentes (FAQ)' : 'Pasos de Atención Oficial'}
                </h3>
              </div>
              <span className="text-[10px] bg-blue-50 text-[#1769AA] px-2.5 py-0.5 rounded-full font-bold">
                {activeSidebarTab === 'faq' ? '1 Clic' : 'En Vivo'}
              </span>
            </div>

            {/* Vista 1: Preguntas Frecuentes (FAQ) */}
            {activeSidebarTab === 'faq' && (
              <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
                {faqList.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(item.prompt)}
                    disabled={loading}
                    className="w-full text-left p-3 rounded-2xl border border-slate-100 hover:border-[#1769AA] hover:bg-blue-50/50 transition group flex items-start gap-2.5"
                  >
                    <span className="text-base shrink-0 mt-0.5">{item.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-slate-800 group-hover:text-[#1769AA] truncate">
                          {item.title}
                        </span>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-[#1769AA] transition shrink-0 ml-1" />
                      </div>
                      <span className="text-[11px] text-slate-500 block truncate mt-0.5">{item.desc}</span>
                      <span className="text-[10px] text-[#1769AA] font-semibold block mt-1">{item.category}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Vista 2: Pasos de Atención en Vivo */}
            {activeSidebarTab === 'thoughts' && (
              <div>
                {activeThoughts.length === 0 ? (
                  <div className="text-center py-6 text-slate-400 text-xs">
                    <Bot className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                    <p>Envía tu consulta o haz clic en una pregunta frecuente para ver el razonamiento en vivo.</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
                    {activeThoughts.map((t, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-slate-50 border border-slate-200 text-xs transition hover:bg-white"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-slate-800 flex items-center gap-1.5">
                            {t.status === 'RUNNING' && <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>}
                            {t.status === 'WARNING' && <span className="w-2 h-2 rounded-full bg-amber-500"></span>}
                            {t.status === 'COMPLETED' && <span className="w-2 h-2 rounded-full bg-[#23856D]"></span>}
                            {t.step_name}
                          </span>
                          <span className="text-[10px] text-slate-400 font-medium">{t.timestamp}</span>
                        </div>
                        <p className="font-semibold text-[#1769AA] text-[11px] mb-0.5">{t.action}</p>
                        <p className="text-slate-600 text-[11px] leading-relaxed">{t.detail}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Trámites de Radicación Rápida en Terreno */}
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
            <h3 className="font-bold text-sm text-[#102A43] mb-4 pb-2 border-b border-slate-100 flex items-center space-x-2">
              <FileCheck className="w-4 h-4 text-[#1769AA]" />
              <span>Radicar Solicitud Directa</span>
            </h3>
            <div className="space-y-2">
              {filingPrompts.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(item.prompt)}
                  disabled={loading}
                  className="w-full text-left p-3.5 rounded-2xl border border-slate-100 hover:border-[#1769AA] hover:bg-blue-50/50 transition group"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-800 group-hover:text-[#1769AA]">
                      {item.title}
                    </span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-[#1769AA] transition" />
                  </div>
                  <span className="text-[11px] text-slate-500 block mt-0.5">{item.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Garantía Institucional y Canales Oficiales */}
          <div className="bg-gradient-to-br from-[#102A43] to-[#1769AA] text-white rounded-3xl p-5 shadow-sm text-xs">
            <div className="flex items-center space-x-2 mb-2">
              <ShieldAlert className="w-4 h-4 text-[#F2B544]" />
              <span className="font-bold">Garantía de Atención Ciudadana</span>
            </div>
            <p className="text-blue-100 leading-relaxed text-[11px]">
              Toda solicitud radicada cuenta con número único de seguimiento y términos de respuesta respaldados por la Ley 1755 de 2015. Atención telefónica gratuita marcando al 195.
            </p>
          </div>

        </div>

      </div>

      {/* Modal de Comprobante Imprimible */}
      <ComprobanteModal
        isOpen={comprobanteOpen}
        onClose={() => setComprobanteOpen(false)}
        data={comprobanteData}
      />
    </div>
  );
}
