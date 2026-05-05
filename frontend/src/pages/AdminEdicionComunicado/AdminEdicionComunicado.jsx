import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminCreacionComunicado/AdminCreacionComunicado.css'
import { Save, FileText, Users, Trash2, AlertCircle, CheckCircle, Church, Heart, Sun, Hammer, BookOpen, Crown, Image as ImageIcon, X } from "lucide-react";

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
            case 'TODOS_HERMANOS': return <Users size={18} />;
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
            const listaAreas = resAreas.data.sort((a, b) => {
                if (a.nombre_area === 'TODOS_HERMANOS') return -1;
                if (b.nombre_area === 'TODOS_HERMANOS') return 1;

                if (a.nombre_area === 'DIPUTACION_MAYOR_GOBIERNO') return 1;
                if (b.nombre_area === 'DIPUTACION_MAYOR_GOBIERNO') return -1;

                return a.nombre_area.localeCompare(b.nombre_area);
            });
            if (isMounted) setAreasDisponibles(listaAreas);

            const resComunicado = await api.get(`api/comunicados/${id}/`);
            const data = resComunicado.data;

            if (isMounted) {
                const areasIds = (data.areas_interes || []).map(nombreRecibido => {
                    const areaEncontrada = listaAreas.find(a => 
                        a.get_nombre_area_display === nombreRecibido || 
                        a.nombre_area === nombreRecibido
                    );
                    return areaEncontrada ? areaEncontrada.id : null;
                }).filter(id => id !== null);

                setFormData({
                    titulo: data.titulo,
                    contenido: data.contenido,
                    tipo_comunicacion: data.tipo_comunicacion,
                    areas_interes: areasIds,
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
        setError("");
        setSuccessMsg("");

        if (formData.areas_interes.length === 0) {
            setError("Debe seleccionar al menos un área de interés. Si es para todos, elija 'Todos los Hermanos'.");
            return;
        }

        setSaving(true);

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

            await api.patch(`api/comunicados/${id}/`, dataToSend); 

            setSuccessMsg("Comunicado actualizado correctamente.");
            setTimeout(() => navigate("/noticias"), 1500);
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                console.log("Detalle error servidor:", err.response.data);
                setError("Error al guardar: " + JSON.stringify(err.response.data));
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

    const handleVincularTelegram = (e) => {
        e.preventDefault();

        if (currentUser && currentUser.enlace_vinculacion_telegram) {
            window.open(currentUser.enlace_vinculacion_telegram, '_blank');
        } else {
            console.error("El enlace de Telegram no está disponible.");
            alert("Hubo un problema al cargar tu enlace personal de Telegram.");
        }
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
                        <a href="/editar-mi-perfil">
                            <i className="bx bx-user"></i>
                            <span className="link_name-dashboard">Mi perfil</span>
                        </a>
                        <span className="tooltip-dashboard">Mi perfil</span>
                    </li>
                    <li>
                        <a href="/noticias">
                            <i className="bx bx-news"></i>
                            <span className="link_name-dashboard">Mis noticias</span>
                        </a>
                        <span className="tooltip-dashboard">Mis noticias</span>
                    </li>
                    <li>
                        <a href="/listado-cuotas">
                            <i className="bx bx-wallet"></i>
                            <span className="link_name-dashboard">Mis cuotas</span>
                        </a>
                        <span className="tooltip-dashboard">Mis cuotas</span>
                    </li>
                    <li>
                        <a href="/mis-papeletas-de-sitio">
                            <i className="bx bx-file"></i>
                            <span className="link_name-dashboard">Mis papeletas</span>
                        </a>
                        <span className="tooltip-dashboard">Mis papeletas</span>
                    </li>
                    <li>
                        <a href="/listado-actos">
                            <i className="bx bx-calendar-event"></i>
                            <span className="link_name-dashboard">Actos</span>
                        </a>
                        <span className="tooltip-dashboard">Actos</span>
                    </li>
                    <li>
                        <a href="/areas-de-interes">
                            <i className="bx bx-list-ul"></i>
                            <span className="link_name-dashboard">Áreas de Interés</span>
                        </a>
                        <span className="tooltip-dashboard">Áreas de Interés</span>
                    </li>
                    <li>
                        <a 
                            href="#" 
                            onClick={!currentUser?.telegram_chat_id ? handleVincularTelegram : (e) => e.preventDefault()}
                            style={{ 
                                cursor: currentUser?.telegram_chat_id ? 'default' : 'pointer',
                                opacity: currentUser?.telegram_chat_id ? 0.6 : 1
                            }}
                        >
                            <i className="bx bxl-telegram"></i>
                            <span className="link_name-dashboard">
                                {currentUser?.telegram_chat_id ? "Telegram Vinculado ✅" : "Vincular Telegram"}
                            </span>
                        </a>
                        <span className="tooltip-dashboard">
                            {currentUser?.telegram_chat_id ? "Ya vinculado" : "Vincular Telegram"}
                        </span>
                    </li>
                    {currentUser?.esAdmin && (
                        <li>
                            <a href="/censo-hermanos">
                                <i className="bx bx-group"></i>
                                <span className="link_name-dashboard">Censo</span>
                            </a>
                            <span className="tooltip-dashboard">Censo</span>
                        </li>
                    )}
                    
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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                <div className="dashboard-split-layout-solicitud">
                    <div className="dashboard-panel-crear-comunicado">
                        
                        <div className="historical-header-container-crear-comunicado">
                            <h1 className="historical-header-title-crear-comunicado">
                                EDITAR COMUNICADO: {formData.titulo ? formData.titulo.toUpperCase() : ''}
                            </h1>
                        </div>

                        {error && (
                            <div className="alert-banner-edicion error-edicion" style={{ margin: '0 30px 20px' }}>
                                <AlertCircle size={20} /> <span>{error}</span>
                            </div>
                        )}
                        
                        {successMsg && (
                            <div className="alert-banner-edicion success-edicion" style={{ margin: '0 30px 20px' }}>
                                <CheckCircle size={20} /> <span>{successMsg}</span>
                            </div>
                        )}

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                            <span className="plazos-text">Información del comunicado</span>
                            <div className="plazos-line"></div>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-container-crear-comunicado">
                                <div className="form-grid-4-crear-comunicado">
                                    
                                    <div className="form-group-crear-comunicado span-3-crear-comunicado">
                                        <label htmlFor="titulo" className="form-label-crear-comunicado">
                                            Título *
                                        </label>
                                        <div className="input-wrapper-crear-comunicado">
                                            <input 
                                                type="text" 
                                                id="titulo"
                                                name="titulo" 
                                                value={formData.titulo} 
                                                onChange={handleChange} 
                                                required 
                                                className="form-control-crear-comunicado"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-comunicado">
                                        <label htmlFor="tipo_comunicacion" className="form-label-crear-comunicado">
                                            Tipo de comunicación *
                                        </label>
                                        <div className="input-wrapper-crear-comunicado">
                                            <select 
                                                id="tipo_comunicacion"
                                                name="tipo_comunicacion" 
                                                value={formData.tipo_comunicacion} 
                                                onChange={handleChange}
                                                required
                                                className="form-control-crear-comunicado"
                                            >
                                                {tiposComunicacion.map(opt => (
                                                    <option key={opt.value} value={opt.value}>
                                                        {opt.label}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>

                                    <div className="form-group-crear-comunicado span-full-crear-comunicado">
                                        <label htmlFor="contenido" className="form-label-crear-comunicado">
                                            Contenido del mensaje *
                                        </label>
                                        <div className="input-wrapper-crear-comunicado">
                                            <textarea 
                                                id="contenido"
                                                name="contenido" 
                                                value={formData.contenido} 
                                                onChange={handleChange}
                                                rows="5"
                                                className="form-control-crear-comunicado textarea-crear-comunicado"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-comunicado span-full-crear-comunicado">
                                        <label className="form-label-crear-comunicado">
                                            Imagen de portada
                                        </label>
                                        
                                        {!previewUrl ? (
                                            <div 
                                                className="image-upload-area-crear-comunicado"
                                                onClick={() => document.getElementById('imagen_portada').click()}
                                            >
                                                <input 
                                                    type="file" 
                                                    id="imagen_portada"
                                                    name="imagen_portada"
                                                    accept="image/*"
                                                    onChange={handleImageChange}
                                                    style={{ display: 'none' }}
                                                />
                                                <ImageIcon size={32} style={{ margin: '0 auto 10px' }}/>
                                                <p>Haz clic para subir o cambiar la imagen</p>
                                                <small>JPG, PNG (Max. 5MB) - <strong>Formato Horizontal obligatorio</strong></small>
                                            </div>
                                        ) : (
                                            <div className="image-preview-container-crear-comunicado" style={{ position: 'relative' }}>
                                                <img 
                                                    src={getFullImageUrl(previewUrl)} 
                                                    alt="Vista previa" 
                                                    className="image-preview-img-crear-comunicado"
                                                    onError={(e) => {
                                                        e.target.style.display = 'none';
                                                    }}
                                                />
                                                
                                                <div className="image-actions-overlay" style={{ position: 'absolute', top: '10px', left: '10px' }}>
                                                    <button
                                                        type="button"
                                                        onClick={() => document.getElementById('imagen_portada_edit').click()}
                                                        className="btn-change-image"
                                                        style={{ padding: '6px 12px', background: 'rgba(0,0,0,0.6)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}
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
                                                    className="btn-delete-image-crear-comunicado"
                                                    title="Eliminar imagen"
                                                >
                                                    <X size={18} color="#ef4444" />
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                </div>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                <span className="plazos-text">Áreas o sectores a los que está dirigido el comunicado</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="form-container-crear-comunicado">
                                <div className="help-text-container-crear-comunicado">
                                    <small>
                                        Selecciona las áreas a las que va dirigido este comunicado. Si no seleccionas ninguna, 
                                        el comunicado se guardará como <strong>Borrador</strong> y no aparecerá en el muro de los hermanos.
                                    </small>
                                </div>

                                <div className="areas-grid-crear-comunicado">
                                    {areasDisponibles.map(area => {
                                        const isSelected = formData.areas_interes.includes(area.id);
                                        
                                        return (
                                            <div 
                                                key={area.id}
                                                onClick={() => toggleArea(area.id)}
                                                className={`area-card-crear-comunicado ${isSelected ? 'selected' : ''}`}
                                            >
                                                <input 
                                                    type="checkbox" 
                                                    checked={isSelected} 
                                                    onChange={() => {}}
                                                    className="area-checkbox-crear-comunicado"
                                                />

                                                <div className="area-icon-crear-comunicado">
                                                    {getAreaIcon(area.nombre_area)}
                                                </div>

                                                <span className="area-name-crear-comunicado">
                                                    {area.get_nombre_area_display || area.nombre_area}
                                                </span>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>

                            <div className="form-actions-crear-comunicado" style={{ justifyContent: 'space-between' }}>
                                
                                <button 
                                    type="button" 
                                    onClick={handleDelete} 
                                    disabled={deleting}
                                    className="btn-delete-puesto"
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', borderRadius: '6px', border: 'none', backgroundColor: '#fee2e2', color: '#ef4444', cursor: 'pointer', fontWeight: '500' }}
                                >
                                    <Trash2 size={18} />
                                    {deleting ? "Eliminando..." : "Eliminar Comunicado"}
                                </button>

                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button 
                                        type="button" 
                                        className="btn-cancel-crear-comunicado" 
                                        onClick={() => navigate("/admin/comunicados")}
                                    >
                                        Cancelar
                                    </button>
                                    
                                    <button 
                                        type="submit" 
                                        className="btn-save-crear-comunicado" 
                                        disabled={saving}
                                    >
                                        <Save size={18} />
                                        {saving ? "Guardando..." : "Guardar Cambios"}
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