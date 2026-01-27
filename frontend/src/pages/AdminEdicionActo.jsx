import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom'; // Importamos useParams para obtener el ID
import api from '../api';
import '../styles/AdminEdicionActo.css';
import { Save, FileText, Settings, ShieldAlert, CheckCircle, Clock, AlertCircle, Lock, ArrowLeft } from "lucide-react";

function AdminEdicionActo() {
    const navigate = useNavigate();
    const { id } = useParams(); // Obtenemos el ID de la URL

    const currentYear = new Date().getFullYear();
    const minDate = `${currentYear}-01-01T00:00`;
    const maxDate = `${currentYear}-12-31T23:59`;
    
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");
    
    const [currentUser, setCurrentUser] = useState(null);
    const [tiposActo, setTiposActo] = useState([]);
    const [requierePapeleta, setRequierePapeleta] = useState(false);
    
    // Estado para controlar si la fecha principal está bloqueada por regla de negocio
    const [isDateLocked, setIsDateLocked] = useState(false);

    const [formData, setFormData] = useState({
        nombre: '',
        descripcion: '',
        fecha: '',
        tipo_acto: '',
        modalidad: 'TRADICIONAL',
        inicio_solicitud: '',
        fin_solicitud: '',
        inicio_solicitud_cirios: '',
        fin_solicitud_cirios: ''
    });

    // --- HELPER: Formatear fecha para input datetime-local ---
    // Django envía "2024-03-24T18:00:00Z" o similar. El input espera "yyyy-MM-ddThh:mm"
    const formatDateForInput = (isoString) => {
        if (!isoString) return '';
        const date = new Date(isoString);
        // Ajuste básico a local para el input (o cortar el string si viene en UTC y queremos mostrarlo tal cual)
        // Para simplificar, cortamos los segundos y la Z si existen
        return isoString.slice(0, 16); 
    };

    // --- CARGA INICIAL ---
    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                // 1. Verificar Usuario
                const resUser = await api.get("api/me/");
                const user = resUser.data;
                if (isMounted) setCurrentUser(user);

                if (!user.esAdmin) {
                    alert("No tienes permisos para editar actos.");
                    navigate("/home");
                    return;
                }

                // 2. Cargar Tipos de Acto
                const resTipos = await api.get("api/tipos-acto/"); 
                if (isMounted) setTiposActo(resTipos.data);

                // 3. Cargar Datos del Acto a Editar
                const resActo = await api.get(`api/actos/${id}/`); // Asumimos que tienes este endpoint GET detail
                const data = resActo.data;

                if (isMounted) {
                    // Preparamos el formulario
                    setFormData({
                        nombre: data.nombre,
                        descripcion: data.descripcion || '',
                        fecha: formatDateForInput(data.fecha),
                        tipo_acto: data.tipo_acto, // Asumimos que viene el Slug o string
                        modalidad: data.modalidad,
                        inicio_solicitud: formatDateForInput(data.inicio_solicitud),
                        fin_solicitud: formatDateForInput(data.fin_solicitud),
                        inicio_solicitud_cirios: formatDateForInput(data.inicio_solicitud_cirios),
                        fin_solicitud_cirios: formatDateForInput(data.fin_solicitud_cirios)
                    });

                    // Configurar visibilidad de secciones según el tipo cargado
                    setRequierePapeleta(data.requiere_papeleta);

                    // Verificar regla de bloqueo de fecha
                    if (data.inicio_solicitud) {
                        const now = new Date();
                        const inicio = new Date(data.inicio_solicitud);
                        if (now >= inicio) {
                            setIsDateLocked(true);
                        }
                    }
                }

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar los datos del acto.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [id, navigate]);

    // --- HANDLERS ---
    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value } = e.target;
        let newData = { ...formData, [name]: value };

        if (name === 'tipo_acto') {
            const tipoSeleccionado = tiposActo.find(t => t.tipo === value);
            if (tipoSeleccionado) {
                setRequierePapeleta(tipoSeleccionado.requiere_papeleta);
                if (!tipoSeleccionado.requiere_papeleta) {
                    newData.modalidad = '';
                    newData.inicio_solicitud = '';
                    newData.fin_solicitud = '';
                    newData.inicio_solicitud_cirios = '';
                    newData.fin_solicitud_cirios = '';
                }
            }
        }

        if (name === 'modalidad' && value === 'UNIFICADO') {
            newData.inicio_solicitud_cirios = '';
            newData.fin_solicitud_cirios = '';
        }

        setFormData(newData);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");

        const payload = { ...formData };

        Object.keys(payload).forEach(key => {
            if (payload[key] === '') payload[key] = null;
        });

        if (!requierePapeleta) {
            payload.modalidad = null;
            payload.inicio_solicitud = null;
            payload.fin_solicitud = null;
            payload.inicio_solicitud_cirios = null;
            payload.fin_solicitud_cirios = null;
        } else if (payload.modalidad === 'UNIFICADO') {
            payload.inicio_solicitud_cirios = null;
            payload.fin_solicitud_cirios = null;
        }

        try {
            await api.put(`api/actos/${id}/editar/`, payload);
            setSuccessMsg("Acto actualizado correctamente.");
            setTimeout(() => navigate("/home"), 1500);
        } catch (err) {
            if (err.response?.status === 500) {
                setError("Error interno del servidor. Revisa que las fechas sean lógicas.");
            } else {
                const errorData = err.response?.data;
                setError(typeof errorData === 'object' ? JSON.stringify(errorData) : "Error al validar.");
            }
        } finally {
            setSaving(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando datos del acto...</div>;

    return (
        <div>
            {/* ... (Sidebar Código Idéntico al anterior) ... */}
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
               {/* Copiar exactamente el mismo sidebar que en Creación */}
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} id="btn" onClick={toggleSidebar}></i>
                </div>
                <ul className="nav-list-dashboard">
                    <li onClick={() => navigate("/home")} style={{cursor: 'pointer'}}>
                        <a href="#">
                            <i className='bx bx-arrow-back'></i>
                            <span className="link_name-dashboard">Volver</span>
                        </a>
                        <span className="tooltip-dashboard">Volver</span>
                    </li>
                    {/* Resto de items del sidebar... */}
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            <img src="/profile.jpeg" alt="profile" />
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{currentUser ? `${currentUser.nombre}` : "Usuario"}</div>
                                <div className="designation-dashboard">Admin</div>
                            </div>
                        </div>
                        <i className="bx bx-log-out" id="log_out" onClick={handleLogout} style={{cursor: 'pointer'}}></i>
                    </li>
                </ul>
            </div>

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">
                    <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '10px' }}>
                        <ArrowLeft size={24} color="#11101d"/>
                    </button>
                    Editar Acto
                </div>
                
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        {/* ALERTAS */}
                        {error && (
                            <div className="alert-banner-edicion error-edicion">
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-edicion success-edicion">
                                <CheckCircle size={20} />
                                <span>{successMsg}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            {/* SECCIÓN 1: DATOS GENERALES */}
                            <div className="form-section-edicion">
                                <h3 className="section-title-edicion"><FileText size={18}/> Datos Generales</h3>
                                <div className="form-grid-edicion grid-2-edicion">
                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Nombre del Acto *</label>
                                        <input 
                                            type="text" 
                                            name="nombre" 
                                            value={formData.nombre} 
                                            onChange={handleChange} 
                                            required 
                                        />
                                    </div>

                                    <div className="form-group-edicion">
                                        <label>Tipo de Acto *</label>
                                        <select 
                                            name="tipo_acto" 
                                            value={formData.tipo_acto} 
                                            onChange={handleChange} 
                                            required
                                        >
                                            <option value="">-- Seleccionar Tipo --</option>
                                            {tiposActo.map(tipo => (
                                                <option key={tipo.id} value={tipo.tipo}>
                                                    {tipo.nombre_mostrar || tipo.tipo}
                                                </option>
                                            ))}
                                        </select>
                                        <small style={{ color: '#ef4444', marginTop: '4px', display:'block', fontSize:'0.75rem' }}>
                                            Nota: Si cambia el tipo y existen puestos generados, obtendrá un error al guardar.
                                        </small>
                                    </div>

                                    <div className="form-group-edicion">
                                        <label>
                                            Fecha y Hora * {isDateLocked && <Lock size={14} style={{marginLeft: '5px', color: '#ef4444'}}/>}
                                        </label>
                                        <input 
                                            type="datetime-local" 
                                            name="fecha" 
                                            value={formData.fecha} 
                                            onChange={handleChange}
                                            min={minDate} 
                                            max={maxDate}
                                            required
                                            disabled={isDateLocked} // REGLA: Bloqueo si ya empezó solicitud
                                            className={isDateLocked ? 'input-disabled' : ''}
                                            title={isDateLocked ? "No se puede cambiar la fecha porque el plazo de solicitud ya ha comenzado" : ""}
                                        />
                                        {isDateLocked && (
                                            <small style={{color: '#ef4444'}}>Fecha bloqueada (plazo iniciado)</small>
                                        )}
                                    </div>

                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Descripción</label>
                                        <textarea 
                                            name="descripcion" 
                                            value={formData.descripcion} 
                                            onChange={handleChange}
                                            rows="3"
                                            className="textarea-standard"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN 2: CONFIGURACIÓN REPARTO */}
                            {requierePapeleta && (
                                <>
                                    <div className="form-section-edicion">
                                        <h3 className="section-title-edicion"><Settings size={18}/> Configuración de Reparto</h3>
                                        <div className="form-grid-edicion grid-2-edicion">
                                            <div className="form-group-edicion">
                                                <label>Modalidad de Reparto</label>
                                                <select name="modalidad" value={formData.modalidad} onChange={handleChange}>
                                                    <option value="TRADICIONAL">Tradicional (Fases separadas)</option>
                                                    <option value="UNIFICADO">Unificado / Express</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section-edicion admin-section-edicion">
                                        <h3 className="section-title-edicion admin-title-edicion"><Clock size={18}/> Edición de Plazos</h3>
                                        
                                        {/* BLOQUE INSIGNIAS / GENERAL */}
                                        <h4 className="subsection-title">
                                            {formData.modalidad === 'TRADICIONAL' ? '1. Solicitud de Insignias / Varas' : 'Plazo Único (General)'}
                                        </h4>
                                        <div className="form-grid-edicion grid-2-edicion">
                                            <div className="form-group-edicion">
                                                <label>Inicio Solicitud</label>
                                                <input 
                                                    type="datetime-local" 
                                                    name="inicio_solicitud" 
                                                    value={formData.inicio_solicitud || ''} 
                                                    onChange={handleChange} 
                                                    min={minDate} max={maxDate}
                                                />
                                            </div>
                                            <div className="form-group-edicion">
                                                <label>Fin Solicitud</label>
                                                <input 
                                                    type="datetime-local" 
                                                    name="fin_solicitud" 
                                                    value={formData.fin_solicitud || ''} 
                                                    onChange={handleChange}
                                                    min={minDate} max={maxDate}
                                                />
                                            </div>
                                        </div>

                                        {/* BLOQUE CIRIOS (SOLO TRADICIONAL) */}
                                        {formData.modalidad === 'TRADICIONAL' && (
                                            <>
                                                <h4 className="subsection-title" style={{ marginTop: '20px' }}>2. Solicitud de Cirios / General</h4>
                                                <div className="form-grid-edicion grid-2-edicion">
                                                    <div className="form-group-edicion">
                                                        <label>Inicio Solicitud</label>
                                                        <input 
                                                            type="datetime-local" 
                                                            name="inicio_solicitud_cirios" 
                                                            value={formData.inicio_solicitud_cirios || ''} 
                                                            onChange={handleChange} 
                                                            min={minDate} max={maxDate}
                                                        />
                                                    </div>
                                                    <div className="form-group-edicion">
                                                        <label>Fin Solicitud</label>
                                                        <input 
                                                            type="datetime-local" 
                                                            name="fin_solicitud_cirios" 
                                                            value={formData.fin_solicitud_cirios || ''} 
                                                            onChange={handleChange}
                                                            min={minDate} max={maxDate}
                                                        />
                                                    </div>
                                                </div>
                                                
                                                <div className="info-box-blue">
                                                    <ShieldAlert size={16} />
                                                    <span>Recuerda: Los plazos no deben solaparse y deben terminar antes del acto.</span>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </>
                            )}

                            {/* BOTONES */}
                            <div className="form-actions-edicion">
                                <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/home")}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn-save-edicion" disabled={saving}>
                                    <Save size={18} />
                                    {saving ? "Guardando..." : "Guardar Cambios"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminEdicionActo;