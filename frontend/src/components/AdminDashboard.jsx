import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard, Inbox, BookOpen, ShieldCheck, AlertTriangle, CheckCircle,
  Clock, ArrowUpRight, Filter, Search, Eye, Check, RefreshCw, X, ChevronRight,
  FileText, Database, Download, CloudUpload, ArrowRight, Layers, ExternalLink, Table, Terminal
} from 'lucide-react';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('cases'); // 'cases', 'snowflake', 'rag', 'audit'
  const [metrics, setMetrics] = useState(null);
  const [cases, setCases] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCase, setSelectedCase] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [overrideDept, setOverrideDept] = useState('');

  // Snowflake State
  const [snowflakeStatus, setSnowflakeStatus] = useState(null);
  const [sfSchema, setSfSchema] = useState(null);
  const [sfAccount, setSfAccount] = useState('');
  const [sfUser, setSfUser] = useState('');
  const [sfPassword, setSfPassword] = useState('');
  const [sfWarehouse, setSfWarehouse] = useState('COMPUTE_WH');
  const [sfDatabase, setSfDatabase] = useState('BARRANQUILLA_CITIZEN_DB');
  const [sfTesting, setSfTesting] = useState(false);
  const [sfSyncing, setSfSyncing] = useState(false);
  const [sfMessage, setSfMessage] = useState(null);
  const [lastSyncedAt, setLastSyncedAt] = useState(new Date());

  const fetchDashboardData = async (showLoadingSpinner = true) => {
    if (showLoadingSpinner) setLoading(true);
    try {
      const [metricsRes, casesRes, docsRes, sfRes, sfSchemaRes] = await Promise.all([
        fetch('/api/analytics/dashboard'),
        fetch(`/api/cases/?status=${statusFilter}&search=${searchQuery}`),
        fetch('/api/knowledge/documents'),
        fetch('/api/snowflake/status'),
        fetch('/api/snowflake/schema_preview')
      ]);

      if (metricsRes.ok) setMetrics(await metricsRes.json());
      if (casesRes.ok) {
        const cData = await casesRes.json();
        setCases(cData.cases || []);
      }
      if (docsRes.ok) {
        const dData = await docsRes.json();
        setDocuments(dData.documents || []);
      }
      if (sfRes.ok) {
        const sfData = await sfRes.json();
        setSnowflakeStatus(sfData);
        if (sfData.account && sfData.account !== "No configurada") setSfAccount(sfData.account);
        if (sfData.user && sfData.user !== "No configurado") setSfUser(sfData.user);
      }
      if (sfSchemaRes.ok) {
        const schemaData = await sfSchemaRes.json();
        setSfSchema(schemaData);
      }
      setLastSyncedAt(new Date());
    } catch (err) {
      console.error("Error fetching admin dashboard data:", err);
    } finally {
      if (showLoadingSpinner) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData(true);

    // Sincronización continua en tiempo real cada 4 segundos
    const intervalId = setInterval(() => {
      fetchDashboardData(false);
    }, 4000);

    // Escuchar creación inmediata de casos desde el portal ciudadano
    const handleCaseCreated = () => {
      fetchDashboardData(false);
    };
    window.addEventListener('bql_case_created', handleCaseCreated);

    const handleFocus = () => {
      fetchDashboardData(false);
    };
    window.addEventListener('focus', handleFocus);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('bql_case_created', handleCaseCreated);
      window.removeEventListener('focus', handleFocus);
    };
  }, [statusFilter, searchQuery]);

  const openCaseDetail = async (caseId) => {
    try {
      const res = await fetch(`/api/cases/${caseId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedCase(data);
      }
    } catch (err) {
      console.error("Error loading case detail:", err);
    }
  };

  const handleApproveClassification = async (caseId, overrideCode = null) => {
    setActionLoading(true);
    try {
      const res = await fetch(`/api/cases/${caseId}/approve_classification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          officer_id: 'OFICIAL_SUPERVISOR_BQL',
          override_department_code: overrideCode || null,
          notes: overrideCode ? 'Dependencia reclasificada formalmente por funcionario.' : 'Clasificación sugerida por el sistema avalada formalmente.'
        })
      });
      if (res.ok) {
        window.dispatchEvent(new CustomEvent('bql_case_updated', { detail: { caseId, overrideCode } }));
        await fetchDashboardData(false);
        await openCaseDetail(caseId);
      }
    } catch (err) {
      console.error("Error approving classification:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateStatus = async (caseId, newStatus) => {
    setActionLoading(true);
    try {
      const res = await fetch(`/api/cases/${caseId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_status: newStatus,
          officer_id: 'OFICIAL_SUPERVISOR_BQL',
          notes: `Cambio de estado administrativo a ${newStatus}`
        })
      });
      if (res.ok) {
        window.dispatchEvent(new CustomEvent('bql_case_updated', { detail: { caseId, overrideCode } }));
        await fetchDashboardData(false);
        await openCaseDetail(caseId);
      }
    } catch (err) {
      console.error("Error updating status:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTestSnowflake = async (e) => {
    e.preventDefault();
    setSfTesting(true);
    setSfMessage(null);
    try {
      const res = await fetch('/api/snowflake/test_connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account: sfAccount,
          user: sfUser,
          password: sfPassword,
          warehouse: sfWarehouse,
          database: sfDatabase
        })
      });
      const data = await res.json();
      setSfMessage(data);
      if (data.success) {
        fetchDashboardData();
      }
    } catch (err) {
      setSfMessage({ success: false, message: 'No se pudo conectar con el servidor de base de datos.' });
    } finally {
      setSfTesting(false);
    }
  };

  const handleSyncSnowflake = async () => {
    setSfSyncing(true);
    setSfMessage(null);
    try {
      const res = await fetch('/api/snowflake/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      setSfMessage(data);
    } catch (err) {
      setSfMessage({ success: false, message: 'Error durante la sincronización a Snowflake.' });
    } finally {
      setSfSyncing(false);
    }
  };

  const handleExportCSV = () => {
    if (cases.length === 0) return;
    const headers = ["Radicado", "Ciudadano", "Telefono", "Barrio", "Categoria", "Dependencia", "Prioridad", "Estado", "Vencimiento"];
    const rows = cases.map(c => [
      c.radicado,
      `"${c.citizen_name || 'Anonimo'}"`,
      `"${c.citizen_phone || ''}"`,
      `"${c.neighborhood || ''}"`,
      `"${c.category}"`,
      `"${c.assigned_to}"`,
      c.priority,
      c.status,
      c.sla_due_date || 'N/A'
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Reporte_Gestion_Ciudadana_Barranquilla_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const kpis = metrics?.kpis || {
    total_cases: 0,
    pending_review: 0,
    in_gestion: 0,
    escalated_human: 0,
    resolved: 0,
    sla_at_risk: 0
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      
      {/* Encabezado Principal y Pestañas */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs uppercase font-bold text-[#1769AA] tracking-wider">Consola Institucional</span>
            <span className="bg-blue-100 text-[#1769AA] text-[10px] font-bold px-2.5 py-0.5 rounded-full">
              Rol: Funcionario / Supervisor
            </span>
            <div className="flex items-center space-x-1.5 bg-emerald-50 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200 text-[10px] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Sincronizado en tiempo real</span>
            </div>
          </div>
          <h2 className="text-xl font-bold text-[#102A43] mt-0.5">Control y Gestión de Solicitudes Distritales</h2>
          <div className="flex items-center space-x-2 mt-1 text-[11px] text-slate-500">
            <span>Última actualización: {lastSyncedAt.toLocaleTimeString('es-CO')}</span>
            <span>•</span>
            <button
              onClick={() => fetchDashboardData(true)}
              disabled={loading}
              className="text-[#1769AA] hover:text-[#102A43] font-bold inline-flex items-center gap-1 hover:underline"
              title="Actualizar datos ahora"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
              <span>Actualizar ahora</span>
            </button>
          </div>
        </div>

        {/* Tabs de Navegación */}
        <div className="flex flex-wrap items-center gap-1 bg-[#F2F6FA] p-1.5 rounded-2xl border border-slate-200">
          <button
            onClick={() => setActiveTab('cases')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              activeTab === 'cases' ? 'bg-[#1769AA] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Inbox className="w-4 h-4" />
            <span>Bandeja de Solicitudes ({cases.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('snowflake')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              activeTab === 'snowflake' ? 'bg-[#1769AA] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Conexión Snowflake</span>
          </button>
          <button
            onClick={() => setActiveTab('rag')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              activeTab === 'rag' ? 'bg-[#1769AA] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Biblioteca Normativa ({documents.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              activeTab === 'audit' ? 'bg-[#1769AA] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Historial de Actuaciones</span>
          </button>
        </div>
      </div>

      {/* Tarjetas de Indicadores Institucionales */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase block">Total Solicitudes</span>
          <span className="text-2xl font-bold text-[#102A43] mt-1 block">{kpis.total_cases}</span>
          <span className="text-[10px] text-slate-500 font-medium block mt-1">Registradas en sistema</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase block">Pendientes</span>
          <span className="text-2xl font-bold text-amber-600 mt-1 block">{kpis.pending_review}</span>
          <span className="text-[10px] text-slate-500 font-medium block mt-1">En espera de gestión</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase block">En Trámite</span>
          <span className="text-2xl font-bold text-[#1769AA] mt-1 block">{kpis.in_gestion}</span>
          <span className="text-[10px] text-slate-500 font-medium block mt-1">En cuadrilla / despacho</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase block">Revisión Funcionario</span>
          <span className="text-2xl font-bold text-rose-600 mt-1 block">{kpis.escalated_human}</span>
          <span className="text-[10px] text-slate-500 font-medium block mt-1">Asignadas a evaluación</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase block">Alertas de Plazo</span>
          <span className={`text-2xl font-bold mt-1 block ${kpis.sla_at_risk > 0 ? 'text-[#B54747]' : 'text-emerald-600'}`}>
            {kpis.sla_at_risk}
          </span>
          <span className="text-[10px] text-slate-500 font-medium block mt-1">≤ 48h para límite legal</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase block">Efectividad Global</span>
          <span className="text-2xl font-bold text-[#23856D] mt-1 block">98.4%</span>
          <span className="text-[10px] text-slate-500 font-medium block mt-1">Cumplimiento de términos</span>
        </div>
      </div>

      {/* Alerta de Plazos si existen solicitudes prioritarias */}
      {metrics?.sla_at_risk_list && metrics.sla_at_risk_list.length > 0 && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-3 text-amber-900 text-xs">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <div>
              <span className="font-bold">Atención prioritaria de términos legales: </span>
              <span>{metrics.sla_at_risk_list.length} solicitudes requieren pronta respuesta antes de su vencimiento legal según la Ley 1755.</span>
            </div>
          </div>
          <button
            onClick={() => setStatusFilter('EN_GESTION')}
            className="text-xs font-bold text-amber-900 underline hover:text-black"
          >
            Filtrar casos
          </button>
        </div>
      )}

      {/* PESTAÑA 1: BANDEJA DE SOLICITUDES */}
      {activeTab === 'cases' && (
        <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
          
          {/* Barra de Filtros y Exportación */}
          <div className="p-5 bg-[#F2F6FA] border-b border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-72">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  placeholder="Buscar por radicado, ciudadano, barrio..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-xs bg-white focus:outline-hidden focus:ring-2 focus:ring-[#1769AA]"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs bg-white text-slate-700 font-semibold"
              >
                <option value="">Todos los Estados</option>
                <option value="RADICADO_SIMULADO">Radicado</option>
                <option value="PENDIENTE_REVISION">Pendiente</option>
                <option value="EN_GESTION">En Trámite</option>
                <option value="ESCALADO_HUMANO">Revisión Funcionario</option>
                <option value="RESUELTO">Resuelto</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleExportCSV}
                className="px-3.5 py-2.5 bg-white border border-slate-300 hover:border-[#1769AA] text-slate-700 font-bold rounded-xl text-xs transition flex items-center space-x-1.5 shadow-xs"
              >
                <Download className="w-4 h-4 text-[#1769AA]" />
                <span>Exportar Reporte</span>
              </button>
              <button
                onClick={fetchDashboardData}
                className="px-3.5 py-2.5 bg-[#1769AA] text-white font-bold rounded-xl text-xs hover:bg-[#102A43] transition flex items-center space-x-1.5 shadow-xs"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Actualizar</span>
              </button>
            </div>
          </div>

          {/* Tabla de Solicitudes */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-bold border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-5">Radicado</th>
                  <th className="py-3.5 px-5">Ciudadano</th>
                  <th className="py-3.5 px-5">Asunto / Categoría</th>
                  <th className="py-3.5 px-5">Dependencia Asignada</th>
                  <th className="py-3.5 px-5">Prioridad</th>
                  <th className="py-3.5 px-5">Estado</th>
                  <th className="py-3.5 px-5">Plazo Límite</th>
                  <th className="py-3.5 px-5 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {cases.map((c) => (
                  <tr key={c.id} className="hover:bg-blue-50/40 transition">
                    <td className="py-3.5 px-5 font-mono font-bold text-[#1769AA]">
                      {c.radicado}
                    </td>
                    <td className="py-3.5 px-5">
                      <p className="font-bold text-slate-900">{c.citizen_name || 'Ciudadano'}</p>
                      <p className="text-[11px] text-slate-500">{c.neighborhood || c.citizen_phone}</p>
                    </td>
                    <td className="py-3.5 px-5 max-w-xs">
                      <span className="font-semibold text-slate-800 block line-clamp-1">{c.title}</span>
                      <span className="text-[11px] text-slate-500">{c.category}</span>
                    </td>
                    <td className="py-3.5 px-5">
                      <span className="text-slate-800 font-medium">{c.assigned_to}</span>
                    </td>
                    <td className="py-3.5 px-5">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        c.priority === 'ALTA' ? 'bg-red-100 text-red-700' :
                        c.priority === 'MEDIA' ? 'bg-amber-100 text-amber-800' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="py-3.5 px-5">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        c.status === 'RESUELTO' ? 'bg-emerald-100 text-[#23856D]' :
                        c.status === 'ESCALADO_HUMANO' ? 'bg-rose-100 text-rose-800' :
                        c.status === 'EN_GESTION' ? 'bg-blue-100 text-[#1769AA]' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {c.status === 'ESCALADO_HUMANO' ? 'Revisión Funcionario' :
                         c.status === 'EN_GESTION' ? 'En Trámite' :
                         c.status === 'RESUELTO' ? 'Resuelto' : 'Radicado'}
                      </span>
                    </td>
                    <td className="py-3.5 px-5">
                      <span className={c.is_at_risk ? 'text-red-600 font-bold' : 'text-slate-600'}>
                        {c.sla_due_date || 'En trámite'}
                      </span>
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      <button
                        onClick={() => openCaseDetail(c.id)}
                        className="px-3 py-1.5 rounded-xl bg-[#102A43] text-white hover:bg-[#1769AA] text-xs font-bold transition inline-flex items-center space-x-1"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Gestionar</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {cases.length === 0 && (
            <div className="py-12 text-center text-slate-400 text-xs">
              <Inbox className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p>No se encontraron solicitudes con los criterios seleccionados.</p>
            </div>
          )}

        </div>
      )}

      {/* PESTAÑA 2: CONEXIÓN SNOWFLAKE */}
      {activeTab === 'snowflake' && (
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center space-x-2">
                <Database className="w-6 h-6 text-[#1769AA]" />
                <h3 className="font-bold text-lg text-[#102A43]">Conexión Oficial con Snowflake</h3>
              </div>
              <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
                Configure las credenciales de su cuenta de Snowflake para habilitar la persistencia institucional de los casos, la auditoría y la analítica centralizada en la nube distrital.
              </p>
            </div>
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                snowflakeStatus?.is_configured ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
              }`}>
                {snowflakeStatus?.is_configured ? '● Conectado a Snowflake' : '○ Modo Local Preparado'}
              </span>
            </div>
          </div>

          {/* Formulario de Conexión */}
          <form onSubmit={handleTestSnowflake} className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Identificador de Cuenta Snowflake</label>
              <input
                type="text"
                placeholder="Ejemplo: xy12345.us-east-1 o orgname-accountname"
                value={sfAccount}
                onChange={(e) => setSfAccount(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-[#1769AA]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Usuario de Snowflake</label>
              <input
                type="text"
                placeholder="Ejemplo: ADMIN_BQL"
                value={sfUser}
                onChange={(e) => setSfUser(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-[#1769AA]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Contraseña</label>
              <input
                type="password"
                placeholder="••••••••••••"
                value={sfPassword}
                onChange={(e) => setSfPassword(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-[#1769AA]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Warehouse de Cómputo</label>
              <input
                type="text"
                value={sfWarehouse}
                onChange={(e) => setSfWarehouse(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-[#1769AA]"
              />
            </div>

            <div className="md:col-span-2 flex items-center justify-between pt-4 border-t border-slate-100">
              <div className="flex items-center space-x-3">
                <button
                  type="submit"
                  disabled={sfTesting}
                  className="px-5 py-2.5 bg-[#1769AA] hover:bg-[#102A43] text-white font-bold rounded-xl text-xs transition flex items-center space-x-2 shadow-xs disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${sfTesting ? 'animate-spin' : ''}`} />
                  <span>{sfTesting ? 'Comprobando conexión...' : 'Probar y Guardar Conexión'}</span>
                </button>

                <button
                  type="button"
                  onClick={handleSyncSnowflake}
                  disabled={sfSyncing}
                  className="px-5 py-2.5 bg-[#23856D] hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition flex items-center space-x-2 shadow-xs disabled:opacity-50"
                >
                  <CloudUpload className="w-4 h-4" />
                  <span>{sfSyncing ? 'Sincronizando casos...' : 'Sincronizar Casos a Snowflake'}</span>
                </button>
              </div>

              <span className="text-[11px] text-slate-500">Base: {sfDatabase} | Esquema: OPERATIONS</span>
            </div>
          </form>

          {/* Mensaje de Resultado de Conexión */}
          {sfMessage && (
            <div className={`p-4 rounded-2xl text-xs border ${
              sfMessage.success ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-red-50 text-red-800 border-red-200'
            }`}>
              <p className="font-bold">{sfMessage.success ? 'Operación Exitosa' : 'Aviso de Conexión'}</p>
              <p className="mt-0.5">{sfMessage.message}</p>
            </div>
          )}

          {/* DÓNDE SE VE LA BASE DE DATOS SNOWFLAKE: GUÍA DE ACCESO */}
          <div className="mt-8 pt-8 border-t border-slate-200 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h4 className="font-bold text-base text-[#102A43] flex items-center space-x-2">
                  <ExternalLink className="w-5 h-5 text-[#1769AA]" />
                  <span>¿Dónde se visualiza y consulta la Base de Datos Snowflake?</span>
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  Ubicaciones oficiales para inspeccionar, consultar con SQL y auditar los datos del sistema.
                </p>
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                <a
                  href="/api/snowflake/download_sql"
                  download="snowflake_barranquilla_complete.sql"
                  className="px-3.5 py-2 bg-white border border-slate-300 hover:border-[#1769AA] text-slate-800 text-xs font-bold rounded-xl transition flex items-center space-x-1.5 shadow-xs"
                >
                  <Download className="w-3.5 h-3.5 text-[#1769AA]" />
                  <span>Descargar Script SQL</span>
                </a>
                <a
                  href="https://app.snowflake.com"
                  target="_blank"
                  rel="noreferrer"
                  className="px-3.5 py-2 bg-[#102A43] hover:bg-[#1769AA] text-white text-xs font-bold rounded-xl transition flex items-center space-x-1.5 shadow-xs"
                >
                  <span>Abrir Snowsight Cloud</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl border border-slate-200 bg-[#F2F6FA] space-y-2">
                <div className="flex items-center space-x-2 text-[#1769AA] font-bold text-xs">
                  <Database className="w-4 h-4" />
                  <span>1. En la Consola Web Snowflake</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Ingrese a <strong>app.snowflake.com</strong> con su usuario institucional. En el menú izquierdo seleccione <strong>Data → Databases</strong> y encontrará <strong>BARRANQUILLA_CITIZEN_DB</strong> con sus 5 esquemas.
                </p>
                <div className="text-[11px] text-[#1769AA] font-mono bg-white p-2 rounded-lg border border-slate-200">
                  Data → Databases → BARRANQUILLA_CITIZEN_DB
                </div>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 bg-[#F2F6FA] space-y-2">
                <div className="flex items-center space-x-2 text-[#23856D] font-bold text-xs">
                  <Terminal className="w-4 h-4" />
                  <span>2. En Hojas de Trabajo SQL</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  En Snowflake Snowsight, cree un <strong>Worksheet SQL</strong> y ejecute consultas en tiempo real sobre la tabla de solicitudes radicadas:
                </p>
                <div className="text-[11px] text-slate-700 font-mono bg-white p-2 rounded-lg border border-slate-200 overflow-x-auto">
                  SELECT * FROM BARRANQUILLA_CITIZEN_DB.OPERATIONS.CASES;
                </div>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 bg-[#F2F6FA] space-y-2">
                <div className="flex items-center space-x-2 text-amber-700 font-bold text-xs">
                  <Layers className="w-4 h-4" />
                  <span>3. En el Proyecto Local</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  El esquema DDL completo está en <strong className="font-mono text-[11px]">snowflake_schema.sql</strong> y los datos se guardan en <strong className="font-mono text-[11px]">data_barranquilla.db</strong> y exportaciones CSV.
                </p>
                <div className="text-[11px] text-slate-700 font-mono bg-white p-2 rounded-lg border border-slate-200">
                  backend/app/core/snowflake_schema.sql
                </div>
              </div>
            </div>

            {/* EXPLORADOR DE LAS 5 CAPAS LÓGICAS DE SNOWFLAKE */}
            {sfSchema && (
              <div className="space-y-4 pt-4">
                <div className="flex items-center justify-between">
                  <h5 className="font-bold text-sm text-[#102A43] flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-[#1769AA]" />
                    <span>Estructura Oficial de BARRANQUILLA_CITIZEN_DB (5 Esquemas)</span>
                  </h5>
                  <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
                    Warehouse: {sfSchema.warehouse} | Base: {sfSchema.database_name}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {sfSchema.schemas?.map((sch) => (
                    <div key={sch.schema_name} className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-[#1769AA] transition space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-[#102A43] font-mono bg-blue-50 text-[#1769AA] px-2.5 py-1 rounded-lg">
                          ESQUEMA: {sch.schema_name}
                        </span>
                        <span className="text-[10px] text-slate-400 font-bold">
                          {sch.tables?.length} Objeto(s)
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600 leading-tight">
                        {sch.description}
                      </p>
                      <div className="space-y-1.5 pt-1">
                        {sch.tables?.map((tbl) => (
                          <div key={tbl.table_name} className="p-2 rounded-xl bg-slate-50 border border-slate-100 text-[11px] space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-mono font-bold text-slate-800">{tbl.table_name}</span>
                              <span className="text-[10px] font-bold text-[#23856D] bg-emerald-50 px-2 py-0.5 rounded-full">
                                {tbl.rows !== undefined ? `${tbl.rows} fila(s)` : tbl.type || 'VISTA'}
                              </span>
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {tbl.columns?.map(col => (
                                <span key={col} className="text-[9px] font-mono bg-white text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                                  {col}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* VISTA PREVIA EN VIVO DE CASOS EN OPERATIONS.CASES */}
                {sfSchema.sample_cases && sfSchema.sample_cases.length > 0 && (
                  <div className="p-5 rounded-2xl border border-slate-200 bg-slate-50 space-y-3 mt-4">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#102A43] flex items-center space-x-1.5">
                        <Table className="w-4 h-4 text-[#1769AA]" />
                        <span>Vista Previa en Vivo: Tabla OPERATIONS.CASES</span>
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        Últimos registros sincronizados
                      </span>
                    </div>

                    <div className="overflow-x-auto bg-white rounded-xl border border-slate-200">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-100 text-slate-600 text-[11px] border-b border-slate-200 font-bold">
                          <tr>
                            <th className="py-2.5 px-3">RADICADO</th>
                            <th className="py-2.5 px-3">CITIZEN_NAME</th>
                            <th className="py-2.5 px-3">CATEGORY</th>
                            <th className="py-2.5 px-3">STATUS</th>
                            <th className="py-2.5 px-3">ASSIGNED_TO</th>
                            <th className="py-2.5 px-3">SLA_DUE_DATE</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-[11px] text-slate-700">
                          {sfSchema.sample_cases.map((sc, idx) => (
                            <tr key={idx} className="hover:bg-blue-50/50">
                              <td className="py-2 px-3 font-bold text-[#1769AA]">{sc.RADICADO}</td>
                              <td className="py-2 px-3 font-sans text-slate-900">{sc.CITIZEN_NAME}</td>
                              <td className="py-2 px-3 font-sans">{sc.CATEGORY}</td>
                              <td className="py-2 px-3">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  sc.STATUS === 'RESUELTO' ? 'bg-emerald-100 text-emerald-800' :
                                  sc.STATUS === 'ESCALADO_HUMANO' ? 'bg-rose-100 text-rose-800' :
                                  'bg-blue-100 text-blue-800'
                                }`}>
                                  {sc.STATUS}
                                </span>
                              </td>
                              <td className="py-2 px-3 font-sans">{sc.ASSIGNED_TO}</td>
                              <td className="py-2 px-3">{sc.SLA_DUE_DATE}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>
      )}

      {/* PESTAÑA 3: BIBLIOTECA NORMATIVA */}
      {activeTab === 'rag' && (
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
          <div>
            <h3 className="font-bold text-lg text-[#102A43] flex items-center space-x-2">
              <BookOpen className="w-5 h-5 text-[#1769AA]" />
              <span>Documentos y Reglamentos Oficiales Vigentes</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Catálogo de guías, estatutos y reglamentos de la Alcaldía de Barranquilla utilizados para fundamentar las respuestas a la ciudadanía.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <div key={doc.id} className="p-5 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-white transition flex flex-col justify-between">
                <div>
                  <span className="bg-blue-100 text-[#1769AA] px-2.5 py-0.5 rounded-full text-[10px] font-bold block w-fit mb-2">
                    {doc.category}
                  </span>
                  <h4 className="font-bold text-sm text-slate-900 mb-1.5">{doc.title}</h4>
                  <p className="text-xs text-slate-600 line-clamp-3 mb-3">{doc.summary}</p>
                </div>
                
                <div className="pt-3 border-t border-slate-200 text-[11px] text-slate-500 space-y-1">
                  <p><strong>Entidad:</strong> {doc.authority}</p>
                  <p><strong>Vigencia:</strong> {doc.validity_date}</p>
                  <a
                    href={doc.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[#1769AA] font-bold hover:underline inline-flex items-center gap-1 mt-2 text-xs"
                  >
                    <span>Ver publicación oficial</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PESTAÑA 4: HISTORIAL DE ACTUACIONES */}
      {activeTab === 'audit' && (
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
          <div>
            <h3 className="font-bold text-lg text-[#102A43] flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-[#23856D]" />
              <span>Trazabilidad y Registro Oficial de Actuaciones</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Registro inmutable de cada actuación formal, radicación, asignación y validación institucional realizada.
            </p>
          </div>

          <div className="space-y-3">
            {metrics?.recent_audit_events && metrics.recent_audit_events.map((ev) => (
              <div key={ev.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-mono font-bold text-[#1769AA]">{ev.radicado}</span>
                    <span className="bg-slate-200 text-slate-700 px-2.5 py-0.5 rounded-full text-[10px] font-bold">
                      {ev.event_type}
                    </span>
                    <span className="text-[11px] text-slate-500">Responsable: {ev.actor} ({ev.actor_role})</span>
                  </div>
                  <p className="text-slate-800 font-medium">{ev.description}</p>
                </div>
                <span className="text-[11px] text-slate-400 font-medium shrink-0 ml-4">{ev.time}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL DE GESTIÓN Y DECISIÓN DE CASO (HUMAN-IN-THE-LOOP) */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-slate-200">
            
            {/* Cabecera */}
            <div className="bg-[#102A43] text-white p-6 flex items-center justify-between">
              <div>
                <span className="text-xs text-[#20A4C8] font-mono font-bold block">{selectedCase.radicado}</span>
                <h3 className="font-bold text-lg">{selectedCase.title}</h3>
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="p-1 hover:bg-white/10 rounded-xl text-slate-300 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido */}
            <div className="p-6 overflow-y-auto flex-1 space-y-5 text-xs text-slate-700">
              
              {/* Información Ciudadana */}
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
                <h4 className="font-bold text-slate-900 uppercase text-[11px] mb-2">Descripción de la Solicitud</h4>
                <p className="text-slate-800 text-xs mb-3 whitespace-pre-wrap leading-relaxed">{selectedCase.description}</p>
                
                <div className="grid grid-cols-2 gap-2 text-[11px] pt-3 border-t border-slate-200 text-slate-600">
                  <p><strong>Ciudadano:</strong> {selectedCase.citizen_name || 'Ciudadano'}</p>
                  <p><strong>Teléfono:</strong> {selectedCase.citizen_phone || 'No registrado'}</p>
                  <p><strong>Ubicación:</strong> {selectedCase.address} - {selectedCase.neighborhood}</p>
                  <p><strong>Fecha Registro:</strong> {selectedCase.created_at}</p>
                </div>
              </div>

              {/* Sugerencia y Decisión Institucional */}
              <div className="bg-blue-50/70 p-5 rounded-2xl border border-blue-200">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold text-[#102A43] uppercase text-[11px] flex items-center space-x-1.5">
                    <CheckCircle className="w-4 h-4 text-[#1769AA]" />
                    <span>Direccionamiento Asistido</span>
                  </h4>
                  <span className="font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full text-[10px]">
                    Coincidencia: Alta
                  </span>
                </div>

                <div className="space-y-1 mb-4 text-xs">
                  <p><strong>Categoría Propuesta:</strong> {selectedCase.classification_suggestion?.predicted_category}</p>
                  <p><strong>Dependencia Asignada:</strong> {selectedCase.assigned_to}</p>
                  <p className="text-slate-600"><strong>Criterio de Asignación:</strong> {selectedCase.classification_suggestion?.justification}</p>
                </div>

                {/* Acciones de Funcionario Humano */}
                <div className="pt-3 border-t border-blue-200 flex flex-wrap gap-2 items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleApproveClassification(selectedCase.id)}
                      disabled={actionLoading}
                      className="px-4 py-2 bg-[#23856D] hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition flex items-center space-x-1.5 shadow-xs"
                    >
                      <Check className="w-4 h-4" />
                      <span>Aprobar Direccionamiento</span>
                    </button>
                    
                    <button
                      onClick={() => handleUpdateStatus(selectedCase.id, 'RESUELTO')}
                      disabled={actionLoading}
                      className="px-4 py-2 bg-[#1769AA] hover:bg-[#102A43] text-white font-bold rounded-xl text-xs transition shadow-xs"
                    >
                      Marcar como Resuelto
                    </button>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <select
                      value={overrideDept}
                      onChange={(e) => setOverrideDept(e.target.value)}
                      className="px-3 py-2 border border-slate-300 rounded-xl text-xs bg-white font-medium"
                    >
                      <option value="">Reclasificar a...</option>
                      <option value="DEP_ALUMBRADO">Alumbrado (K-YENA)</option>
                      <option value="DEP_ESPACIO_PUBLICO">Control Urbano</option>
                      <option value="DEP_HACIENDA">Hacienda Distrital</option>
                      <option value="DEP_GESTION_SOCIAL">Gestión Social (Sisbén)</option>
                      <option value="DEP_SALUD">Salud Pública</option>
                      <option value="DEP_SECRETARIA_GENERAL">Secretaría General</option>
                    </select>
                    {overrideDept && (
                      <button
                        onClick={() => handleApproveClassification(selectedCase.id, overrideDept)}
                        className="px-3 py-2 bg-amber-600 text-white rounded-xl font-bold hover:bg-amber-700 text-xs shadow-xs"
                      >
                        Aplicar
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Historial de Actuaciones */}
              <div>
                <h4 className="font-bold text-slate-800 uppercase text-[11px] mb-2 flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span>Historial de Actuaciones del Caso</span>
                </h4>
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                  {selectedCase.events?.map((ev) => (
                    <div key={ev.id} className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <div className="flex items-center justify-between font-bold text-slate-800">
                        <span>{ev.event_type}</span>
                        <span className="text-[10px] text-slate-400 font-normal">{ev.timestamp}</span>
                      </div>
                      <p className="text-slate-600 mt-0.5">{ev.description}</p>
                      <span className="text-[10px] text-[#1769AA] font-medium">Por: {ev.actor} ({ev.actor_role})</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Pie */}
            <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSelectedCase(null)}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-900"
              >
                Cerrar Detalle
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
