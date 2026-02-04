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
    Crown,
    Image as ImageIcon,
    X
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL

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

    const [previewUrl, setPreviewUrl] = useState(null);

    const [formData, setFormData] = useState({
        titulo: '',
        contenido: '',
        tipo_comunicacion: '',
        areas_interes: [],
        imagen_portada: null
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

    const getFullImageUrl = (pathOrBlob) => {
        if (!pathOrBlob) return null;
        
        if (pathOrBlob.startsWith('blob:') || pathOrBlob.startsWith('http')) {
            return pathOrBlob;
        }
        
        const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
        const path = pathOrBlob.startsWith('/') ? pathOrBlob : `/${pathOrBlob}`;
        
        return `${baseUrl}${path}`;
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
                        areas_interes: data.areas_interes || [],
                        imagen_portada: null
                    });

                    if (data.imagen_portada) {
                        setPreviewUrl(data.imagen_portada);
                    }
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

    useEffect(() => {
        return () => {
            if (previewUrl && previewUrl.startsWith('blob:')) {
                URL.revokeObjectURL(previewUrl);
            }
        };
    }, [previewUrl]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setFormData(prev => ({ ...prev, imagen_portada: file }));
            setPreviewUrl(URL.createObjectURL(file));
        }
    };

    const removeImage = () => {
        setFormData(prev => ({ ...prev, imagen_portada: null }));
        setPreviewUrl(null);
        const fileInput = document.getElementById('imagen_portada');
        if (fileInput) fileInput.value = "";
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
            const dataToSend = new FormData();
            dataToSend.append('titulo', formData.titulo);
            dataToSend.append('contenido', formData.contenido);
            dataToSend.append('tipo_comunicacion', formData.tipo_comunicacion);

            if (formData.imagen_portada instanceof File) {
                dataToSend.append('imagen_portada', formData.imagen_portada);
            }

            formData.areas_interes.forEach(id => {
                dataToSend.append('areas_interes', id);
            });

            await api.put(`api/comunicados/${id}/`, dataToSend, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setSuccessMsg("Comunicado actualizado correctamente.");
            setTimeout(() => navigate("/home"), 1500); 
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                setError("Error al guardar. Verifique los campos.");
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
            navigate("/home");
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
                                        <label>Imagen de Portada</label>
                                        
                                        {!previewUrl ? (
                                            <div 
                                                className="image-upload-area"
                                                onClick={() => document.getElementById('imagen_portada').click()}
                                                style={{
                                                    border: '2px dashed #d1d5db',
                                                    borderRadius: '8px',
                                                    padding: '20px',
                                                    textAlign: 'center',
                                                    cursor: 'pointer',
                                                    backgroundColor: '#f9fafb',
                                                    transition: 'all 0.2s',
                                                    color: '#6b7280'
                                                }}
                                            >
                                                <input 
                                                    type="file" 
                                                    id="imagen_portada"
                                                    name="imagen_portada"
                                                    accept="image/*"
                                                    onChange={handleImageChange}
                                                    style={{ display: 'none' }}
                                                />
                                                <ImageIcon size={32} style={{ margin: '0 auto 10px', color: '#9ca3af' }}/>
                                                <p style={{ fontSize: '0.9rem', margin: 0 }}>Haz clic para subir o cambiar la imagen</p>
                                                <p style={{ fontSize: '0.8rem', color: '#9ca3af', margin: '5px 0 0' }}>JPG, PNG (Max. 5MB)</p>
                                            </div>
                                        ) : (
                                            // ESTADO: CON IMAGEN (Previsualización)
                                            <div className="image-preview-container" style={{ position: 'relative', width: 'fit-content' }}>
                                                <img 
                                                    src={getFullImageUrl(previewUrl)} 
                                                    alt="Portada" 
                                                    style={{ 
                                                        maxWidth: '100%', 
                                                        maxHeight: '300px', 
                                                        borderRadius: '8px',
                                                        border: '1px solid #e5e7eb',
                                                        display: 'block'
                                                    }}
                                                    onError={(e) => {
                                                        e.target.style.display = 'none';
                                                    }}
                                                />
                                                
                                                {/* Botón cambiar imagen (sobre la imagen) */}
                                                <div style={{
                                                    position: 'absolute',
                                                    bottom: '10px',
                                                    right: '10px',
                                                    display: 'flex',
                                                    gap: '8px'
                                                }}>
                                                    <button
                                                        type="button"
                                                        onClick={() => document.getElementById('imagen_portada_edit').click()}
                                                        style={{
                                                            background: 'rgba(255, 255, 255, 0.9)',
                                                            border: '1px solid #e5e7eb',
                                                            borderRadius: '6px',
                                                            padding: '6px 12px',
                                                            cursor: 'pointer',
                                                            fontSize: '0.85rem',
                                                            fontWeight: '600',
                                                            color: '#374151',
                                                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                                        }}
                                                    >
                                                        Cambiar
                                                    </button>
                                                    <input 
                                                        type="file" 
                                                        id="imagen_portada_edit"
                                                        accept="image/*"
                                                        onChange={handleImageChange}
                                                        style={{ display: 'none' }}
                                                    />
                                                </div>

                                                <button
                                                    type="button"
                                                    onClick={removeImage}
                                                    style={{
                                                        position: 'absolute',
                                                        top: '10px',
                                                        right: '10px',
                                                        background: 'rgba(255, 255, 255, 0.9)',
                                                        border: 'none',
                                                        borderRadius: '50%',
                                                        padding: '5px',
                                                        cursor: 'pointer',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                                    }}
                                                    title="Eliminar imagen"
                                                >
                                                    <X size={18} color="#ef4444" />
                                                </button>
                                            </div>
                                        )}
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