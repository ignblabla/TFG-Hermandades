import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api';
import '../styles/AdminCreacionActo.css';
import { Save, FileText, Settings, ShieldAlert, CheckCircle, Clock, AlertCircle, Lock, ArrowLeft } from "lucide-react";

function AdminEdicionActo() {
    const navigate = useNavigate();
    const { id } = useParams();

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

    const formatDateForInput = (isoString) => {
        if (!isoString) return '';
        const date = new Date(isoString);
        return isoString.slice(0, 16); 
    };

    // --- CARGA INICIAL ---
    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                const user = resUser.data;
                if (isMounted) setCurrentUser(user);

                if (!user.esAdmin) {
                    alert("No tienes permisos para editar actos.");
                    navigate("/home");
                    return;
                }

                const resTipos = await api.get("api/tipos-acto/"); 
                if (isMounted) setTiposActo(resTipos.data);

                const resActo = await api.get(`api/actos/${id}/`);
                const data = resActo.data;

                if (isMounted) {
                    setFormData({
                        nombre: data.nombre,
                        descripcion: data.descripcion || '',
                        fecha: formatDateForInput(data.fecha),
                        tipo_acto: data.tipo_acto,
                        modalidad: data.modalidad,
                        inicio_solicitud: formatDateForInput(data.inicio_solicitud),
                        fin_solicitud: formatDateForInput(data.fin_solicitud),
                        inicio_solicitud_cirios: formatDateForInput(data.inicio_solicitud_cirios),
                        fin_solicitud_cirios: formatDateForInput(data.fin_solicitud_cirios)
                    });

                    setRequierePapeleta(data.requiere_papeleta);

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
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i 
                        className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} 
                        id="btn" 
                        onClick={toggleSidebar}
                    ></i>
                </div>
                <ul className="nav-list-dashboard">
                    <li>
                        <i className="bx bx-search" onClick={toggleSidebar}></i>
                        <input type="text" placeholder="Search..." />
                        <span className="tooltip-dashboard">Search</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-grid-alt"></i>
                            <span className="link_name-dashboard">Dashboard</span>
                        </a>
                        <span className="tooltip-dashboard">Dashboard</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-user"></i>
                            <span className="link_name-dashboard">User</span>
                        </a>
                        <span className="tooltip-dashboard">User</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-chat"></i>
                            <span className="link_name-dashboard">Message</span>
                        </a>
                        <span className="tooltip-dashboard">Message</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-pie-chart-alt-2"></i>
                            <span className="link_name-dashboard">Analytics</span>
                        </a>
                        <span className="tooltip-dashboard">Analytics</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-folder"></i>
                            <span className="link_name-dashboard">File Manager</span>
                        </a>
                        <span className="tooltip-dashboard">File Manager</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-cart-alt"></i>
                            <span className="link_name-dashboard">Order</span>
                        </a>
                        <span className="tooltip-dashboard">Order</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-cog"></i>
                            <span className="link_name-dashboard">Settings</span>
                        </a>
                        <span className="tooltip-dashboard">Settings</span>
                    </li>
                    
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            <img src="profile.jpeg" alt="profile image" />
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{currentUser ? `${currentUser.nombre} ${currentUser.primer_apellido}` : "Usuario"}</div>
                                <div className="designation-dashboard">Administrador</div>
                            </div>
                        </div>
                        <i 
                            className="bx bx-log-out" 
                            id="log_out" 
                            onClick={handleLogout}
                            style={{cursor: 'pointer'}} 
                        ></i>
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
                        
                        {error && (
                            <div className="alert-banner-creacion-acto error-creacion-acto">
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-creacion-acto success-creacion-acto">
                                <CheckCircle size={20} />
                                <span>{successMsg}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            {/* SECCIÓN 1: DATOS GENERALES */}
                            <div className="form-section-creacion-acto">
                                <h3 className="section-title-creacion-acto"><FileText size={18}/> Datos Generales</h3>
                                <div className="form-grid-creacion-acto">
                                    
                                    <div className="form-group-creacion-acto span-2-main">
                                        <label>Nombre del Acto *</label>
                                        <input 
                                            type="text" 
                                            name="nombre" 
                                            value={formData.nombre} 
                                            onChange={handleChange} 
                                            required 
                                        />
                                    </div>

                                    <div className="form-group-creacion-acto">
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
                                                    {tipo.nombre_mostrar}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group-creacion-acto">
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
                                            disabled={isDateLocked}
                                            className={isDateLocked ? 'input-disabled' : ''}
                                            title={isDateLocked ? "Fecha bloqueada por inicio de plazo" : ""}
                                        />
                                    </div>

                                    <div className="form-group-creacion-acto span-full">
                                        <label>Descripción</label>
                                        <textarea 
                                            name="descripcion" 
                                            value={formData.descripcion} 
                                            onChange={handleChange}
                                            rows="4"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN 2: CONFIGURACIÓN REPARTO */}
                            {requierePapeleta && (
                                <>
                                    <div className="form-section-creacion-acto">
                                        <h3 className="section-title-creacion-acto"><Settings size={18}/> Configuración de Reparto</h3>
                                        <div className="form-grid-creacion-acto">
                                            
                                            <div className="form-group-creacion-acto span-full">
                                                <label>Modalidad de Reparto</label>
                                                <select name="modalidad" value={formData.modalidad} onChange={handleChange}>
                                                    <option value="TRADICIONAL">Tradicional (Fases separadas)</option>
                                                    <option value="UNIFICADO">Unificado / Express</option>
                                                </select>
                                                <small style={{ color: '#6b7280', display: 'block', marginTop: '5px' }}>
                                                    {formData.modalidad === 'TRADICIONAL' 
                                                        ? 'Primero se asignan insignias, luego cirios.' 
                                                        : 'Todos los puestos se asignan en un mismo plazo.'}
                                                </small>
                                            </div>

                                        </div>
                                    </div>

                                    <div className="form-section-creacion-acto admin-section-creacion-acto">
                                        <h3 className="section-title-creacion-acto admin-title-creacion-acto"><Clock size={18}/> Edición de Plazos</h3>
                                        
                                        <h4 style={{ margin: '15px 0 10px', color: '#4b5563', fontSize: '0.95rem' }}>
                                            {formData.modalidad === 'TRADICIONAL' ? '1. Solicitud de Insignias / Varas' : 'Plazo Único (General)'}
                                        </h4>
                                        <div className="grid-dates-row">
                                            <div className="form-group-creacion-acto">
                                                <label>Inicio Solicitud</label>
                                                <input 
                                                    type="datetime-local" 
                                                    name="inicio_solicitud" 
                                                    value={formData.inicio_solicitud || ''} 
                                                    onChange={handleChange} 
                                                    min={minDate} max={maxDate}
                                                />
                                            </div>
                                            <div className="form-group-creacion-acto">
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

                                        {formData.modalidad === 'TRADICIONAL' && (
                                            <>
                                                <h4 style={{ margin: '20px 0 10px', color: '#4b5563', fontSize: '0.95rem' }}>2. Solicitud de Cirios / General</h4>
                                                <div className="grid-dates-row">
                                                    <div className="form-group-creacion-acto">
                                                        <label>Inicio Solicitud</label>
                                                        <input 
                                                            type="datetime-local" 
                                                            name="inicio_solicitud_cirios" 
                                                            value={formData.inicio_solicitud_cirios || ''} 
                                                            onChange={handleChange} 
                                                            min={minDate} max={maxDate}
                                                        />
                                                    </div>
                                                    <div className="form-group-creacion-acto">
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
                                                
                                                <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#eff6ff', borderRadius: '6px', borderLeft: '4px solid #3b82f6', fontSize: '0.85rem', color: '#1e40af' }}>
                                                    <ShieldAlert size={16} style={{ verticalAlign: 'text-bottom', marginRight: '5px' }}/>
                                                    Recuerda: En modalidad tradicional, la solicitud de cirios no puede comenzar antes de que termine la de insignias.
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </>
                            )}

                            <div className="form-actions-creacion-acto">
                                <button type="button" className="btn-cancel-creacion-acto" onClick={() => navigate("/home")}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn-save-creacion-acto" disabled={saving}>
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