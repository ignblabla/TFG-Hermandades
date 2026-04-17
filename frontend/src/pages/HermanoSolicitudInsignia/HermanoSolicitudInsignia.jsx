import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../HermanoSolicitudInsignia/HermanoSolicitudInsignia.css';
import { Info, CalendarX, ScrollText, Shirt, ChevronDown, Send, ChevronRight, ArrowUp, ArrowDown, X, AlertCircle, CheckCircle, Medal, Flame, CalendarCheck } from "lucide-react";

function HermanoSolicitudInsignia() {
    const navigate = useNavigate();
    const { id } = useParams();
    
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false); 
    
    const [currentUser, setCurrentUser] = useState(null);
    const [actoActivo, setActoActivo] = useState(null);

    const [success, setSuccess] = useState(false); 
    const [error, setError] = useState("");

    const [insigniasSeleccionadas, setInsigniasSeleccionadas] = useState([]);
    const [isDragOver, setIsDragOver] = useState(false);

    const [mostrarCristo, setMostrarCristo] = useState(true);
    const [mostrarVirgen, setMostrarVirgen] = useState(true);

    const [modalBloqueo, setModalBloqueo] = useState(false);
    const [modalNoActivo, setModalNoActivo] = useState(false);
    const [modalFueraPlazoConSolicitud, setModalFueraPlazoConSolicitud] = useState(false);
    const [fechaSolicitudRealizada, setFechaSolicitudRealizada] = useState(null);

    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                if (isMounted) setCurrentUser(resUser.data);

                try {
                    const resActo = await api.get(`api/actos/${id}/`); 
                    if (isMounted) {
                        const acto = resActo.data;
                        setActoActivo(acto);

                        const now = new Date();
                        const inicioPlazo = new Date(acto.inicio_solicitud);
                        const finPlazo = new Date(acto.fin_solicitud);
                        const enPlazo = now >= inicioPlazo && now <= finPlazo;

                        try {
                            const resPapeletas = await api.get("api/papeletas/mis-papeletas/");
                            const misPapeletas = resPapeletas.data.results || resPapeletas.data;
                            
                            const papeletaActiva = misPapeletas.find(p => {
                                const coincideActo = Number(p.acto) === Number(id); 
                                const estado = String(p.estado_papeleta || '').toUpperCase();
                                const estaActiva = estado !== 'ANULADA' && estado !== 'NO_ASIGNADA';

                                return coincideActo && estaActiva;
                            });

                            if (papeletaActiva) {
                                if (enPlazo) {
                                    setModalBloqueo(true);
                                } else {
                                    setFechaSolicitudRealizada(papeletaActiva.fecha_solicitud || papeletaActiva.fecha_emision || papeletaActiva.created_at);
                                    setModalFueraPlazoConSolicitud(true);
                                }
                            } else {
                                if (!enPlazo) {
                                    setModalNoActivo(true);
                                }
                            }
                        } catch (errPapeletas) {
                            console.error("Error verificando papeletas previas:", errPapeletas);
                        }
                    }
                } catch (errActo) {
                    if (errActo.response && errActo.response.status === 404) {
                        if (isMounted) {
                            setActoActivo(null);
                            setModalNoActivo(true);
                        }
                    } else {
                        console.error("Error obteniendo el acto activo:", errActo);
                    }
                }

            } catch (err) {
                console.error("Error de autenticación o servidor:", err);
                if (err.response?.status === 401) {
                    navigate("/login");
                }
            } finally {
                setTimeout(() => {
                    if (isMounted) setLoading(false);
                }, 3000);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [id, navigate]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    const handleDragStart = (e, insignia) => {
        e.dataTransfer.setData('insignia', JSON.stringify(insignia));
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => {
        setIsDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);
        const insigniaData = e.dataTransfer.getData('insignia');
        
        if (insigniaData) {
            const insignia = JSON.parse(insigniaData);
            if (!insigniasSeleccionadas.some(i => i.id === insignia.id)) {
                setInsigniasSeleccionadas([...insigniasSeleccionadas, insignia]);
            }
        }
    };

    const moverArriba = (index) => {
        if (index === 0) return;
        const nuevas = [...insigniasSeleccionadas];
        const temp = nuevas[index];
        nuevas[index] = nuevas[index - 1];
        nuevas[index - 1] = temp;
        setInsigniasSeleccionadas(nuevas);
    };

    const moverAbajo = (index) => {
        if (index === insigniasSeleccionadas.length - 1) return;
        const nuevas = [...insigniasSeleccionadas];
        const temp = nuevas[index];
        nuevas[index] = nuevas[index + 1];
        nuevas[index + 1] = temp;
        setInsigniasSeleccionadas(nuevas);
    };

    const quitarInsignia = (idSeleccionada) => {
        setInsigniasSeleccionadas(insigniasSeleccionadas.filter(i => i.id !== idSeleccionada));
    };

    const enviarSolicitud = async () => {
        setSaving(true);
        setError(""); 
        setSuccess(false);

        const payload = {
            acto_id: Number(id),
            preferencias: insigniasSeleccionadas.map((insignia, index) => ({
                puesto_solicitado: insignia.id,
                orden_prioridad: index + 1
            }))
        };

        try {
            await api.post("api/papeletas/solicitar-insignia/", payload);
            setSuccess(true); 
            
            setTimeout(() => {
                navigate("/home");
            }, 2500);

        } catch (err) {
            console.error("Error al enviar solicitud:", err);
            setError("Ocurrió un problema de conexión con el servidor. Por favor, inténtelo de nuevo.");
        } finally {
            setSaving(false);
        }
    };

    const getNombreTipoActo = (tipo) => {
        if (!tipo) return "de Sitio";

        const tipoStr = typeof tipo === 'object' ? tipo.tipo : tipo;
        
        const diccionarioTipos = {
            'ESTACION_PENITENCIA': 'Estación de Penitencia',
            'CABILDO_GENERAL': 'Cabildo General',
            'CABILDO_EXTRAORDINARIO': 'Cabildo Extraordinario',
            'VIA_CRUCIS': 'Vía Crucis',
            'QUINARIO': 'Quinario',
            'TRIDUO': 'Triduo',
            'ROSARIO_AURORA': 'Rosario de la Aurora',
            'CONVIVENCIA': 'Convivencia',
            'PROCESION_EUCARISTICA': 'Procesión Eucarística',
            'PROCESION_EXTRAORDINARIA': 'Procesión Extraordinaria'
        };

        return diccionarioTipos[tipoStr] || "de Sitio";
    };

    const formatearFechaHora = (dateString) => {
        if (!dateString) return "-";
        const date = new Date(dateString);

        return date.toLocaleString('es-ES', { 
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        }).replaceAll('/', '-');
    };

    const insigniasDisponibles = actoActivo?.puestos_disponibles?.filter(
        p => !insigniasSeleccionadas.some(seleccionada => seleccionada.id === p.id)
    ) || [];

    const insigniasCristo = insigniasDisponibles.filter(p => p.cortejo_cristo);
    const insigniasVirgen = insigniasDisponibles.filter(p => !p.cortejo_cristo);

    const renderInsignias = (insignias) => {
        if (insignias.length === 0) {
            return (
                <p className="solicitud-insignia-empty-msg">
                    No hay insignias disponibles para este cortejo.
                </p>
            );
        }

        return (
            <div className="insignias-grid-container">
                {insignias.map((insignia) => (
                    <div 
                        key={insignia.id} 
                        className="insignia-card"
                        draggable
                        onDragStart={(e) => handleDragStart(e, insignia)}
                    >
                        <h4 className="insignia-card-title">
                            {insignia.nombre}
                        </h4>
                    </div>
                ))}
            </div>
        );
    };

    if (loading) {
        const loadingText = "Comprobando estado de la solicitud...";
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#FAF9F6' }}>
                <h3 className="loading-animated-text" style={{ color: '#800020' }}>
                    {loadingText.split("").map((char, index) => (
                        <span key={index} style={{ animationDelay: `${index * 0.05}s` }}>
                            {char === " " ? "\u00A0" : char}
                        </span>
                    ))}
                </h3>
            </div>
        );
    }

    return (
        <div>
            {modalBloqueo && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Solicitud ya realizada</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            <p>
                                Ya consta una solicitud activa de papeleta de sitio para el acto <strong>{actoActivo?.nombre}</strong>.
                                <br/><br/>
                                Le recordamos que <strong>no es posible realizar múltiples solicitudes de insignias para un mismo acto</strong>. Si desea hacer cambios, por favor contacte con secretaría.
                            </p>
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {modalFueraPlazoConSolicitud && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Solicitud ya registrada</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            <p>
                                Usted ya realizó una solicitud para el acto <strong>{actoActivo?.nombre}</strong> el día <strong>{formatearFechaHora(fechaSolicitudRealizada)}</strong>.
                                <br/><br/>
                                Actualmente el plazo de modificación o nuevas solicitudes se encuentra cerrado.
                            </p>
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {modalNoActivo && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Plazo cerrado</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            {actoActivo && actoActivo.inicio_solicitud && actoActivo.fin_solicitud ? (
                                new Date() < new Date(actoActivo.inicio_solicitud) ? (
                                    <p>
                                        El plazo para solicitar insignias aún no se encuentra abierto. Comenzará el próximo <strong>{formatearFechaHora(actoActivo.inicio_solicitud)}</strong>. Por favor, vuelva a intentarlo más adelante.
                                    </p>
                                ) : (
                                    <p>
                                        El plazo para solicitar insignias ya ha concluido (finalizó el <strong>{formatearFechaHora(actoActivo.fin_solicitud)}</strong>).
                                    </p>
                                )
                            ) : (
                                <p>
                                    Actualmente el plazo para solicitar insignias no se encuentra abierto o ya ha concluido. Por favor, manténgase atento a los comunicados oficiales de la Hermandad.
                                </p>
                            )}
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {!modalBloqueo && !modalNoActivo && !modalFueraPlazoConSolicitud && (
                <>
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

                    <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                        <div className="dashboard-split-layout-solicitud">
                            <div className="dashboard-panel-solicitud">
                                <div className="historical-header-container-solicitud">
                                    <h1 className="historical-header-title-solicitud">SOLICITUD DE INSIGNIAS</h1>
                                    <p className="historical-header-subtitle-solicitud">
                                        {getNombreTipoActo(actoActivo?.tipo_acto)} {actoActivo?.fecha ? new Date(actoActivo.fecha).getFullYear() : ""}
                                    </p>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Datos generales de la solicitud de insignias</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="solicitud-cards-container">
                                    <div className="solicitud-card-wrapper">
                                        <div className="solicitud-card-content">
                                            <div className="solicitud-card-icon">
                                                <CalendarCheck size={32} strokeWidth={2.5} />
                                            </div>
                                            <h3 className="solicitud-card-title">INICIO SOLICITUD INSIGNIAS</h3>
                                            <p className="solicitud-card-description">
                                                Fecha de inicio para la solicitud general de insignias, cirios apagados, maniguetas y varas.
                                            </p>
                                            <div className="solicitud-card-date">
                                                {formatearFechaHora(actoActivo?.inicio_solicitud)}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="solicitud-card-wrapper">
                                        <div className="solicitud-card-content">
                                            <div className="solicitud-card-icon">
                                                <CalendarX size={32} strokeWidth={2.5} />
                                            </div>
                                            <h3 className="solicitud-card-title">FIN SOLICITUD INSIGNIAS</h3>
                                            <p className="solicitud-card-description">
                                                Fecha de cierre para la solicitud general de insignias, cirios apagados, maniguetas y varas.
                                            </p>
                                            <div className="solicitud-card-date">
                                                {formatearFechaHora(actoActivo?.fin_solicitud)}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="solicitud-card-wrapper">
                                        <div className="solicitud-card-content">
                                            <div className="solicitud-card-icon">
                                                <Medal size={32} strokeWidth={2.5} />
                                            </div>
                                            <h3 className="solicitud-card-title">INSIGNIAS DISPONIBLES</h3>
                                            <p className="solicitud-card-description">
                                                Número total de insignias, cirios apagados, maniguetas y varas configuradas para este acto.
                                            </p>
                                            <div className="solicitud-card-date">
                                                {actoActivo?.total_insignias ?? 0}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Formulario de solicitud de insignias</span>
                                    <div className="plazos-line"></div>
                                </div>

                                {error && (
                                    <div className="form-alert form-alert-error" style={{ marginBottom: '20px' }}>
                                        <AlertCircle size={20} />
                                        <span>{error}</span>
                                    </div>
                                )}
                                
                                {success && (
                                    <div className="form-alert form-alert-success" style={{ marginBottom: '20px' }}>
                                        <CheckCircle size={20} />
                                        <span>Solicitud procesada correctamente. Redirigiendo a sus papeletas...</span>
                                    </div>
                                )}

                                <div className="dashboard-layout-wrapper">
                                    {actoActivo ? (
                                        <>
                                            <div className="solicitud-insignia-container">
                                                <h3 className="solicitud-insignia-title">Insignias disponibles</h3>
                                                <p className="solicitud-insignia-description mb-10">
                                                    Arrastre las insignias que desea solicitar hacia el panel de la derecha.
                                                </p>

                                                <div className="lista-disponibles-container">
                                                    {insigniasDisponibles.length > 0 ? (
                                                        <>
                                                            <div 
                                                                className="cortejo-subtitle-wrapper" 
                                                                onClick={() => setMostrarCristo(!mostrarCristo)}
                                                            >
                                                                <h4 className="cortejo-subtitle">
                                                                    Cortejo de Nuestro Padre Jesús en Su Soberano Poder ante Caifás
                                                                </h4>
                                                                {mostrarCristo ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                                            </div>

                                                            {mostrarCristo && renderInsignias(insigniasCristo)}

                                                            <div 
                                                                className="cortejo-subtitle-wrapper" 
                                                                onClick={() => setMostrarVirgen(!mostrarVirgen)}
                                                            >
                                                                <h4 className="cortejo-subtitle">
                                                                    Cortejo de Nuestra Señora de la Salud
                                                                </h4>
                                                                {mostrarVirgen ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                                            </div>

                                                            {mostrarVirgen && renderInsignias(insigniasVirgen)}
                                                        </>
                                                    ) : (
                                                        <p className="solicitud-insignia-empty-msg">
                                                            Has seleccionado todas las insignias disponibles.
                                                        </p>
                                                    )}
                                                </div>
                                            </div>

                                            <div 
                                                className={`resumen-solicitud-container ${isDragOver ? 'drag-over-active' : ''}`}
                                                onDragOver={handleDragOver}
                                                onDragLeave={handleDragLeave}
                                                onDrop={handleDrop}
                                            >
                                                <h3 className="solicitud-insignia-title">Insignias seleccionadas</h3>
                                                <p className="solicitud-insignia-description">
                                                    Suéltelas aquí. Ordénelas de arriba a abajo en función de su prioridad.
                                                </p>

                                                <div className="lista-seleccionadas-container">
                                                    {insigniasSeleccionadas.length === 0 ? (
                                                        <div className="empty-dropzone">
                                                            Arrastre aquí una insignia
                                                        </div>
                                                    ) : (
                                                        insigniasSeleccionadas.map((insignia, index) => (
                                                            <div key={insignia.id} className="seleccionada-card">
                                                                <div className="seleccionada-info">
                                                                    <span className="prioridad-badge">{index + 1}º</span>
                                                                    <span className="seleccionada-nombre">{insignia.nombre}</span>
                                                                </div>
                                                                
                                                                <div className="seleccionada-acciones">
                                                                    <button 
                                                                        onClick={() => moverArriba(index)} 
                                                                        disabled={index === 0}
                                                                        title="Subir prioridad"
                                                                    >
                                                                        <ArrowUp size={18} />
                                                                    </button>
                                                                    <button 
                                                                        onClick={() => moverAbajo(index)} 
                                                                        disabled={index === insigniasSeleccionadas.length - 1}
                                                                        title="Bajar prioridad"
                                                                    >
                                                                        <ArrowDown size={18} />
                                                                    </button>
                                                                    <button 
                                                                        onClick={() => quitarInsignia(insignia.id)} 
                                                                        className="btn-quitar"
                                                                        title="Quitar de la lista"
                                                                    >
                                                                        <X size={18} />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        ))
                                                    )}
                                                </div>

                                                <div className="btn-enviar-wrapper">
                                                    <button 
                                                        className="btn-enviar-solicitud-final"
                                                        onClick={enviarSolicitud}
                                                        disabled={saving || insigniasSeleccionadas.length === 0}
                                                    >
                                                        <Send size={20} />
                                                        {saving ? "Procesando..." : "Enviar Solicitud de Insignias"}
                                                    </button>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="solicitud-insignia-container" style={{width: '100%'}}>
                                            <p className="solicitud-insignia-error-msg">
                                                Actualmente no hay ningún plazo abierto para solicitar insignias.
                                            </p>
                                        </div>
                                    )}
                                </div>

                            </div>
                        </div>
                    </section>

                    {/* <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                        <div className="dashboard-split-layout-solicitud">
                            <div className="dashboard-panel-main-solicitud">

                                <div className="dashboard-layout-wrapper">
                                    {actoActivo ? (
                                        <>
                                            <div className="solicitud-insignia-container">
                                                <h3 className="solicitud-insignia-title">Insignias disponibles</h3>
                                                <p className="solicitud-insignia-description mb-10">
                                                    Arrastre las insignias que desea solicitar hacia el panel de la derecha.
                                                </p>

                                                <div className="lista-disponibles-container">
                                                    {insigniasDisponibles.length > 0 ? (
                                                        <>
                                                            <div 
                                                                className="cortejo-subtitle-wrapper" 
                                                                onClick={() => setMostrarCristo(!mostrarCristo)}
                                                            >
                                                                <h4 className="cortejo-subtitle">
                                                                    Cortejo de Nuestro Padre Jesús en Su Soberano Poder ante Caifás
                                                                </h4>
                                                                {mostrarCristo ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                                            </div>

                                                            {mostrarCristo && renderInsignias(insigniasCristo)}

                                                            <div 
                                                                className="cortejo-subtitle-wrapper" 
                                                                onClick={() => setMostrarVirgen(!mostrarVirgen)}
                                                            >
                                                                <h4 className="cortejo-subtitle">
                                                                    Cortejo de Nuestra Señora de la Salud
                                                                </h4>
                                                                {mostrarVirgen ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                                            </div>

                                                            {mostrarVirgen && renderInsignias(insigniasVirgen)}
                                                        </>
                                                    ) : (
                                                        <p className="solicitud-insignia-empty-msg">
                                                            Has seleccionado todas las insignias disponibles.
                                                        </p>
                                                    )}
                                                </div>
                                            </div>

                                            <div 
                                                className={`resumen-solicitud-container ${isDragOver ? 'drag-over-active' : ''}`}
                                                onDragOver={handleDragOver}
                                                onDragLeave={handleDragLeave}
                                                onDrop={handleDrop}
                                            >
                                                <h3 className="solicitud-insignia-title">Insignias seleccionadas</h3>
                                                <p className="solicitud-insignia-description">
                                                    Suéltelas aquí. Ordénelas de arriba a abajo en función de su prioridad.
                                                </p>

                                                <div className="lista-seleccionadas-container">
                                                    {insigniasSeleccionadas.length === 0 ? (
                                                        <div className="empty-dropzone">
                                                            Arrastre aquí una insignia
                                                        </div>
                                                    ) : (
                                                        insigniasSeleccionadas.map((insignia, index) => (
                                                            <div key={insignia.id} className="seleccionada-card">
                                                                <div className="seleccionada-info">
                                                                    <span className="prioridad-badge">{index + 1}º</span>
                                                                    <span className="seleccionada-nombre">{insignia.nombre}</span>
                                                                </div>
                                                                
                                                                <div className="seleccionada-acciones">
                                                                    <button 
                                                                        onClick={() => moverArriba(index)} 
                                                                        disabled={index === 0}
                                                                        title="Subir prioridad"
                                                                    >
                                                                        <ArrowUp size={18} />
                                                                    </button>
                                                                    <button 
                                                                        onClick={() => moverAbajo(index)} 
                                                                        disabled={index === insigniasSeleccionadas.length - 1}
                                                                        title="Bajar prioridad"
                                                                    >
                                                                        <ArrowDown size={18} />
                                                                    </button>
                                                                    <button 
                                                                        onClick={() => quitarInsignia(insignia.id)} 
                                                                        className="btn-quitar"
                                                                        title="Quitar de la lista"
                                                                    >
                                                                        <X size={18} />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        ))
                                                    )}
                                                </div>

                                                <div className="btn-enviar-wrapper">
                                                    <button 
                                                        className="btn-enviar-solicitud-final"
                                                        onClick={enviarSolicitud}
                                                        disabled={saving || insigniasSeleccionadas.length === 0}
                                                    >
                                                        <Send size={20} />
                                                        {saving ? "Procesando..." : "Enviar Solicitud de Insignias"}
                                                    </button>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="solicitud-insignia-container" style={{width: '100%'}}>
                                            <p className="solicitud-insignia-error-msg">
                                                Actualmente no hay ningún plazo abierto para solicitar insignias.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="dashboard-panel-sidebar-solicitud">
                                <div className="criterios-card">
                                    <div className="criterios-icon">
                                        <ScrollText size={40} strokeWidth={2} />
                                    </div>
                                    
                                    <h2 className="criterios-title">CRITERIOS DE ASIGNACIÓN</h2>
                                    
                                    <p className="criterios-intro">
                                        Conforme a la Regla 42ª, los puestos se asignan estrictamente por <span className="criterios-bold">orden de antigüedad</span> en la nómina <span className="criterios-bold">de hermanos</span>, salvo los cargos de confianza designados por la Junta de Gobierno.
                                    </p>
                                </div>

                                <div className="criterios-card">
                                    <div className="criterios-icon">
                                        <Shirt size={40} strokeWidth={2} />
                                    </div>
                                    
                                    <h2 className="criterios-title">PROTOCOLO DE VESTIMENTA</h2>
                                    
                                    <p className="criterios-intro">
                                        {actoActivo?.tipo_acto === 'ESTACION_PENITENCIA' ? (
                                            <>
                                                Se recuerda la obligatoriedad de vestir el hábito de la Hermandad:{" "}
                                                <span className="criterios-bold">
                                                    túnica blanca de cola, cinturón de esparto, medalla de la Hermandad y sandalias de cuero
                                                </span>.
                                            </>
                                        ) : (
                                            <>
                                                Se recuerda la obligatoriedad de mantener la estética tradicional:{" "}
                                                <span className="criterios-bold">traje de chaqueta oscuro</span> para los hombres y{" "}
                                                <span className="criterios-bold">vestido negro</span> para las mujeres, acorde a la solemnidad del acto.
                                                <br />
                                                <span className="criterios-bold">Imprescindible portar la medalla de la Hermandad.</span>
                                            </>
                                        )}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section> */}
                </>
            )}
        </div>
    );
}

export default HermanoSolicitudInsignia;