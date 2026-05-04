import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from '../../api';
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../../constants";
import { ArrowLeft, FileText, MapPin, FolderDot, Save, AlertCircle, CheckCircle } from "lucide-react";


function AdminEdicionPuesto() {
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isOpen, setIsOpen] = useState(false);

    const { id } = useParams(); 
    const isEditing = Boolean(id);

    const [listaActos, setListaActos] = useState([]);
    const [listaTiposPuesto, setListaTiposPuesto] = useState([]);

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [successMsg, setSuccessMsg] = useState("");
        const [saving, setSaving] = useState(false);

    const [formData, setFormData] = useState({
        nombre: "",
        numero_maximo_asignaciones: 1,
        acto: "",
        tipo_puesto: "",
        lugar_citacion: "",
        hora_citacion: "",
        disponible: true,
        cortejo_cristo: true
    });

    const navigate = useNavigate();

    const formatearNombre = (texto) => {
        if (!texto) return "";
        return texto
            .replace(/_/g, " ")
            .toLowerCase()
            .replace(/\b\w/g, (char) => char.toUpperCase());
    };

    const toggleSidebar = () => setIsOpen(!isOpen);

    useEffect(() => {
        const token = localStorage.getItem(ACCESS_TOKEN || "access");

        if (!token) {
            setLoading(false);
            navigate("/login");
            return;
        }

        const fetchData = async () => {
            try {
                const userRes = await api.get("/api/me/");
                const userData = userRes.data;
                
                if (!userData.esAdmin) {
                    alert("No tienes permisos de administrador para gestionar puestos.");
                    navigate("/");
                    return;
                }
                setUser(userData);

                const [actosRes, tiposRes] = await Promise.all([
                    api.get("/api/actos/"),
                    api.get("/api/tipos-puesto/")
                ]);

                const actosData = Array.isArray(actosRes.data) ? actosRes.data : (actosRes.data.results || []);
                const tiposData = Array.isArray(tiposRes.data) ? tiposRes.data : (tiposRes.data.results || []);

                let actoAsignadoId = null;

                if (isEditing) {
                    const puestoRes = await api.get(`/api/puestos/${id}/`);
                    const puestoData = puestoRes.data;
                    
                    actoAsignadoId = (puestoData.acto && typeof puestoData.acto === 'object') 
                        ? puestoData.acto.id 
                        : (puestoData.acto || null);
                    
                    setFormData({
                        nombre: puestoData.nombre || "",
                        numero_maximo_asignaciones: puestoData.numero_maximo_asignaciones || 1,
                        acto: actoAsignadoId || "", 
                        tipo_puesto: (puestoData.tipo_puesto && typeof puestoData.tipo_puesto === 'object') 
                            ? puestoData.tipo_puesto.id 
                            : (puestoData.tipo_puesto || ""), 
                        lugar_citacion: puestoData.lugar_citacion || "",
                        hora_citacion: puestoData.hora_citacion ? puestoData.hora_citacion.substring(0, 5) : "",
                        disponible: puestoData.disponible ?? true,
                        cortejo_cristo: puestoData.cortejo_cristo ?? true
                    });
                }

                const hoy = new Date();
                hoy.setHours(0, 0, 0, 0);

                const actosFiltrados = actosData.filter(acto => {
                    if (!acto.requiere_papeleta) return false;

                    if (isEditing && acto.id === actoAsignadoId) return true;

                    if (!acto.inicio_solicitud) return false;

                    const fechaInicio = new Date(acto.inicio_solicitud);
                    fechaInicio.setHours(0, 0, 0, 0);

                    return fechaInicio >= hoy;
                });

                setListaActos(actosFiltrados);
                setListaTiposPuesto(tiposData);

            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response && err.response.status !== 401) {
                    setError("No se pudo cargar la información necesaria.");
                } else if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                    localStorage.removeItem(ACCESS_TOKEN || "access"); 
                    navigate("/login");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate, id, isEditing]);


    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        const url = isEditing 
            ? `/api/puestos/${id}/`
            : `/api/puestos/`;
        
        try {
            const payload = {
                ...formData,
                acto: formData.acto ? parseInt(formData.acto, 10) : null,
                tipo_puesto: formData.tipo_puesto,
                numero_maximo_asignaciones: parseInt(formData.numero_maximo_asignaciones, 10),
                hora_citacion: formData.hora_citacion ? formData.hora_citacion : null,
                lugar_citacion: formData.lugar_citacion ? formData.lugar_citacion : null
            };

            if (isEditing) {
                await api.put(url, payload);
            } else {
                await api.post(url, payload);
            }

            setSuccessMsg(isEditing ? "Puesto actualizado correctamente." : "Puesto creado correctamente.");
            
            setTimeout(() => {
                navigate("/new-home"); 
            }, 2000);

        } catch (err) {
            console.error(err);

            if (err.response && err.response.data) {
                const data = err.response.data;

                if (data.acto) {
                    const msg = Array.isArray(data.acto) ? data.acto[0] : data.acto;
                    setError(`⚠️ ${msg}`); 
                } 
                else if (data.nombre) {
                    const msg = Array.isArray(data.nombre) ? data.nombre[0] : data.nombre;
                    setError(`⚠️ ${msg}`);
                }
                else if (data.hora_citacion) {
                    const msg = Array.isArray(data.hora_citacion) ? data.hora_citacion[0] : data.hora_citacion;
                    setError(`⚠️ ${msg}`);
                }
                else if (data.detail) {
                    setError(data.detail);
                }
                else if (data.non_field_errors) {
                    setError(data.non_field_errors[0]);
                }
                else {
                    const firstKey = Object.keys(data)[0];
                    const firstMsg = data[firstKey];
                    const msgTexto = Array.isArray(firstMsg) ? firstMsg[0] : firstMsg;
                    setError(`Error en ${firstKey}: ${msgTexto}`);
                }
            } else {
                setError("Error de conexión con el servidor. Inténtelo más tarde.");
            }
        } finally {
            setSaving(false);
        }
    };

    const handleVincularTelegram = (e) => {
        e.preventDefault();

        if (user && user.enlace_vinculacion_telegram) {
            window.open(user.enlace_vinculacion_telegram, '_blank');
        } else {
            console.error("El enlace de Telegram no está disponible.");
            alert("Hubo un problema al cargar tu enlace personal de Telegram.");
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem(ACCESS_TOKEN || "access");
        localStorage.removeItem(REFRESH_TOKEN || "refresh");
        setUser(null);
        window.location.href = "/";
    };

    if (loading) return <div className="site-wrapper">Cargando...</div>;
    if (!user) return null;

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
                            onClick={!user?.telegram_chat_id ? handleVincularTelegram : (e) => e.preventDefault()}
                            style={{ 
                                cursor: user?.telegram_chat_id ? 'default' : 'pointer',
                                opacity: user?.telegram_chat_id ? 0.6 : 1
                            }}
                        >
                            <i className="bx bxl-telegram"></i>
                            <span className="link_name-dashboard">
                                {user?.telegram_chat_id ? "Telegram Vinculado ✅" : "Vincular Telegram"}
                            </span>
                        </a>
                        <span className="tooltip-dashboard">
                            {user?.telegram_chat_id ? "Ya vinculado" : "Vincular Telegram"}
                        </span>
                    </li>
                    {user?.esAdmin && (
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
                                <div className="name-dashboard">{user ? `${user.nombre} ${user.primer_apellido}` : "Usuario"}</div>
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
                    <div className="dashboard-panel-crear-puesto">
                        <div className="historical-header-container-crear-puesto">
                            <h1 className="historical-header-title-crear-puesto">EDITAR PUESTO</h1>
                        </div>

                        {error && (
                            <div className="alert-banner-creacion-puesto error-creacion-puesto" style={{marginBottom: '20px'}}>
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-creacion-puesto success-creacion-puesto" style={{marginBottom: '20px'}}>
                                <CheckCircle size={20} />
                                <span>{successMsg}</span>
                            </div>
                        )}

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Datos generales del puesto</span>
                            <div className="plazos-line"></div>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-container-crear-puesto">
                                <div className="form-grid-4-crear-puesto">
                                    <div className="form-group-crear-puesto span-3-crear-puesto">
                                        <label htmlFor="nombre" className="form-label-crear-puesto">
                                            Nombre del puesto *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input 
                                                type="text" 
                                                id="nombre"
                                                name="nombre" 
                                                value={formData.nombre} 
                                                onChange={handleChange} 
                                                placeholder="Ej: Vara Senatus, Guión Sacramental..."
                                                required 
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto">
                                        <label htmlFor="numero_maximo_asignaciones" className="form-label-crear-puesto">
                                            Cantidad *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input 
                                                type="number" 
                                                id="numero_maximo_asignaciones"
                                                name="numero_maximo_asignaciones" 
                                                value={formData.numero_maximo_asignaciones} 
                                                onChange={handleChange}
                                                placeholder="Ej: 1"
                                                min="1"
                                                required
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label className={`checkbox-container-crear-puesto ${formData.disponible ? 'checked' : ''}`}>
                                            <input 
                                                type="checkbox" 
                                                name="disponible" 
                                                checked={formData.disponible} 
                                                onChange={handleChange}
                                                className="styled-checkbox-crear-puesto"
                                            />
                                            <div className="checkbox-text-crear-puesto">
                                                <span className="checkbox-title-crear-puesto">Disponible para asignación</span>
                                                <span className="checkbox-desc-crear-puesto">Marcar como disponible para asignación inmediata.</span>
                                            </div>
                                        </label>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label className={`checkbox-container-crear-puesto ${formData.cortejo_cristo ? 'checked' : ''}`}>
                                            <input 
                                                type="checkbox" 
                                                name="cortejo_cristo" 
                                                checked={formData.cortejo_cristo} 
                                                onChange={handleChange}
                                                className="styled-checkbox-crear-puesto"
                                            />
                                            <div className="checkbox-text-crear-puesto">
                                                <span className="checkbox-title-crear-puesto">Sección del cortejo</span>
                                                <span className="checkbox-desc-crear-puesto">Marcar si pertenece al cortejo de Cristo. Dejar en blanco si pertenece al de la Virgen.</span>
                                            </div>
                                        </label>
                                    </div>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Selección del acto asociado y del tipo de puesto</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="form-grid-4-crear-puesto">
                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="acto" className="form-label-crear-puesto">
                                            Acto asociado *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <select
                                                id="acto"
                                                name="acto"
                                                value={formData.acto}
                                                onChange={handleChange}
                                                required
                                                className="form-control-crear-puesto"
                                            >
                                                <option value="" disabled>Seleccione un acto</option>
                                                {listaActos.map(acto => (
                                                    <option key={acto.id} value={acto.id}>
                                                        {acto.nombre} ({new Date(acto.fecha).toLocaleDateString()})
                                                    </option>
                                                ))}
                                                {listaActos.length === 0 && (
                                                    <option disabled>No hay actos que requieran papeleta.</option>
                                                )}
                                            </select>
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="tipo_puesto" className="form-label-crear-puesto">
                                            Tipo de puesto *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <select
                                                id="tipo_puesto"
                                                name="tipo_puesto"
                                                value={formData.tipo_puesto}
                                                onChange={handleChange}
                                                required
                                                className="form-control-crear-puesto"
                                            >
                                                <option value="" disabled>Seleccione Categoría</option>
                                                {listaTiposPuesto.map(tipo => (
                                                    <option key={tipo.id} value={tipo.nombre_tipo}>
                                                        {formatearNombre(tipo.nombre_tipo)} {tipo.solo_junta_gobierno ? '(Solo Junta)' : ''}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <MapPin size={18} /> Datos de citación
                                        </span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="form-grid-4-crear-puesto">
                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="lugar_citacion" className="form-label-crear-puesto">
                                            Lugar de citación *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input
                                                type="text"
                                                id="lugar_citacion"
                                                name="lugar_citacion"
                                                value={formData.lugar_citacion}
                                                onChange={handleChange}
                                                placeholder="Ej: Parroquia de San Gonzalo"
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="hora_citacion" className="form-label-crear-puesto">
                                            Hora de citación *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input
                                                type="time"
                                                id="hora_citacion"
                                                name="hora_citacion"
                                                value={formData.hora_citacion}
                                                onChange={handleChange}
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="form-actions-crear-puesto">
                                    <button 
                                        type="button" 
                                        className="btn-cancel-crear-puesto" 
                                        onClick={() => navigate("/home")}
                                    >
                                        Cancelar
                                    </button>
                                    
                                    <button 
                                        type="submit" 
                                        className="btn-save-crear-puesto" 
                                        disabled={saving}
                                    >
                                        <Save size={18} />
                                        {saving ? "Guardando..." : "Guardar cambios"}
                                    </button>
                                </div>
                                
                            </div>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    )
}

export default AdminEdicionPuesto;