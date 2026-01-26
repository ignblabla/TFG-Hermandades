import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import '../styles/AdminEdicionHermano.css';
import { Save, FileText, Settings, ShieldAlert, CheckCircle, Clock, AlertCircle } from "lucide-react";

function AdminCreacionActo() {
    const navigate = useNavigate();

    const currentYear = new Date().getFullYear();
    const minDate = `${currentYear}-01-01T00:00`;
    const maxDate = `${currentYear}-12-31T23:59`;
    
    const [isOpen, setIsOpen] = useState(false); // Sidebar
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");
    
    const [currentUser, setCurrentUser] = useState(null);
    const [tiposActo, setTiposActo] = useState([]);
    const [requierePapeleta, setRequierePapeleta] = useState(false);

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

    // --- CARGA INICIAL (Usuario + Tipos de Acto) ---
    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                const user = resUser.data;
                
                if (isMounted) setCurrentUser(user);

                if (!user.esAdmin) {
                    alert("No tienes permisos para crear actos.");
                    navigate("/home");
                    return;
                }

                const resTipos = await api.get("api/tipos-acto/"); 
                if (isMounted) setTiposActo(resTipos.data);

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar configuración inicial.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [navigate]);

    // --- EFECTO MENSAJES ---
    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    // --- HANDLERS ---
    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value } = e.target;
        
        let newData = { ...formData, [name]: value };

        // 1. Lógica especial para TIPO DE ACTO
        if (name === 'tipo_acto') {
            const tipoSeleccionado = tiposActo.find(t => t.tipo === value);
            if (tipoSeleccionado) {
                setRequierePapeleta(tipoSeleccionado.requiere_papeleta);
                
                if (!tipoSeleccionado.requiere_papeleta) {
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
        setSuccessMsg("");

        const payload = { ...formData };
        const dateFields = ['inicio_solicitud', 'fin_solicitud', 'inicio_solicitud_cirios', 'fin_solicitud_cirios'];
        
        dateFields.forEach(field => {
            if (!payload[field]) payload[field] = null;
        });

        try {
            await api.post('api/actos/crear/', payload);
            setSuccessMsg("Acto creado correctamente.");
            
            setTimeout(() => {
                navigate("/home");
            }, 1500);

        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                const errorData = err.response.data;
                
                if (errorData.detail) {
                    setError(errorData.detail);
                } else {
                    const errorMessages = Object.entries(errorData)
                        .map(([key, msg]) => {
                            const fieldName = key === 'non_field_errors' ? 'Error' : key.replace(/_/g, ' ').toUpperCase();
                            const msgText = Array.isArray(msg) ? msg[0] : msg;
                            return `${fieldName}: ${msgText}`;
                        })
                        .join(" | ");
                    setError(errorMessages);
                }
            } else {
                setError("Ocurrió un error inesperado al conectar con el servidor.");
            }
            window.scrollTo(0, 0);
        } finally {
            setSaving(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando configuración...</div>;

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
                <div className="text-dashboard">Crear Nuevo Acto</div>
                
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        {/* BANNER DE ERRORES/EXITO */}
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
                                            placeholder={`Ej: Estación de Penitencia ${currentYear}`}
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
                                                    {tipo.nombre_mostrar}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group-edicion">
                                        <label>Fecha y Hora * ({currentYear})</label>
                                        <input 
                                            type="datetime-local" 
                                            name="fecha" 
                                            value={formData.fecha} 
                                            onChange={handleChange}
                                            min={minDate} 
                                            max={maxDate}
                                            required
                                        />
                                    </div>

                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Descripción</label>
                                        <textarea 
                                            name="descripcion" 
                                            value={formData.descripcion} 
                                            onChange={handleChange}
                                            rows="3"
                                            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN 2: CONFIGURACIÓN REPARTO (Solo visible si requiere papeleta) */}
                            {requierePapeleta && (
                                <>
                                    <div className="form-section-edicion">
                                        <h3 className="section-title-edicion"><Settings size={18}/> Configuración de Reparto</h3>
                                        <div className="form-grid-edicion grid-2-edicion">
                                            <div className="form-group-edicion">
                                                <label>Modalidad de Reparto</label>
                                                <select name="modalidad" value={formData.modalidad} onChange={handleChange}>
                                                    <option value="TRADICIONAL">Tradicional (Fases separadas)</option>
                                                    <option value="UNIFICADO">Unificado / Express (Todo a la vez)</option>
                                                </select>
                                                <small style={{ color: '#6b7280', display: 'block', marginTop: '5px' }}>
                                                    {formData.modalidad === 'TRADICIONAL' 
                                                        ? 'Primero se asignan insignias, luego cirios.' 
                                                        : 'Todos los puestos se asignan en un mismo plazo (usando la fecha de inicio/fin general).'}
                                                </small>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section-edicion admin-section-edicion">
                                        <h3 className="section-title-edicion admin-title-edicion"><Clock size={18}/> Plazos de Solicitud Online</h3>
                                        
                                        {/* BLOQUE 1: FECHAS PRINCIPALES (INSIGNIAS / GENERAL) */}
                                        <h4 style={{ margin: '15px 0 10px', color: '#4b5563', fontSize: '0.95rem' }}>
                                            {formData.modalidad === 'TRADICIONAL' 
                                                ? '1. Solicitud de Insignias / Varas' 
                                                : 'Plazo Único de Solicitud (General)'}
                                        </h4>
                                        <div className="form-grid-edicion grid-2-edicion">
                                            <div className="form-group-edicion">
                                                <label>Inicio Solicitud</label>
                                                <input 
                                                    type="datetime-local" 
                                                    name="inicio_solicitud" 
                                                    value={formData.inicio_solicitud || ''} 
                                                    onChange={handleChange} 
                                                    min={minDate} 
                                                    max={maxDate}
                                                />
                                            </div>
                                            <div className="form-group-edicion">
                                                <label>Fin Solicitud</label>
                                                <input 
                                                    type="datetime-local" 
                                                    name="fin_solicitud" 
                                                    value={formData.fin_solicitud || ''} 
                                                    onChange={handleChange}
                                                    min={minDate} 
                                                    max={maxDate}
                                                />
                                            </div>
                                        </div>

                                        {/* BLOQUE 2: FECHAS CIRIOS (Solo visible si es TRADICIONAL) 
                                        */}
                                        {formData.modalidad === 'TRADICIONAL' && (
                                            <>
                                                <h4 style={{ margin: '20px 0 10px', color: '#4b5563', fontSize: '0.95rem' }}>2. Solicitud de Cirios / General</h4>
                                                <div className="form-grid-edicion grid-2-edicion">
                                                    <div className="form-group-edicion">
                                                        <label>Inicio Solicitud</label>
                                                        <input 
                                                            type="datetime-local" 
                                                            name="inicio_solicitud_cirios" 
                                                            value={formData.inicio_solicitud_cirios || ''} 
                                                            onChange={handleChange} 
                                                            min={minDate} 
                                                            max={maxDate}
                                                        />
                                                    </div>
                                                    <div className="form-group-edicion">
                                                        <label>Fin Solicitud</label>
                                                        <input 
                                                            type="datetime-local" 
                                                            name="fin_solicitud_cirios" 
                                                            value={formData.fin_solicitud_cirios || ''} 
                                                            onChange={handleChange}
                                                            min={minDate} 
                                                            max={maxDate}
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

                            {/* --- BOTONES DE ACCIÓN --- */}
                            <div className="form-actions-edicion">
                                <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/home")}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn-save-edicion" disabled={saving}>
                                    <Save size={18} />
                                    {saving ? "Creando Acto..." : "Crear Acto"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminCreacionActo;