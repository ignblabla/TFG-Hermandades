import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api';
import '../styles/AdminEdicionActo.css';
import { 
    Save,
    FileText,
    Users,
    Trash2,
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

function AdminEdicionComunicado() {
    const navigate = useNavigate();
    const { id } = useParams();

    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    const [currentUser, setCurrentUser] = useState(null);
    const [areasDisponibles, setAreasDisponibles] = useState([]);

    const [formData, setFormData] = useState({
        titulo: '',
        contenido: '',
        tipo_comunicacion: '',
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

                const resComunicado = await api.get(`api/comunicados/${id}/`);
                const data = resComunicado.data;

                if (isMounted) {
                    setFormData({
                        titulo: data.titulo,
                        contenido: data.contenido,
                        tipo_comunicacion: data.tipo_comunicacion,
                        areas_interes: data.areas_interes || [] 
                    });
                }

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar los datos del comunicado.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [id]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const toggleArea = (areaId) => {
        setFormData(prev => {
            const current = prev.areas_interes;
            if (current.includes(areaId)) {
                return { ...prev, areas_interes: current.filter(id => id !== areaId) };
            } else {
                return { ...prev, areas_interes: [...current, areaId] };
            }
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        try {
            await api.put(`api/comunicados/${id}/`, formData);
            setSuccessMsg("Comunicado actualizado correctamente.");
            
            setTimeout(() => navigate("/admin/comunicados"), 1500); 
        } catch (err) {
            if (err.response && err.response.data) {
                setError(JSON.stringify(err.response.data));
            } else {
                setError("Error al guardar los cambios.");
            }
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm("¿Estás seguro de que deseas eliminar este comunicado? Esta acción es irreversible.")) {
            return;
        }

        setDeleting(true);
        try {
            await api.delete(`api/comunicados/${id}/`);
            navigate("/admin/comunicados");
        } catch (err) {
            console.error(err);
            setError("Error al eliminar el comunicado. Verifica tus permisos.");
            setDeleting(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando datos...</div>;

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

            {/* CONTENIDO PRINCIPAL */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Editar Comunicado</div>
                
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        {/* ALERTAS */}
                        {error && (
                            <div className="alert-banner-edicion error-edicion">
                                <AlertCircle size={20} /> <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-edicion success-edicion">
                                <CheckCircle size={20} /> <span>{successMsg}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            {/* SECCIÓN 1: DATOS */}
                            <div className="form-section-edicion">
                                <h3 className="section-title-edicion"><FileText size={18}/> Datos del Comunicado</h3>
                                <div className="form-grid-edicion grid-2-edicion">
                                    
                                    <div className="form-group-creacion-comunicado">
                                        <label>Título *</label>
                                        <input 
                                            type="text" 
                                            name="titulo" 
                                            value={formData.titulo} 
                                            onChange={handleChange} 
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
                                                <option key={opt.value} value={opt.value}>{opt.label}</option>
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
                                            className="textarea-standard-creacion-comunicado"
                                            required
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN 2: ÁREAS DE INTERÉS (M2M) */}
                            <div className="form-section-creacion-comunicado admin-section-creacion-comunicado">
                                <h3 className="section-title-creacion-comunicado admin-title-creacion-comunicado">
                                    <Users size={18}/> Áreas de Interés (Destinatarios)
                                </h3>

                                <div className="help-text-container-creacion-comunicado">
                                    <small>
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
                            </div>

                            {/* ACCIONES DEL FORMULARIO */}
                            <div className="form-actions-edicion" style={{ justifyContent: 'space-between', marginTop: '30px' }}>
                                
                                <button 
                                    type="button" 
                                    onClick={handleDelete} 
                                    disabled={deleting}
                                    style={{ 
                                        backgroundColor: '#fee2e2', 
                                        color: '#991b1b', 
                                        border: '1px solid #fca5a5', 
                                        padding: '10px 20px', 
                                        borderRadius: '6px', 
                                        cursor: 'pointer', 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        gap: '8px',
                                        fontSize: '0.9rem',
                                        fontWeight: '500'
                                    }} 
                                >
                                    <Trash2 size={18} />
                                    {deleting ? "Eliminando..." : "Eliminar Comunicado"}
                                </button>

                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/admin/comunicados")}>
                                        Cancelar
                                    </button>
                                    <button type="submit" className="btn-save-edicion" disabled={saving}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <Save size={18} />
                                            {saving ? "Guardando..." : "Guardar Cambios"}
                                        </div>
                                    </button>
                                </div>
                            </div>

                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminEdicionComunicado;