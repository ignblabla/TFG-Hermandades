import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../AdminCreacionActo/AdminCrearActo.css';
import { Save, FileText, Settings, ShieldAlert, CheckCircle, Clock, AlertCircle, Lock } from "lucide-react";
import ResumenActoCard from '../../components/ResumenActoCard';

function AdminCrearActo() {
    const navigate = useNavigate();

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

    // 1. Inicializamos modalidad vacía
    const [formData, setFormData] = useState({
        nombre: '',
        lugar: '',
        descripcion: '',
        fecha: '',
        tipo_acto: '',
        modalidad: '',
        inicio_solicitud: '',
        fin_solicitud: '',
        inicio_solicitud_cirios: '',
        fin_solicitud_cirios: ''
    });

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

        if (name === 'tipo_acto') {
            const tipoSeleccionado = tiposActo.find(t => t.tipo === value);
            if (tipoSeleccionado) {
                setRequierePapeleta(tipoSeleccionado.requiere_papeleta);
                
                if (!tipoSeleccionado.requiere_papeleta) {
                    newData.inicio_solicitud = '';
                    newData.fin_solicitud = '';
                    newData.inicio_solicitud_cirios = '';
                    newData.fin_solicitud_cirios = '';
                    newData.modalidad = '';
                } else {
                    newData.modalidad = '';
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

        if (!requierePapeleta) {
            payload.modalidad = null;
        }

        try {
            await api.post('api/actos/crear/', payload);
            setSuccessMsg("Acto creado correctamente.");
            
            setTimeout(() => {
                navigate("/home");
            }, 1500);

        } catch (err) {
            console.error(err);
            if (err.response?.status === 500) {
                setError("Error interno del servidor. Revisa que las fechas sean lógicas.");
            } else {
                const errorData = err.response?.data;
                if (typeof errorData === 'object' && errorData !== null) {
                    const mensajesLimpios = Object.values(errorData)
                        .flat()
                        .join(" | ");
                    setError(mensajesLimpios || "Error al validar los datos del acto.");
                } else {
                    setError(typeof errorData === 'string' ? errorData : "Error al crear el acto.");
                }
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
                <div className="text-dashboard">Crear nuevo acto</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="dashboard-layout-wrapper">
                        <form className="container-crear-acto" onSubmit={handleSubmit}>
                            
                            <h3 className="section-title-crear-acto">
                                <FileText size={18} /> Información general
                            </h3>

                            {/* 4. Bloques de Error y Éxito integrados DENTRO del form */}
                            {error && (
                                <div className="alert-error-crear-acto" style={{ 
                                    backgroundColor: '#fee2e2', 
                                    color: '#dc2626', 
                                    padding: '15px', 
                                    borderRadius: '8px', 
                                    marginBottom: '20px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px'
                                }}>
                                    <AlertCircle size={20} />
                                    <div>{error}</div>
                                </div>
                            )}

                            {successMsg && (
                                <div className="alert-success-crear-acto" style={{ 
                                    backgroundColor: '#dcfce3', 
                                    color: '#16a34a', 
                                    padding: '15px', 
                                    borderRadius: '8px', 
                                    marginBottom: '20px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px'
                                }}>
                                    <CheckCircle size={20} />
                                    <div>{successMsg}</div>
                                </div>
                            )}

                            <div className="form-group-crear-acto">
                                <label htmlFor="nombre">Nombre del acto</label>
                                <input 
                                    type="text"
                                    id="nombre"
                                    name="nombre"
                                    value={formData.nombre}
                                    onChange={handleChange}
                                    placeholder={`Ej: Estación de Penitencia ${currentYear}`}
                                    className="form-input-crear-acto"
                                    required
                                />
                            </div>

                            <div className="form-group-crear-acto">
                                <label htmlFor="lugar">Lugar de celebración</label>
                                <input
                                    type="text"
                                    id="lugar"
                                    name="lugar"
                                    value={formData.lugar}
                                    onChange={handleChange}
                                    placeholder="Ej: Parroquia de San Ildefonso"
                                    className="form-input-crear-acto"
                                    required
                                />
                            </div>

                            <div className="form-row-2-cols-crear-acto">
                                <div className="form-group-crear-acto">
                                    <label htmlFor="tipo_acto">Tipo de acto</label>
                                    <select
                                        id="tipo_acto"
                                        name="tipo_acto"
                                        value={formData.tipo_acto}
                                        onChange={handleChange}
                                        className="form-input-crear-acto"
                                        required
                                    >
                                        <option value="" disabled>Selecciona un tipo</option>
                                        {tiposActo.map((tipo, index) => (
                                            <option key={index} value={tipo.tipo}>
                                                {tipo.tipo.replace(/_/g, ' ')}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="form-group-crear-acto">
                                    <label htmlFor="fecha">Fecha y hora</label>
                                    <input
                                        type="datetime-local"
                                        id="fecha"
                                        name="fecha"
                                        value={formData.fecha}
                                        onChange={handleChange}
                                        min={minDate}
                                        max={maxDate}
                                        className="form-input-crear-acto"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="form-group-crear-acto">
                                <label htmlFor="descripcion">Descripción</label>
                                <textarea
                                    id="descripcion"
                                    name="descripcion"
                                    value={formData.descripcion}
                                    onChange={handleChange}
                                    placeholder="Añade detalles adicionales sobre el acto..."
                                    className="form-input-crear-acto textarea-crear-acto"
                                    rows="4"
                                />
                            </div>

                            <h3 className="section-title-crear-acto mt-section">
                                <Settings size={18}/> Configuración de Reparto
                            </h3>
                            
                            <div className="form-group-crear-acto">
                                <label htmlFor="modalidad">Modalidad de Reparto</label>
                                <select 
                                    id="modalidad"
                                    name="modalidad" 
                                    value={formData.modalidad} 
                                    onChange={handleChange}
                                    className="form-input-crear-acto"
                                    disabled={!requierePapeleta}
                                    required={requierePapeleta} // 3. Se hace obligatorio si requiere papeleta
                                >
                                    {/* Opción por defecto vacía */}
                                    <option value="" disabled>Seleccione una opción</option>
                                    <option value="TRADICIONAL">Tradicional (Fases separadas)</option>
                                    <option value="UNIFICADO">Unificado / Express (Todo a la vez)</option>
                                </select>
                                <small className="form-help-text-crear-acto">
                                    {!requierePapeleta 
                                        ? 'Este tipo de acto no requiere reparto de papeletas.'
                                        : formData.modalidad === 'TRADICIONAL' 
                                            ? 'Primero se asignan insignias, luego cirios.' 
                                            : formData.modalidad === 'UNIFICADO'
                                                ? 'Todos los puestos se asignan en un mismo plazo.'
                                                : 'Seleccione una modalidad para continuar.'}
                                </small>
                            </div>

                            <h3 className="section-title-crear-acto mt-section">
                                <Clock size={18}/> Plazos de Solicitud Online
                            </h3>
                            
                            <h4 className="subtitle-crear-acto">
                                {formData.modalidad === 'TRADICIONAL' && requierePapeleta
                                    ? '1. Solicitud de Insignias / Varas' 
                                    : 'Plazo Único de Solicitud (General)'}
                            </h4>
                            
                            <div className="form-row-2-cols-crear-acto">
                                <div className="form-group-crear-acto">
                                    <label htmlFor="inicio_solicitud">Inicio Solicitud</label>
                                    <div className="input-wrapper-crear-acto">
                                        <input 
                                            type="datetime-local" 
                                            id="inicio_solicitud"
                                            name="inicio_solicitud" 
                                            value={formData.inicio_solicitud || ''} 
                                            onChange={handleChange} 
                                            min={minDate} max={maxDate}
                                            className={`form-input-crear-acto ${!requierePapeleta ? 'has-icon' : ''}`}
                                            disabled={!requierePapeleta}
                                        />
                                        {!requierePapeleta && <Lock className="input-lock-icon" size={16} />}
                                    </div>
                                </div>
                                <div className="form-group-crear-acto">
                                    <label htmlFor="fin_solicitud">Fin Solicitud</label>
                                    <div className="input-wrapper-crear-acto">
                                        <input 
                                            type="datetime-local" 
                                            id="fin_solicitud"
                                            name="fin_solicitud" 
                                            value={formData.fin_solicitud || ''} 
                                            onChange={handleChange}
                                            min={minDate} max={maxDate}
                                            className={`form-input-crear-acto ${!requierePapeleta ? 'has-icon' : ''}`}
                                            disabled={!requierePapeleta}
                                        />
                                        {!requierePapeleta && <Lock className="input-lock-icon" size={16} />}
                                    </div>
                                </div>
                            </div>

                            <h4 className="subtitle-crear-acto mt-subtitle">
                                2. Solicitud de Cirios / General
                            </h4>
                            
                            <div className="form-row-2-cols-crear-acto">
                                <div className="form-group-crear-acto">
                                    <label htmlFor="inicio_solicitud_cirios">Inicio Solicitud</label>
                                    <div className="input-wrapper-crear-acto">
                                        <input 
                                            type="datetime-local" 
                                            id="inicio_solicitud_cirios"
                                            name="inicio_solicitud_cirios" 
                                            value={formData.inicio_solicitud_cirios || ''} 
                                            onChange={handleChange} 
                                            min={minDate} max={maxDate}
                                            className={`form-input-crear-acto ${(!requierePapeleta || formData.modalidad === 'UNIFICADO') ? 'has-icon' : ''}`}
                                            disabled={!requierePapeleta || formData.modalidad === 'UNIFICADO'}
                                        />
                                        {(!requierePapeleta || formData.modalidad === 'UNIFICADO') && <Lock className="input-lock-icon" size={16} />}
                                    </div>
                                </div>
                                <div className="form-group-crear-acto">
                                    <label htmlFor="fin_solicitud_cirios">Fin Solicitud</label>
                                    <div className="input-wrapper-crear-acto">
                                        <input 
                                            type="datetime-local" 
                                            id="fin_solicitud_cirios"
                                            name="fin_solicitud_cirios" 
                                            value={formData.fin_solicitud_cirios || ''} 
                                            onChange={handleChange}
                                            min={minDate} max={maxDate}
                                            className={`form-input-crear-acto ${(!requierePapeleta || formData.modalidad === 'UNIFICADO') ? 'has-icon' : ''}`}
                                            disabled={!requierePapeleta || formData.modalidad === 'UNIFICADO'}
                                        />
                                        {(!requierePapeleta || formData.modalidad === 'UNIFICADO') && <Lock className="input-lock-icon" size={16} />}
                                    </div>
                                </div>
                            </div>
                            
                            {requierePapeleta && formData.modalidad === 'TRADICIONAL' && (
                                <div className="alert-info-crear-acto">
                                    <ShieldAlert size={18} />
                                    <span>Recuerda: En modalidad tradicional, la solicitud de cirios no puede comenzar antes de que termine la de insignias.</span>
                                </div>
                            )}

                            <div className="form-actions-crear-acto">
                                <button 
                                    type="button" 
                                    className="btn-cancel-crear-acto" 
                                    onClick={() => navigate("/home")}
                                >
                                    Cancelar
                                </button>
                                
                                <button 
                                    type="submit" 
                                    className="btn-save-crear-acto" 
                                    disabled={saving}
                                >
                                    <Save size={18} />
                                    {saving ? "Creando Acto..." : "Crear Acto"}
                                </button>
                            </div>
                        </form>

                        <div className="container-cultos-card">
                            <ResumenActoCard formData={formData} />
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminCrearActo;