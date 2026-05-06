import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../AdminCreacionComunicado/AdminCreacionComunicado.css'
import { Save, FileText, Users, AlertCircle, CheckCircle, Church, Heart, Sun, Hammer, BookOpen, Crown, Image as ImageIcon, X, Headphones } from "lucide-react";

function AdminCreacionComunicado() {
    const navigate = useNavigate();
    
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    const [currentUser, setCurrentUser] = useState(null);
    const [areasDisponibles, setAreasDisponibles] = useState([]);

    const [previewUrl, setPreviewUrl] = useState(null);

    const [formData, setFormData] = useState({
        titulo: '',
        contenido: '',
        tipo_comunicacion: 'GENERAL',
        areas_interes: [],
        imagen_portada: null,
        generar_podcast: false
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

    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                const user = resUser.data;
                
                if (isMounted) setCurrentUser(user);

                if (!user.esAdmin) {
                    alert("No tienes permisos para crear comunicados.");
                    navigate("/noticias");
                    return;
                }

                const resAreas = await api.get("api/areas-interes/");
                if (isMounted) {
                    const sortedAreas = resAreas.data.sort((a, b) => {
                        if (a.nombre_area === 'TODOS_HERMANOS') return -1;
                        if (b.nombre_area === 'TODOS_HERMANOS') return 1;

                        if (a.nombre_area === 'DIPUTACION_MAYOR_GOBIERNO') return 1;
                        if (b.nombre_area === 'DIPUTACION_MAYOR_GOBIERNO') return -1;

                        return a.nombre_area.localeCompare(b.nombre_area);
                    });
                    setAreasDisponibles(sortedAreas);
                }

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al conectar con el servidor.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [navigate]);

    useEffect(() => {
        if (successMsg || error) {
            const timer = setTimeout(() => {
                setSuccessMsg("");
                setError("");
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg, error]);

    useEffect(() => {
        return () => {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
        };
    }, [previewUrl]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({ 
            ...prev, 
            [name]: type === 'checkbox' ? checked : value 
        }));
    };

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        
        if (file) {
            const objectUrl = URL.createObjectURL(file);
            const img = new Image();
            img.src = objectUrl;

            img.onload = () => {
                const width = img.naturalWidth;
                const height = img.naturalHeight;
                if (width > height) {
                    setFormData(prev => ({ ...prev, imagen_portada: file }));
                    setPreviewUrl(objectUrl);
                    setError("");
                } else {
                    setError("La imagen debe ser horizontal (formato paisaje).");
                    e.target.value = ""; 
                    URL.revokeObjectURL(objectUrl);
                }
            };
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
            const dataToSend = new FormData();
            dataToSend.append('titulo', formData.titulo);
            dataToSend.append('contenido', formData.contenido);
            dataToSend.append('tipo_comunicacion', formData.tipo_comunicacion);

            dataToSend.append('generar_podcast', formData.generar_podcast);
            
            if (formData.imagen_portada) {
                dataToSend.append('imagen_portada', formData.imagen_portada);
            }

            formData.areas_interes.forEach(id => {
                dataToSend.append('areas_interes', id);
            });

            await api.post('api/comunicados/', dataToSend, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            setSuccessMsg("Comunicado emitido correctamente.");

            setTimeout(() => {
                navigate("/noticias");
            }, 1500);

        } catch (err) {
            console.error(err);
            if (err.response) {
                if (err.response.status === 403) {
                    setError("No tienes permisos (Solo administradores o Junta de Gobierno).");
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

    const handleVincularTelegram = (e) => {
        e.preventDefault();

        if (currentUser && currentUser.enlace_vinculacion_telegram) {
            window.open(currentUser.enlace_vinculacion_telegram, '_blank');
        } else {
            console.error("El enlace de Telegram no está disponible.");
            alert("Hubo un problema al cargar tu enlace personal de Telegram.");
        }
    };

    if (loading) return <div className="loading-screen">Cargando panel...</div>;

    return (
        <div>

            <div className="toast-container-crear-comunicado">
                {successMsg && (
                    <div className="toast-message-crear-comunicado toast-success-crear-comunicado">
                        <CheckCircle size={24} />
                        <span>{successMsg}</span>
                    </div>
                )}
                {error && (
                    <div className="toast-message-crear-comunicado toast-error-crear-comunicado">
                        <AlertCircle size={24} />
                        <span>{error}</span>
                    </div>
                )}
            </div>

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
                            <h1 className="historical-header-title-crear-comunicado">CREAR COMUNICADO</h1>
                        </div>

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
                                                placeholder="Ej: Horario de reparto de papeletas"
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
                                                placeholder="Escriba aquí el cuerpo de la noticia..."
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
                                                />
                                                <ImageIcon size={32} style={{ margin: '0 auto 10px' }}/>
                                                <p>Haz clic para subir una imagen de portada</p>
                                                <small>JPG, PNG (Max. 5MB) - <strong>Formato horizontal obligatorio</strong></small>
                                            </div>
                                        ) : (
                                            <div className="image-preview-container-crear-comunicado">
                                                <img 
                                                    src={previewUrl} 
                                                    alt="Vista previa" 
                                                    className="image-preview-img-crear-comunicado"
                                                />
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

                                    <div className="form-group-crear-comunicado span-full-crear-comunicado">
                                        <label className="form-label-crear-comunicado">
                                            Formato podcast
                                        </label>
                                        <label className={`checkbox-container-crear-comunicado ${formData.generar_podcast ? 'checked' : ''}`}>
                                            <input
                                                type="checkbox"
                                                name="generar_podcast"
                                                checked={formData.generar_podcast}
                                                onChange={handleChange}
                                                className="styled-checkbox-crear-comunicado"
                                            />
                                            <div className="checkbox-text-crear-comunicado">
                                                <span className="checkbox-title-crear-comunicado" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <Headphones size={20} color={formData.generar_podcast ? "#ffffff" : "#800020"} />
                                                    Generar podcast a dos voces
                                                </span>
                                                <span className="checkbox-desc-crear-comunicado">
                                                    Crear automáticamente un audio inmersivo con el contenido de este comunicado.
                                                </span>
                                            </div>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Áreas o sectores a los que está dirigido el comunicado</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="form-container-crear-comunicado">

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

                            <div className="form-actions-crear-comunicado">
                                <button 
                                    type="button" 
                                    className="btn-cancel-crear-comunicado" 
                                    onClick={() => navigate("/home")}
                                >
                                    Cancelar
                                </button>
                                
                                <button 
                                    type="submit" 
                                    className="btn-save-crear-comunicado" 
                                    disabled={saving}
                                >
                                    <Save size={18} />
                                    {saving ? "Emitiendo..." : "Emitir Comunicado"}
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