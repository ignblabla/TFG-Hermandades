import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminEdicionHermano/AdminEdicionHermano.css';
import { Save, User, MapPin, Calendar, ShieldAlert, CheckCircle, AlertCircle, AlertTriangle } from "lucide-react";

function AdminEditarHermano() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    const [accesoDenegado, setAccesoDenegado] = useState(false);

    const [showConfirmBaja, setShowConfirmBaja] = useState(false);
    const [givingBaja, setGivingBaja] = useState(false);

    const [currentUser, setCurrentUser] = useState(null);
    const [formData, setFormData] = useState({
        dni: '', nombre: '', primer_apellido: '', segundo_apellido: '',
        email: '', telefono: '', password: '',
        fecha_nacimiento: '', genero: 'MASCULINO', estado_civil: 'SOLTERO',
        direccion: '', codigo_postal: '', localidad: '', provincia: '', comunidad_autonoma: '',
        lugar_bautismo: '', fecha_bautismo: '', parroquia_bautismo: '',
        numero_registro: '', estado_hermano: 'PENDIENTE_INGRESO', 
        fecha_ingreso_corporacion: '', fecha_baja_corporacion: '',
        esAdmin: false
    });

    useEffect(() => {
        let isMounted = true;
        const fetchAllData = async () => {
            try {
                let user = currentUser;
                if (!user) {
                    const resUser = await api.get("api/me/");
                    user = resUser.data;
                    if (isMounted) setCurrentUser(user);
                }

                if (!user.esAdmin) {
                    if (isMounted) {
                        setAccesoDenegado(true);
                        setLoading(false);
                    }
                    return;
                }

                const resHermano = await api.get(`api/hermanos/${id}/gestion/`);
                
                if (isMounted) {
                    const data = resHermano.data;
                    setFormData({
                        ...data,
                        password: '',
                        segundo_apellido: data.segundo_apellido || '',
                        email: data.email || '',
                        direccion: data.direccion || '',
                        codigo_postal: data.codigo_postal || '',
                        localidad: data.localidad || '',
                        provincia: data.provincia || '',
                        comunidad_autonoma: data.comunidad_autonoma || '',
                        lugar_bautismo: data.lugar_bautismo || '',
                        parroquia_bautismo: data.parroquia_bautismo || '',
                        fecha_baja_corporacion: data.fecha_baja_corporacion || '',
                        numero_registro: data.numero_registro || ''
                    });
                }

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar los datos del hermano.");
                if (err.response?.status === 404) navigate("/hermanos/listado");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchAllData();
        return () => { isMounted = false; };
    }, [id, navigate]);

    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => {
                setSuccessMsg("");
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleDarDeBaja = async () => {
        setGivingBaja(true);
        try {
            await api.post(`api/hermanos/${id}/dar-de-baja/`);
            setShowConfirmBaja(false);
            setSuccessMsg(`El hermano ha sido dado de baja correctamente.`);
            setTimeout(() => {
                navigate("/censo-hermanos");
            }, 3000);
        } catch (err) {
            setShowConfirmBaja(false);
            if (err.response?.status === 403) {
                setError(err.response.data?.detail || "No tienes permisos para realizar esta acción.");
            } else {
                setError("Error al dar de baja al hermano.");
            }
        } finally {
            setGivingBaja(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        const payload = { ...formData };

        if (!payload.password || payload.password.trim() === "") {
            delete payload.password;
        }

        const dateFields = [
            'fecha_nacimiento', 
            'fecha_bautismo', 
            'fecha_ingreso_corporacion', 
            'fecha_baja_corporacion'
        ];

        dateFields.forEach(field => {
            if (payload[field] === "") {
                payload[field] = null;
            }
        });

        try {
            await api.put(`api/hermanos/${id}/gestion/`, payload);
            setSuccessMsg("Datos actualizados correctamente.");
            setFormData(prev => ({ ...prev, password: '' }));
            setTimeout(() => {
                navigate("/censo-hermanos");
            }, 3000);

        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                const errorData = err.response.data;
                const errorMessages = Object.entries(errorData)
                    .map(([key, msg]) => `${key.toUpperCase()}: ${msg}`)
                    .join(" | ");
                setError(errorMessages);
            } else {
                setError("Error al guardar los cambios.");
            }
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

    if (accesoDenegado) {
        return (
            <div className="site-wrapper" style={{textAlign: 'center', marginTop: '50px'}}>
                <h2 style={{color: 'red'}}>🚫 Acceso Restringido</h2>
                <p>Esta sección es exclusiva para Administradores.</p>
                <button onClick={() => navigate("/new-home")} className="btn-purple">Volver al inicio</button>
            </div>
        );
    }

    if (loading) return <div className="loading-screen">Cargando ficha...</div>;

    const estaEnBaja = formData.estado_hermano === 'BAJA' || Boolean(formData.fecha_baja_corporacion);

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

            {showConfirmBaja && (
                <div className="modal-overlay-confirmacion">
                    <div className="modal-content-confirmacion">
                        <div className="modal-header-confirmacion">
                            <AlertTriangle className="modal-icon-warning" size={28} />
                            <h3>Confirmar baja</h3>
                        </div>
                        <div className="modal-body-confirmacion">
                            <p>
                                ¿Estás seguro de dar de baja a <strong>"{formData.nombre} {formData.primer_apellido}"</strong>?
                                <br /><br />
                                Esta acción cambiará su estado a <strong>BAJA</strong>, registrará la fecha de hoy y <strong>desactivará su acceso al sistema</strong>.
                            </p>
                            <div className="modal-actions-confirmacion">
                                <button
                                    className="btn-cancelar-modal"
                                    onClick={() => setShowConfirmBaja(false)}
                                    disabled={givingBaja}
                                >
                                    Cancelar
                                </button>
                                <button
                                    className="btn-confirmar-modal"
                                    onClick={handleDarDeBaja}
                                    disabled={givingBaja}
                                >
                                    {givingBaja ? "Procesando..." : "Confirmar y dar de baja"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
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
                    <div className="dashboard-panel-editar-perfil">
                        <div className="historical-header-container-editar-perfil">
                            <h1 className="historical-header-title-editar-perfil">
                                EDITAR DATOS DEL HERMANO - Nº REGISTRO: {formData.numero_registro || 'N/A'}
                            </h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Datos del Hermano</span>
                            <div className="plazos-line"></div>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-container-editar-perfil">
                                <div className="form-row-editar-perfil">
                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="nombre" className="form-label-editar-perfil">
                                            Nombre
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="text" 
                                                id="nombre"
                                                name="nombre" 
                                                value={formData.nombre}
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="primer_apellido" className="form-label-editar-perfil">
                                            Primer apellido
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="text" 
                                                id="primer_apellido"
                                                name="primer_apellido" 
                                                value={formData.primer_apellido} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="segundo_apellido" className="form-label-editar-perfil">
                                            Segundo apellido
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="text" 
                                                id="segundo_apellido"
                                                name="segundo_apellido" 
                                                value={formData.segundo_apellido} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="dni" className="form-label-editar-perfil">
                                            DNI
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="text" 
                                                id="dni"
                                                name="dni" 
                                                value={formData.dni} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="form-row-editar-perfil">
                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="fecha_nacimiento" className="form-label-editar-perfil">
                                            Fecha de nacimiento
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="date" 
                                                id="fecha_nacimiento"
                                                name="fecha_nacimiento" 
                                                value={formData.fecha_nacimiento || ''} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="genero" className="form-label-editar-perfil">
                                            Género
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <select 
                                                id="genero"
                                                name="genero" 
                                                value={formData.genero} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            >
                                                <option value="MASCULINO">Masculino</option>
                                                <option value="FEMENINO">Femenino</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="estado_civil" className="form-label-editar-perfil">
                                            Estado Civil
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <select 
                                                id="estado_civil"
                                                name="estado_civil" 
                                                value={formData.estado_civil} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            >
                                                <option value="SOLTERO">Soltero/a</option>
                                                <option value="CASADO">Casado/a</option>
                                                <option value="SEPARADO">Separado/a</option>
                                                <option value="VIUDO">Viudo/a</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="password" className="form-label-editar-perfil">
                                            Nueva Contraseña
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="password" 
                                                id="password"
                                                name="password" 
                                                value={formData.password} 
                                                onChange={handleChange} 
                                                placeholder="Opcional" 
                                                autoComplete="new-password"
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Datos de contacto</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="form-grid-editar-perfil">
                                <div className="form-group-solicitud-editar-perfil span-3-editar-perfil">
                                    <label htmlFor="direccion" className="form-label-editar-perfil">Dirección Postal</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="direccion" name="direccion" value={formData.direccion} onChange={handleChange} className="form-control-editar-perfil" disabled={estaEnBaja} />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-3-editar-perfil">
                                    <label htmlFor="localidad" className="form-label-editar-perfil">Localidad</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="localidad" name="localidad" value={formData.localidad} onChange={handleChange} className="form-control-editar-perfil" disabled={estaEnBaja} />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                    <label htmlFor="codigo_postal" className="form-label-editar-perfil">C. Postal</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="codigo_postal" name="codigo_postal" value={formData.codigo_postal} onChange={handleChange} className="form-control-editar-perfil" disabled={estaEnBaja} />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                    <label htmlFor="provincia" className="form-label-editar-perfil">Provincia</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="provincia" name="provincia" value={formData.provincia} onChange={handleChange} className="form-control-editar-perfil" disabled={estaEnBaja} />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                    <label htmlFor="comunidad_autonoma" className="form-label-editar-perfil">Comunidad Autónoma</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="comunidad_autonoma" name="comunidad_autonoma" value={formData.comunidad_autonoma} onChange={handleChange} className="form-control-editar-perfil" disabled={estaEnBaja} />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil span-3-editar-perfil">
                                    <label htmlFor="telefono" className="form-label-editar-perfil">Teléfono</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="telefono" name="telefono" value={formData.telefono} onChange={handleChange} required className="form-control-editar-perfil" disabled={estaEnBaja} />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-3-editar-perfil">
                                    <label htmlFor="email" className="form-label-editar-perfil">Email</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required className="form-control-editar-perfil" disabled={estaEnBaja} />
                                    </div>
                                </div>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Datos eclesiásticos</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="form-row-editar-perfil">
                                <div className="form-group-solicitud-editar-perfil">
                                    <label htmlFor="fecha_bautismo" className="form-label-editar-perfil">Fecha Bautismo</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input 
                                            type="date" 
                                            id="fecha_bautismo"
                                            name="fecha_bautismo" 
                                            value={formData.fecha_bautismo || ''} 
                                            onChange={handleChange}
                                            className="form-control-editar-perfil"
                                            disabled={estaEnBaja}
                                        />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil">
                                    <label htmlFor="lugar_bautismo" className="form-label-editar-perfil">Lugar Bautismo</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input 
                                            type="text" 
                                            id="lugar_bautismo"
                                            name="lugar_bautismo" 
                                            value={formData.lugar_bautismo || ''} 
                                            onChange={handleChange}
                                            className="form-control-editar-perfil"
                                            disabled={estaEnBaja}
                                        />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil">
                                    <label htmlFor="parroquia_bautismo" className="form-label-editar-perfil">Parroquia</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input 
                                            type="text" 
                                            id="parroquia_bautismo"
                                            name="parroquia_bautismo" 
                                            value={formData.parroquia_bautismo || ''} 
                                            onChange={handleChange}
                                            className="form-control-editar-perfil"
                                            disabled={estaEnBaja}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Gestión interna (Secretaría)</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="admin-highlight-editar-perfil">
                                <div className="form-grid-4-editar-perfil">
                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="numero_registro" className="form-label-editar-perfil">Nº Registro Hermandad</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="number" 
                                                id="numero_registro"
                                                name="numero_registro" 
                                                value={formData.numero_registro || ''} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="estado_hermano" className="form-label-editar-perfil">Estado</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="text" 
                                                id="estado_hermano"
                                                name="estado_hermano" 
                                                value={formData.estado_hermano || ''} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="fecha_ingreso_corporacion" className="form-label-editar-perfil">Fecha Ingreso</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="date" 
                                                id="fecha_ingreso_corporacion"
                                                name="fecha_ingreso_corporacion" 
                                                value={formData.fecha_ingreso_corporacion || ''} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="fecha_baja_corporacion" className="form-label-editar-perfil">Fecha Baja</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="date" 
                                                id="fecha_baja_corporacion"
                                                name="fecha_baja_corporacion" 
                                                value={formData.fecha_baja_corporacion || ''} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
                                                disabled={estaEnBaja}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div 
                                className="form-actions-editar-perfil" 
                                style={{ justifyContent: !estaEnBaja ? 'space-between' : 'flex-end' }}
                            >
                                {!estaEnBaja && (
                                    <button 
                                        type="button" 
                                        className="btn-danger-editar-perfil" 
                                        onClick={() => setShowConfirmBaja(true)}
                                    >
                                        <ShieldAlert size={18} />
                                        Dar de baja
                                    </button>
                                )}

                                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                    <button 
                                        type="button" 
                                        className="btn-cancel-editar-perfil" 
                                        onClick={() => navigate("/censo-hermanos")}
                                    >
                                        {estaEnBaja ? "Volver" : "Cancelar"}
                                    </button>
                                    
                                    {!estaEnBaja && (
                                        <button 
                                            type="submit" 
                                            className="btn-save-editar-perfil" 
                                            disabled={saving}
                                        >
                                            <Save size={18} />
                                            {saving ? "Guardando..." : "Guardar cambios"}
                                        </button>
                                    )}
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminEditarHermano;