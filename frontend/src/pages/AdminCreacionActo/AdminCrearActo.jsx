import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../AdminCreacionActo/AdminCrearActo.css';
import { Save, FileText, Settings, ShieldAlert, CheckCircle, Clock, AlertCircle, Lock, ImageIcon, X } from "lucide-react";
import ResumenActoCard from '../../components/ResumenActoCard';

function AdminCrearActo() {
    const navigate = useNavigate();

    const currentYear = new Date().getFullYear();
    const minDate = `${currentYear}-01-01T00:00`;
    const maxDate = `${currentYear}-12-31T23:59`;
    
    const [isOpen, setIsOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [successMsg, setSuccessMsg] = useState("");
    
    const [currentUser, setCurrentUser] = useState(null);
    const [tiposActo, setTiposActo] = useState([]);
    const [requierePapeleta, setRequierePapeleta] = useState(false);

    const [previewUrl, setPreviewUrl] = useState(null);

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
        fin_solicitud_cirios: '',
        imagen_portada: null
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

    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    useEffect(() => {
        return () => {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
        };
    }, [previewUrl]);

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
            const dataToSend = new FormData();

            Object.keys(payload).forEach(key => {
                if (key !== 'imagen_portada' && payload[key] !== null && payload[key] !== '') {
                    dataToSend.append(key, payload[key]);
                }
            });

            if (formData.imagen_portada) {
                dataToSend.append('imagen_portada', formData.imagen_portada);
            }

            await api.post('api/actos/crear/', dataToSend, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            setSuccessMsg("Acto creado correctamente.");
            
            setTimeout(() => {
                navigate("/listado-actos");
            }, 3000);

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

    const handleVincularTelegram = (e) => {
        e.preventDefault();

        if (currentUser && currentUser.enlace_vinculacion_telegram) {
            window.open(currentUser.enlace_vinculacion_telegram, '_blank');
        } else {
            console.error("El enlace de Telegram no está disponible.");
            alert("Hubo un problema al cargar tu enlace personal de Telegram.");
        }
    };

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
                    <div className="dashboard-panel-crear-acto">
                        <div className="historical-header-container-crear-acto">
                            <h1 className="historical-header-title-crear-acto">CREAR ACTO</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Información general del acto</span>
                            <div className="plazos-line"></div>
                        </div>

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

                        <form onSubmit={handleSubmit}>

                            <div className="form-container-crear-acto">
                                <div className="form-group-solicitud-crear-acto">
                                    <label htmlFor="nombre" className="form-label-crear-acto">
                                        Nombre del acto <span className="required">*</span>
                                    </label>
                                    <div className="input-wrapper-crear-acto">
                                        <input 
                                            type="text"
                                            id="nombre"
                                            name="nombre"
                                            value={formData.nombre}
                                            onChange={handleChange}
                                            placeholder={`Ej: Estación de Penitencia ${currentYear}`}
                                            className="form-control-crear-acto"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-crear-acto">
                                    <label htmlFor="lugar" className="form-label-crear-acto">
                                        Lugar de celebración <span className="required">*</span>
                                    </label>
                                    <div className="input-wrapper-crear-acto">
                                        <input 
                                            type="text"
                                            id="lugar"
                                            name="lugar"
                                            value={formData.lugar} 
                                            onChange={handleChange}
                                            placeholder="Ej: Parroquia de San Sebastián"
                                            className="form-control-crear-acto"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-row-crear-acto">
                                    <div className="form-group-solicitud-crear-acto">
                                        <label htmlFor="tipo_acto" className="form-label-crear-acto">
                                            Tipo de acto <span className="required">*</span>
                                        </label>
                                        <div className="input-wrapper-crear-acto">
                                            <select
                                                id="tipo_acto"
                                                name="tipo_acto"
                                                value={formData.tipo_acto}
                                                onChange={handleChange}
                                                className="form-control-crear-acto"
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
                                    </div>

                                    <div className="form-group-solicitud-crear-acto">
                                        <label htmlFor="fecha" className="form-label-crear-acto">
                                            Fecha y hora <span className="required">*</span>
                                        </label>
                                        <div className="input-wrapper-crear-acto">
                                            <input 
                                                type="datetime-local"
                                                id="fecha"
                                                name="fecha"
                                                value={formData.fecha} 
                                                onChange={handleChange}
                                                className="form-control-crear-acto"
                                                required
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="form-group-solicitud-crear-acto">
                                    <label htmlFor="descripcion" className="form-label-crear-acto">
                                        Descripción
                                    </label>
                                    <div className="input-wrapper-crear-acto">
                                        <textarea
                                            id="descripcion"
                                            name="descripcion"
                                            value={formData.descripcion}
                                            onChange={handleChange}
                                            placeholder="Añade detalles adicionales sobre el acto..."
                                            className="form-control-crear-acto textarea-crear-acto"
                                            rows="4"
                                        />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-crear-acto">
                                    <label className="form-label-crear-acto">
                                        Imagen de portada
                                    </label>
                                    
                                    {!previewUrl ? (
                                        <div 
                                            className="image-upload-area-crear-acto"
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
                                            <small>JPG, PNG (Max. 5MB) - <strong>Formato Horizontal obligatorio</strong></small>
                                        </div>
                                    ) : (
                                        <div className="image-preview-container-crear-acto">
                                            <img 
                                                src={previewUrl} 
                                                alt="Vista previa" 
                                                className="image-preview-img-crear-acto"
                                            />
                                            <button
                                                type="button"
                                                onClick={removeImage}
                                                className="btn-delete-image-crear-acto"
                                                title="Eliminar imagen"
                                            >
                                                <X size={18} color="#ef4444" />
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Configuración de reparto de papeletas de sitio</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="form-container-crear-acto-espacio">
                                    <div className="form-group-solicitud-crear-acto">
                                        <label htmlFor="modalidad" className="form-label-crear-acto">
                                            Modalidad de reparto {requierePapeleta && <span className="required">*</span>}
                                        </label>
                                        <div className="input-wrapper-crear-acto">
                                            <select 
                                                id="modalidad"
                                                name="modalidad" 
                                                value={formData.modalidad} 
                                                onChange={handleChange}
                                                className="form-control-crear-acto"
                                                disabled={!requierePapeleta}
                                                required={requierePapeleta}
                                            >
                                                <option value="" disabled>Seleccione una opción</option>
                                                <option value="TRADICIONAL">Tradicional (Fases separadas)</option>
                                                <option value="UNIFICADO">Unificado (Insignias y cirios a la vez)</option>
                                            </select>
                                        </div>
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
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Plazos de solicitud online</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="form-container-crear-acto-espacio">
                                    <div className="form-row-crear-acto">
                                        <div className="form-group-solicitud-crear-acto">
                                            <label htmlFor="inicio_solicitud" className="form-label-crear-acto">
                                                {formData.modalidad === 'UNIFICADO' 
                                                    ? 'Inicio solicitud insignias y cirios' 
                                                    : (formData.modalidad === 'TRADICIONAL' && requierePapeleta) 
                                                        ? 'Inicio solicitud insignias' 
                                                        : 'Inicio solicitud insignias'}
                                            </label>
                                            <div className="input-wrapper-crear-acto">
                                                <input 
                                                    type="datetime-local" 
                                                    id="inicio_solicitud"
                                                    name="inicio_solicitud" 
                                                    value={formData.inicio_solicitud || ''} 
                                                    onChange={handleChange} 
                                                    min={minDate} max={maxDate}
                                                    className={`form-control-crear-acto ${!requierePapeleta ? 'has-icon' : ''}`}
                                                    disabled={!requierePapeleta}
                                                />
                                                {!requierePapeleta && <Lock className="input-lock-icon" size={16} />}
                                            </div>
                                        </div>
                                        
                                        <div className="form-group-solicitud-crear-acto">
                                            <label htmlFor="fin_solicitud" className="form-label-crear-acto">
                                                {formData.modalidad === 'UNIFICADO' 
                                                    ? 'Fin solicitud insignias y cirios' 
                                                    : (formData.modalidad === 'TRADICIONAL' && requierePapeleta) 
                                                        ? 'Fin solicitud insignias' 
                                                        : 'Fin solicitud insignias'}
                                            </label>
                                            <div className="input-wrapper-crear-acto">
                                                <input 
                                                    type="datetime-local" 
                                                    id="fin_solicitud"
                                                    name="fin_solicitud" 
                                                    value={formData.fin_solicitud || ''} 
                                                    onChange={handleChange}
                                                    min={minDate} max={maxDate}
                                                    className={`form-control-crear-acto ${!requierePapeleta ? 'has-icon' : ''}`}
                                                    disabled={!requierePapeleta}
                                                />
                                                {!requierePapeleta && <Lock className="input-lock-icon" size={16} />}
                                            </div>
                                        </div>
                                    </div>

                                    {formData.modalidad !== 'UNIFICADO' && (
                                        <div className="form-row-crear-acto">
                                            <div className="form-group-solicitud-crear-acto">
                                                <label htmlFor="inicio_solicitud_cirios" className="form-label-crear-acto">
                                                    {formData.modalidad === 'TRADICIONAL' ? 'Inicio solicitud cirios' : 'Inicio solicitud cirios'}
                                                </label>
                                                <div className="input-wrapper-crear-acto">
                                                    <input 
                                                        type="datetime-local" 
                                                        id="inicio_solicitud_cirios"
                                                        name="inicio_solicitud_cirios" 
                                                        value={formData.inicio_solicitud_cirios || ''} 
                                                        onChange={handleChange} 
                                                        min={minDate} max={maxDate}
                                                        className={`form-control-crear-acto ${(!requierePapeleta || formData.modalidad === 'UNIFICADO') ? 'has-icon' : ''}`}
                                                        disabled={!requierePapeleta || formData.modalidad === 'UNIFICADO'}
                                                    />
                                                    {(!requierePapeleta || formData.modalidad === 'UNIFICADO') && <Lock className="input-lock-icon" size={16} />}
                                                </div>
                                            </div>
                                            
                                            <div className="form-group-solicitud-crear-acto">
                                                <label htmlFor="fin_solicitud_cirios" className="form-label-crear-acto">
                                                    {formData.modalidad === 'TRADICIONAL' ? 'Fin solicitud cirios' : 'Fin solicitud cirios'}
                                                </label>
                                                <div className="input-wrapper-crear-acto">
                                                    <input 
                                                        type="datetime-local" 
                                                        id="fin_solicitud_cirios"
                                                        name="fin_solicitud_cirios" 
                                                        value={formData.fin_solicitud_cirios || ''} 
                                                        onChange={handleChange}
                                                        min={minDate} max={maxDate}
                                                        className={`form-control-crear-acto ${(!requierePapeleta || formData.modalidad === 'UNIFICADO') ? 'has-icon' : ''}`}
                                                        disabled={!requierePapeleta || formData.modalidad === 'UNIFICADO'}
                                                    />
                                                    {(!requierePapeleta || formData.modalidad === 'UNIFICADO') && <Lock className="input-lock-icon" size={16} />}
                                                </div>
                                            </div>
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

                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminCrearActo;