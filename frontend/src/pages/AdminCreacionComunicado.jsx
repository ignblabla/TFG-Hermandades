import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import '../styles/AdminCreacionComunicado.css'; 
import { 
    Save, 
    FileText, 
    Users, 
    MessageSquare, 
    AlertCircle, 
    CheckCircle, 
    Info,
    Church,
    Heart,
    Sun,
    Hammer,
    BookOpen,
    Crown
} from "lucide-react";

function AdminCreacionComunicado() {
    const navigate = useNavigate();
    
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    const [currentUser, setCurrentUser] = useState(null);
    const [areasDisponibles, setAreasDisponibles] = useState([]);

    const [formData, setFormData] = useState({
        titulo: '',
        contenido: '',
        tipo_comunicacion: 'GENERAL',
        areas_interes: []
    });

    const tiposComunicacion = [
        { value: 'GENERAL', label: 'General' },
        { value: 'INFORMATIVO', label: 'Informativo' },
        { value: 'CULTOS', label: 'Cultos' },
        { value: 'SECRETARIA', label: 'Secretaría' },
        { value: 'URGENTE', label: 'Urgente' },
        { value: 'EVENTOS', label: 'Eventos y Caridad' },
    ];

    const getAreaIcon = (nombreArea) => {
        switch (nombreArea) {
            case 'ACOLITOS': return <Church size={18} />;
            case 'COSTALEROS': return <Users size={18} />;
            case 'CARIDAD': return <Heart size={18} />;
            case 'JUVENTUD': return <Sun size={18} />;
            case 'PRIOSTIA': return <Hammer size={18} />;
            case 'CULTOS_FORMACION': return <BookOpen size={18} />;
            case 'PATRIMONIO': return <Church size={18} />;
            case 'DIPUTACION_MAYOR_GOBIERNO': return <Crown size={18} />;
            default: return <Users size={18} />;
        }
    };

    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                if (isMounted) setCurrentUser(resUser.data);

                const resAreas = await api.get("api/areas-interes/");
                if (isMounted) setAreasDisponibles(resAreas.data);

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al conectar con el servidor.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, []);

    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const toggleArea = (areaId) => {
        setFormData(prev => {
            const currentAreas = prev.areas_interes;
            if (currentAreas.includes(areaId)) {
                return { ...prev, areas_interes: currentAreas.filter(id => id !== areaId) };
            } else {
                return { ...prev, areas_interes: [...currentAreas, areaId] };
            }
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        if (!formData.titulo.trim() || !formData.contenido.trim()) {
            setError("El título y el contenido son obligatorios.");
            setSaving(false);
            window.scrollTo(0, 0);
            return;
        }

        try {
            await api.post('api/comunicados/', formData);
            
            setSuccessMsg("Comunicado emitido correctamente.");

            setTimeout(() => {
                navigate("/home");
            }, 1500);

        } catch (err) {
            console.error(err);
            if (err.response) {
                if (err.response.status === 403) {
                    setError("No tienes permisos (Solo Admins o Junta de Gobierno).");
                } else if (err.response.data) {
                    const errorData = err.response.data;
                    if (errorData.detail) {
                        setError(errorData.detail);
                    } else {
                        const errorMessages = Object.entries(errorData)
                            .map(([key, msg]) => {
                                const fieldName = key === 'non_field_errors' ? 'Error' : key.toUpperCase();
                                return `${fieldName}: ${Array.isArray(msg) ? msg[0] : msg}`;
                            })
                            .join(" | ");
                        setError(errorMessages);
                    }
                }
            } else {
                setError("Error de conexión al enviar el comunicado.");
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

    if (loading) return <div className="loading-screen">Cargando panel...</div>;

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
                <div className="text-dashboard">Nuevo Comunicado</div>
                
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        {/* BANNER DE ERRORES/ÉXITO */}
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
                            {/* SECCIÓN 1: DATOS BÁSICOS */}
                            <div className="form-section-creacion-comunicado">
                                <h3 className="section-title-creacion-comunicado"><FileText size={18}/> Información del Comunicado</h3>
                                <div className="form-grid-creacion-comunicado grid-2-creacion-comunicado">
                                    
                                    {/* Título */}
                                    <div className="form-group-creacion-comunicado">
                                        <label>Título *</label>
                                        <input 
                                            type="text" 
                                            name="titulo" 
                                            value={formData.titulo} 
                                            onChange={handleChange} 
                                            placeholder="Ej: Horario de reparto de papeletas"
                                            required 
                                        />
                                    </div>

                                    <div className="form-group-creacion-comunicado">
                                        <label>Tipo de Comunicación *</label>
                                        <select 
                                            name="tipo_comunicacion" 
                                            value={formData.tipo_comunicacion} 
                                            onChange={handleChange}
                                            required
                                        >
                                            {tiposComunicacion.map(opt => (
                                                <option key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group-creacion-comunicado span-2-creacion-comunicado">
                                        <label>Contenido del Mensaje *</label>
                                        <textarea 
                                            name="contenido" 
                                            value={formData.contenido} 
                                            onChange={handleChange}
                                            rows="6"
                                            placeholder="Escriba aquí el cuerpo de la noticia..."
                                            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db', resize: 'vertical' }}
                                            required
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN 2: DESTINATARIOS (Áreas de Interés) */}
                            <div className="form-section-creacion-comunicado admin-section-creacion-comunicado">
                                <h3 className="section-title-creacion-comunicado admin-title-creacion-comunicado">
                                    <Users size={18}/> Áreas de Interés (Destinatarios)
                                </h3>
                                
                                <div style={{ marginBottom: '15px' }}>
                                    <small style={{ color: '#6b7280' }}>
                                        Selecciona las áreas a las que va dirigido este comunicado. Si no seleccionas ninguna, 
                                        el comunicado se guardará como <strong>Borrador</strong> y no aparecerá en el muro de los hermanos.
                                    </small>
                                </div>

                                <div className="areas-grid-creacion-comunicado">
                                    {areasDisponibles.map(area => {
                                        const isSelected = formData.areas_interes.includes(area.id);
                                        
                                        return (
                                            <div 
                                                key={area.id}
                                                onClick={() => toggleArea(area.id)}
                                                className={`area-card-creacion-comunicado ${isSelected ? 'selected' : ''}`}
                                            >
                                                <input 
                                                    type="checkbox" 
                                                    checked={isSelected} 
                                                    onChange={() => {}}
                                                />

                                                <div className="area-icon-creacion-comunicado">
                                                    {getAreaIcon(area.nombre_area)}
                                                </div>

                                                <span className="area-name-creacion-comunicado">
                                                    {area.get_nombre_area_display || area.nombre_area}
                                                </span>
                                            </div>
                                        )
                                    })}
                                </div>

                                {formData.areas_interes.length === 0 && (
                                    <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#fff7ed', borderRadius: '6px', borderLeft: '4px solid #f97316', fontSize: '0.85rem', color: '#9a3412', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Info size={16} />
                                        <span>Este comunicado se guardará en modo <strong>Borrador</strong> (sin destinatarios).</span>
                                    </div>
                                )}
                            </div>

                            {/* BOTONES DE ACCIÓN */}
                            <div className="form-actions-edicion">
                                <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/home")}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn-save-edicion" disabled={saving}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Save size={18} />
                                        {saving ? "Emitiendo..." : "Emitir Comunicado"}
                                    </div>
                                </button>
                            </div>

                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminCreacionComunicado;