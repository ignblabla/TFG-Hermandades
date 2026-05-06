import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../HermanoEdicionDatos/HermanoEdicionDatos.css'
import { Save, User, MapPin, AlertCircle, CheckCircle, Calendar, ShieldAlert, ListTodo,
    Users, Heart, Hammer, Church, Sun, BookOpen, Crown, Landmark, CreditCard, Bell
} from "lucide-react";


function EditarMiPerfil() {
    const navigate = useNavigate();
    const [isOpen, setIsOpen] = useState(false);
    
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");
    const [currentUser, setCurrentUser] = useState(null);
    const [areasDB, setAreasDB] = useState([]);
    
    const [readOnlyData, setReadOnlyData] = useState({});
    const [formData, setFormData] = useState({
        telefono: '', 
        estado_civil: 'SOLTERO',
        direccion: '', 
        codigo_postal: '', 
        localidad: '', 
        provincia: '', 
        comunidad_autonoma: '',
        email: '',
        password: '',
        areas_interes: [],
        datos_bancarios: {
            iban: '',
            es_titular: true,
            titular_cuenta: '',
            periodicidad: 'ANUAL'
        }
    });

    const areaInfoEstatica = {
        'TODOS_HERMANOS': { icon: <Bell size={20} />, title: 'Todos los Hermanos' },
        'COSTALEROS': { icon: <Users size={20} />, title: 'Costaleros' },
        'CARIDAD': { icon: <Heart size={20} />, title: 'Diputación de Caridad' },
        'JUVENTUD': { icon: <Sun size={20} />, title: 'Juventud' },
        'PRIOSTIA': { icon: <Hammer size={20} />, title: 'Priostía' },
        'CULTOS_FORMACION': { icon: <BookOpen size={20} />, title: 'Cultos y Formación' },
        'PATRIMONIO': { icon: <Landmark size={20} />, title: 'Patrimonio' },
        'ACOLITOS': { icon: <Church size={20} />, title: 'Acólitos' },
        'DIPUTACION_MAYOR_GOBIERNO': { icon: <Crown size={20} />, title: 'Dip. Mayor de Gobierno' },
    };

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    // --- EFECTO DE CARGA ---
    useEffect(() => {
        let isMounted = true;
        const fetchMyData = async () => {
            try {
                const [resMe, resAreas] = await Promise.all([
                    api.get("api/me/"),
                    api.get("/api/areas-interes/")
                ]);
                
                if (isMounted) {
                    const data = resMe.data;
                    const dataAreas = resAreas.data;

                    setCurrentUser(data);
                    setAreasDB(dataAreas);

                    setReadOnlyData({
                        nombre: data.nombre || '',
                        primer_apellido: data.primer_apellido || '',
                        segundo_apellido: data.segundo_apellido || '',
                        dni: data.dni || '',
                        fecha_nacimiento: data.fecha_nacimiento || '',
                        genero: data.genero || '',
                        fecha_bautismo: data.fecha_bautismo,
                        lugar_bautismo: data.lugar_bautismo,
                        parroquia_bautismo: data.parroquia_bautismo,
                        numero_registro: data.numero_registro || 'Pendiente',
                        estado_hermano: data.estado_hermano || '',
                        fecha_ingreso: data.fecha_ingreso_corporacion,
                        fecha_baja: data.fecha_baja_corporacion
                    });

                    const areasUsuario = data.areas_interes || [];
                    if (!areasUsuario.includes('TODOS_HERMANOS')) {
                        areasUsuario.push('TODOS_HERMANOS');
                    }

                    // Campos permitidos
                    setFormData({
                        password: data.password || '',
                        telefono: data.telefono || '',
                        estado_civil: data.estado_civil || 'SOLTERO',
                        direccion: data.direccion || '',
                        codigo_postal: data.codigo_postal || '',
                        localidad: data.localidad || '',
                        provincia: data.provincia || '',
                        comunidad_autonoma: data.comunidad_autonoma || '',
                        email: data.email,
                        areas_interes: data.areas_interes || [],
                        datos_bancarios: data.datos_bancarios || {
                            iban: '',
                            es_titular: true,
                            titular_cuenta: '',
                            periodicidad: 'ANUAL'
                        }
                    });
                }
            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar tu perfil. Comprueba tu conexión.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchMyData();
        return () => { isMounted = false; };
    }, []);

    // --- TEMPORIZADOR PARA MENSAJE DE ÉXITO ---
    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    // --- HANDLERS ---
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleBankChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            datos_bancarios: {
                ...prev.datos_bancarios,
                [name]: type === 'checkbox' ? checked : value
            }
        }));
    };

    const handleAreaToggle = (areaNombre) => {
        if (areaNombre === 'TODOS_HERMANOS') return;

        setFormData(prev => {
            const currentAreas = prev.areas_interes;
            if (currentAreas.includes(areaNombre)) {
                return { ...prev, areas_interes: currentAreas.filter(a => a !== areaNombre) };
            } else {
                return { ...prev, areas_interes: [...currentAreas, areaNombre] };
            }
        });
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

        if (payload.datos_bancarios.es_titular) {
            payload.datos_bancarios.titular_cuenta = '';
        }

        if (!payload.areas_interes.includes('TODOS_HERMANOS')) {
            payload.areas_interes.push('TODOS_HERMANOS');
        }

        try {
            await api.patch("api/me/", payload);
            setSuccessMsg("Sus datos han sido actualizados con éxito");
            setFormData(prev => ({ ...prev, password: '' }));
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                const errorData = err.response.data;
                const errorMessages = Object.entries(errorData)
                    .map(([key, msg]) => {
                        if (typeof msg === 'object' && msg !== null) {
                            return Object.entries(msg).map(([subKey, subMsg]) => `${subKey.toUpperCase()}: ${subMsg}`).join(" | ");
                        }
                        return `${key.toUpperCase()}: ${msg}`;
                    })
                    .join(" | ");
                setError(errorMessages);
            } else {
                setError("Error al guardar los cambios. Inténtalo de nuevo más tarde.");
            }
        } finally {
            setSaving(false);
        }
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

    if (loading) return <div className="loading-screen">Cargando tu perfil...</div>;

    const sortedAreasDB = [...areasDB].sort((a, b) => {
        if (a.nombre_area === 'TODOS_HERMANOS') return -1;
        if (b.nombre_area === 'TODOS_HERMANOS') return 1;
        return a.nombre_area.localeCompare(b.nombre_area); 
    });

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
                    <div className="dashboard-panel-editar-perfil">
                        <div className="historical-header-container-editar-perfil">
                            <h1 className="historical-header-title-editar-perfil">EDITAR DATOS PERSONALES</h1>
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
                                                value={readOnlyData.nombre} 
                                                disabled 
                                                className="form-control-editar-perfil"
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
                                                value={readOnlyData.primer_apellido} 
                                                disabled 
                                                className="form-control-editar-perfil"
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
                                                value={readOnlyData.segundo_apellido} 
                                                disabled 
                                                className="form-control-editar-perfil"
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
                                                value={readOnlyData.dni} 
                                                disabled 
                                                className="form-control-editar-perfil"
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
                                                value={readOnlyData.fecha_nacimiento || ''} 
                                                disabled 
                                                className="form-control-editar-perfil"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="genero" className="form-label-editar-perfil">
                                            Género
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="text" 
                                                id="genero"
                                                name="genero" 
                                                value={readOnlyData.genero} 
                                                disabled 
                                                className="form-control-editar-perfil"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="estado_civil" className="form-label-editar-perfil">
                                            Estado civil
                                        </label>
                                        <div className="input-wrapper-editar-perfil">
                                            <select 
                                                id="estado_civil"
                                                name="estado_civil" 
                                                value={formData.estado_civil} 
                                                onChange={handleChange}
                                                className="form-control-editar-perfil"
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
                                            Nueva contraseña
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
                                    <label htmlFor="direccion" className="form-label-editar-perfil">Dirección postal</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="direccion" name="direccion" value={formData.direccion} onChange={handleChange} className="form-control-editar-perfil" />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-3-editar-perfil">
                                    <label htmlFor="localidad" className="form-label-editar-perfil">Localidad</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="localidad" name="localidad" value={formData.localidad} onChange={handleChange} className="form-control-editar-perfil" />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                    <label htmlFor="codigo_postal" className="form-label-editar-perfil">Código postal</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="codigo_postal" name="codigo_postal" value={formData.codigo_postal} onChange={handleChange} className="form-control-editar-perfil" />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                    <label htmlFor="provincia" className="form-label-editar-perfil">Provincia</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="provincia" name="provincia" value={formData.provincia} onChange={handleChange} className="form-control-editar-perfil" />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                    <label htmlFor="comunidad_autonoma" className="form-label-editar-perfil">Comunidad autónoma</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="comunidad_autonoma" name="comunidad_autonoma" value={formData.comunidad_autonoma} onChange={handleChange} className="form-control-editar-perfil" />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil span-3-editar-perfil">
                                    <label htmlFor="telefono" className="form-label-editar-perfil">Teléfono</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="text" id="telefono" name="telefono" value={formData.telefono} onChange={handleChange} required className="form-control-editar-perfil" />
                                    </div>
                                </div>
                                <div className="form-group-solicitud-editar-perfil span-3-editar-perfil">
                                    <label htmlFor="email" className="form-label-editar-perfil">Email</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required className="form-control-editar-perfil" />
                                    </div>
                                </div>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Datos bancarios</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="form-grid-4-editar-perfil">
                                <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                    <label htmlFor="iban" className="form-label-editar-perfil">IBAN de la cuenta</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input 
                                            type="text" 
                                            id="iban"
                                            name="iban" 
                                            value={formData.datos_bancarios.iban} 
                                            onChange={handleBankChange} 
                                            placeholder="ES00..." 
                                            required 
                                            className="form-control-editar-perfil"
                                        />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil">
                                    <label htmlFor="periodicidad" className="form-label-editar-perfil">Periodicidad</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <select 
                                            id="periodicidad"
                                            name="periodicidad" 
                                            value={formData.datos_bancarios.periodicidad} 
                                            onChange={handleBankChange}
                                            className="form-control-editar-perfil"
                                        >
                                            <option value="TRIMESTRAL">Trimestral</option>
                                            <option value="SEMESTRAL">Semestral</option>
                                            <option value="ANUAL">Anual</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil">
                                    <label className="form-label-editar-perfil">Titularidad</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <label 
                                            className={`form-control-editar-perfil checkbox-box-editar-perfil ${formData.datos_bancarios.es_titular ? 'checked' : ''}`}
                                        >
                                            <input 
                                                type="checkbox" 
                                                name="es_titular" 
                                                checked={formData.datos_bancarios.es_titular} 
                                                onChange={handleBankChange} 
                                                className="styled-checkbox-editar-perfil" 
                                            />
                                            <span>Soy titular de la cuenta</span>
                                        </label>
                                    </div>
                                </div>

                                {!formData.datos_bancarios.es_titular && (
                                    <div className="form-group-solicitud-editar-perfil span-2-editar-perfil">
                                        <label htmlFor="titular_cuenta" className="form-label-editar-perfil">Nombre y apellidos del titular</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="text" 
                                                id="titular_cuenta"
                                                name="titular_cuenta" 
                                                value={formData.datos_bancarios.titular_cuenta || ''} 
                                                onChange={handleBankChange} 
                                                placeholder="Solo si no es tu cuenta"
                                                required={!formData.datos_bancarios.es_titular} 
                                                className="form-control-editar-perfil"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Datos eclesiásticos</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="form-row-editar-perfil">
                                <div className="form-group-solicitud-editar-perfil">
                                    <label htmlFor="fecha_bautismo" className="form-label-editar-perfil">Fecha de bautismo</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input 
                                            type="date" 
                                            id="fecha_bautismo"
                                            name="fecha_bautismo" 
                                            value={readOnlyData.fecha_bautismo || ''} 
                                            disabled 
                                            className="form-control-editar-perfil"
                                        />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil">
                                    <label htmlFor="lugar_bautismo" className="form-label-editar-perfil">Localidad de bautismo</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input 
                                            type="text" 
                                            id="lugar_bautismo"
                                            name="lugar_bautismo" 
                                            value={readOnlyData.lugar_bautismo || ''} 
                                            disabled 
                                            className="form-control-editar-perfil"
                                        />
                                    </div>
                                </div>

                                <div className="form-group-solicitud-editar-perfil">
                                    <label htmlFor="parroquia_bautismo" className="form-label-editar-perfil">Parroquia de bautismo</label>
                                    <div className="input-wrapper-editar-perfil">
                                        <input 
                                            type="text" 
                                            id="parroquia_bautismo"
                                            name="parroquia_bautismo" 
                                            value={readOnlyData.parroquia_bautismo || ''} 
                                            disabled 
                                            className="form-control-editar-perfil"
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
                                        <label htmlFor="numero_registro" className="form-label-editar-perfil">Número de registro</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="number" 
                                                id="numero_registro"
                                                name="numero_registro" 
                                                value={readOnlyData.numero_registro || ''} 
                                                disabled 
                                                className="form-control-editar-perfil"
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
                                                value={readOnlyData.estado_hermano || ''} 
                                                disabled 
                                                className="form-control-editar-perfil"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="fecha_ingreso_corporacion" className="form-label-editar-perfil">Fecha ingreso</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="date" 
                                                id="fecha_ingreso_corporacion"
                                                name="fecha_ingreso_corporacion" 
                                                value={readOnlyData.fecha_ingreso || ''} 
                                                disabled 
                                                className="form-control-editar-perfil"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-solicitud-editar-perfil">
                                        <label htmlFor="fecha_baja_corporacion" className="form-label-editar-perfil">Fecha baja</label>
                                        <div className="input-wrapper-editar-perfil">
                                            <input 
                                                type="date" 
                                                id="fecha_baja_corporacion"
                                                name="fecha_baja_corporacion" 
                                                value={readOnlyData.fecha_baja || ''} 
                                                disabled 
                                                className="form-control-editar-perfil"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="form-actions-editar-perfil" style={{ justifyContent: 'space-between' }}>
                                <button 
                                    type="button" 
                                    className="btn-danger-editar-perfil" 
                                    onClick={() => navigate("/solicitar-baja")}
                                >
                                    <AlertCircle size={18} />
                                    Solicitar baja
                                </button>
                                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                    <button 
                                        type="button" 
                                        className="btn-cancel-editar-perfil" 
                                        onClick={() => navigate("/new-home")}
                                    >
                                        Cancelar
                                    </button>
                                    
                                    <button 
                                        type="submit" 
                                        className="btn-save-editar-perfil" 
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
    );
}

export default EditarMiPerfil;