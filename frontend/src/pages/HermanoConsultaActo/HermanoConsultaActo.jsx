import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminConsultaActo/AdminConsultaActo.css';
import '../HermanoConsultaActo/HermanoConsultaActo.css'
import '../HermanoConsultaNoticia/HermanoConsultaNoticia.css'
import { AlertCircle, Calendar, MapPin, Info, Ticket, ClipboardList, Award, Flame, ListOrdered, Clock, X } from "lucide-react";

import ReactCalendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';

function HermanoConsultaActo() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false);
    
    const [currentUser, setCurrentUser] = useState(null);
    const [acto, setActo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [fechaSeleccionada, setFechaSeleccionada] = useState(new Date());

    const [modalPlazo, setModalPlazo] = useState({ isOpen: false, titulo: '', mensaje: '' });

    const calendarRef = useRef(null);
    const [calendarHeight, setCalendarHeight] = useState('auto');

    const navigate = useNavigate();

    const formatearFechaHora = (dateString) => {
        if (!dateString) return "-";
        const date = new Date(dateString);

        const fecha = date.toLocaleDateString('es-ES', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric' 
        }).replace(/\//g, '-');

        const hora = date.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        return `${fecha} a las ${hora}`;
    };

    useEffect(() => {
        let isMounted = true; 

        const fetchData = async () => {
            setLoading(true);
            try {
                let userData = currentUser;
                if (!userData) {
                    const resUser = await api.get("/api/me/");
                    userData = resUser.data;
                    if (isMounted) setCurrentUser(userData);
                }

                const resActo = await api.get(`/api/actos/${id}/`);
                
                if (isMounted) {
                    setActo(resActo.data);
                }

            } catch (err) {
                console.error("Error:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else {
                    if (isMounted) setError("No se pudo cargar la información del acto.");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        if (id) {
            fetchData();
        }
        
        return () => {
            isMounted = false;
        };
    }, [id, navigate, currentUser]);

    useEffect(() => {
        if (!calendarRef.current) return;
        const observer = new ResizeObserver((entries) => {
            for (let entry of entries) {
                setCalendarHeight(entry.target.offsetHeight);
            }
        });
        observer.observe(calendarRef.current);
        return () => observer.disconnect();
    }, [acto]); 

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setCurrentUser(null);
        navigate("/login");
    };

    const handleSolicitarInsignias = () => {
        if (!acto || !acto.inicio_solicitud || !acto.fin_solicitud) {
            navigate(`/hermano/solicitar-insignias/${id}`);
            return;
        }

        const ahora = new Date();
        const inicio = new Date(acto.inicio_solicitud);
        const fin = new Date(acto.fin_solicitud);

        if (ahora < inicio) {
            setModalPlazo({
                isOpen: true,
                titulo: 'Plazo cerrado',
                mensaje: `El plazo para solicitar insignias abrirá el ${formatearFechaHora(acto.inicio_solicitud)} y finalizará el ${formatearFechaHora(acto.fin_solicitud)}.`
            });
        } else if (ahora > fin) {
            setModalPlazo({
                isOpen: true,
                titulo: 'Plazo finalizado',
                mensaje: `El plazo para solicitar insignias finalizó el ${formatearFechaHora(acto.fin_solicitud)}.`
            });
        } else {
            navigate(`/hermano/solicitar-insignias/${id}`);
        }
    };

    const handleSolicitarCirios = () => {
        if (!acto || !acto.inicio_solicitud_cirios || !acto.fin_solicitud_cirios) {
            navigate(`/hermano/solicitar-cirios/${id}`);
            return;
        }

        const ahora = new Date();
        const inicio = new Date(acto.inicio_solicitud_cirios);
        const fin = new Date(acto.fin_solicitud_cirios);

        if (ahora < inicio) {
            setModalPlazo({
                isOpen: true,
                titulo: 'Plazo cerrado',
                mensaje: `El plazo para solicitar cirios abrirá el ${formatearFechaHora(acto.inicio_solicitud_cirios)} y finalizará el ${formatearFechaHora(acto.fin_solicitud_cirios)}.`
            });
        } else if (ahora > fin) {
            setModalPlazo({
                isOpen: true,
                titulo: 'Plazo finalizado',
                mensaje: `El plazo para solicitar cirios finalizó el ${formatearFechaHora(acto.fin_solicitud_cirios)}.`
            });
        } else {
            navigate(`/hermano/solicitar-cirios/${id}`);
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

    const tileClassName = ({ date, view }) => {
        if (view === 'month' && acto && acto.fecha) {
            const fechaActo = new Date(acto.fecha);

            if (
                date.getDate() === fechaActo.getDate() &&
                date.getMonth() === fechaActo.getMonth() &&
                date.getFullYear() === fechaActo.getFullYear()
            ) {
                return 'dia-acto-burdeos';
            }
        }
        return null;
    };

    if (loading) {
        return <div className="site-wrapper" style={{textAlign: 'center', marginTop: '50px'}}>Cargando...</div>;
    }

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
                    <div className="dashboard-panel-evento">
                        <div className="historical-header-container-evento">
                            <h1 className="historical-header-title-evento">{acto.nombre}</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Detalles de la convocatoria</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="detalles-convocatoria-container">
                            <div className="detalle-item detalle-item-25">
                                <Calendar className="detalle-icon" size={32} strokeWidth={2.5} />
                                <div className="detalle-info">
                                    <span className="detalle-label">Fecha y Hora</span>
                                    <span className="detalle-valor">{formatearFechaHora(acto?.fecha)}</span>
                                </div>
                            </div>

                            <div className="detalle-item detalle-item-50">
                                <MapPin className="detalle-icon" size={32} strokeWidth={2.5} />
                                <div className="detalle-info">
                                    <span className="detalle-label">Lugar</span>
                                    <span className="detalle-valor">{acto?.lugar || "No especificado"}</span>
                                </div>
                            </div>

                            <div className="detalle-item detalle-item-25">
                                <Ticket className="detalle-icon" size={32} strokeWidth={2.5} />
                                <div className="detalle-info">
                                    <span className="detalle-label">Papeleta de Sitio</span>
                                    <span className={`detalle-valor ${acto?.requiere_papeleta ? 'obligatoria' : 'no-requerida'}`}>
                                        {acto?.requiere_papeleta ? "Obligatoria" : "No requerida"}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Descripción del acto</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="descripcion-acto-container">
                            <div className="descripcion-acto-texto">
                                {acto.descripcion ? (
                                    acto.descripcion.split('\n').map((parrafo, index) => {
                                        if (parrafo.trim() !== '') {
                                            return (
                                                <p key={index} className="descripcion-acto-parrafo">
                                                    {parrafo}
                                                </p>
                                            );
                                        }
                                        return null;
                                    })
                                ) : (
                                    <p className="descripcion-acto-parrafo">
                                        No hay información adicional disponible para este acto.
                                    </p>
                                )}
                            </div>
                        </div>

                        {acto?.requiere_papeleta && acto?.modalidad === 'TRADICIONAL' && (
                            <>
                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                    <span className="plazos-text">Plazos de solicitud de papeletas de sitio</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="detalles-convocatoria-container">
                                    <div className="detalle-item detalle-item-25">
                                        <div className="detalle-info">
                                            <span className="detalle-label">Inicio solicitud insignias</span>
                                            <span className="detalle-valor">{formatearFechaHora(acto?.inicio_solicitud)}</span>
                                        </div>
                                    </div>

                                    <div className="detalle-item detalle-item-25">
                                        <div className="detalle-info">
                                            <span className="detalle-label">Fin solicitud insignias</span>
                                            <span className="detalle-valor">{formatearFechaHora(acto?.fin_solicitud)}</span>
                                        </div>
                                    </div>

                                    <div className="detalle-item detalle-item-25">
                                        <div className="detalle-info">
                                            <span className="detalle-label">Inicio solicitud cirios</span>
                                            <span className="detalle-valor">{formatearFechaHora(acto?.inicio_solicitud_cirios)}</span>
                                        </div>
                                    </div>

                                    <div className="detalle-item detalle-item-25">
                                        <div className="detalle-info">
                                            <span className="detalle-label">Fin solicitud cirios</span>
                                            <span className="detalle-valor">{formatearFechaHora(acto?.fin_solicitud_cirios)}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                    <span className="plazos-text">Trámites y solicitudes</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="action-cards-container">
                                    <button className="action-card-button" onClick={handleSolicitarInsignias}>
                                        <ClipboardList size={45} color="#800020" className="action-card-icon" />
                                        <div className="action-card-text-content">
                                            <h3 className="action-card-title">SOLICITAR INSIGNIAS</h3>
                                            <p className="action-card-description">Realiza tu solicitud para portar una insignia.</p>
                                        </div>
                                    </button>

                                    <button className="action-card-button" onClick={handleSolicitarCirios}>
                                        <Flame size={45} color="#800020" className="action-card-icon" />
                                        <div className="action-card-text-content">
                                            <h3 className="action-card-title">SOLICITAR CIRIOS</h3>
                                            <p className="action-card-description">Realiza tu solicitud para participar portando un cirio.</p>
                                        </div>
                                    </button>
                                </div>

                                {currentUser?.esAdmin && (
                                    <>
                                        <div className="action-cards-container">
                                            <button className="action-card-button action-card-button-admin" onClick={() => navigate(`/admin/gestion-reparto-insignias/${id}`)}>
                                                <ListOrdered size={45} color="#ffffff" className="action-card-icon" />
                                                <div className="action-card-text-content">
                                                    <h3 className="action-card-title action-card-title-admin">ASIGNAR INSIGNIAS</h3>
                                                    <p className="action-card-description action-card-description-admin">Accede a la gestión y adjudicación de insignias.</p>
                                                </div>
                                            </button>

                                            <button className="action-card-button action-card-button-admin" onClick={() => navigate(`/admin/gestion-reparto-cirios/${id}`)}>
                                                <ListOrdered size={45} color="#ffffff" className="action-card-icon" />
                                                <div className="action-card-text-content">
                                                    <h3 className="action-card-title action-card-title-admin">ASIGNAR CIRIOS</h3>
                                                    <p className="action-card-description action-card-description-admin">Accede a la gestión y adjudicación de cirios.</p>
                                                </div>
                                            </button>
                                        </div>
                                    </>
                                )}
                            </>
                        )}

                        {acto?.requiere_papeleta && acto?.modalidad === 'UNIFICADA' && (
                            <>
                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                    <span className="plazos-text">Plazos de solicitud de papeletas de sitio</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="detalles-convocatoria-container">
                                    <div className="detalle-item detalle-item-50">
                                        <div className="detalle-info">
                                            <span className="detalle-label">Inicio de solicitud de insignias, varas y cirios</span>
                                            <span className="detalle-valor">{formatearFechaHora(acto?.inicio_solicitud)}</span>
                                        </div>
                                    </div>

                                    <div className="detalle-item detalle-item-50">
                                        <div className="detalle-info">
                                            <span className="detalle-label">Fin de solicitud de insignias, varas y cirios</span>
                                            <span className="detalle-valor">{formatearFechaHora(acto?.fin_solicitud)}</span>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                    </div>
                </div>
            </section>

            {/* <section className="home-section-dashboard">
                <div className="text-dashboard">Detalles del acto</div>

                <div className="dashboard-content-layout">

                    <div className="dashboard-main-info">
                        {error && (
                            <div className="error-message" style={{ color: 'red', marginBottom: '15px' }}>
                                <AlertCircle size={16} /> {error}
                            </div>
                        )}

                        <div className="info-card">
                            <h3 className="info-card-title">{acto.nombre}</h3>

                            {acto && (() => {
                                let imgSrc = '/portada-comunicado.png';

                                if (acto.imagen_portada) {
                                    const baseUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, "");
                                    const imagePath = acto.imagen_portada;
                                    imgSrc = imagePath.startsWith('http') 
                                        ? imagePath 
                                        : `${baseUrl}${imagePath.startsWith('/') ? imagePath : `/${imagePath}`}`;
                                }

                                return (
                                    <div className="acto-cover-image-container">
                                        <img 
                                            src={imgSrc} 
                                            alt={`Portada de ${acto.nombre}`} 
                                            className="acto-cover-image"
                                        />
                                    </div>
                                );
                            })()}

                            {acto?.requiere_papeleta && (
                                <div className="info-item">
                                    <Clock size={22} className="info-icon" />
                                    <div style={{ width: '100%' }}>
                                        <span className="info-label">
                                            {acto.modalidad === 'TRADICIONAL' ? 'Plazo Insignias' : 'Plazo Solicitudes'}
                                        </span>
                                        <div className="plazos-fechas-wrapper">
                                            <span className="info-value plazo-fecha">
                                                <strong>Inicio:</strong> {formatearFechaHora(acto.inicio_solicitud)}
                                            </span>
                                            <span className="info-value plazo-fecha">
                                                <strong>Fin:</strong> {formatearFechaHora(acto.fin_solicitud)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            
                        </div>

                    </div>

                    <div className="dashboard-calendar-sidebar">
                        
                        <div className="calendar-container" ref={calendarRef}>
                            <ReactCalendar 
                                onChange={setFechaSeleccionada} 
                                value={fechaSeleccionada}
                                className="custom-calendar"
                                tileClassName={tileClassName}
                            />
                        </div>

                        {acto?.requiere_papeleta && acto?.modalidad === 'TRADICIONAL' && (
                            <>
                                <div 
                                    className="action-card" 
                                    onClick={handleSolicitarInsignias}
                                >
                                    <div className="action-card-content-wrapper">
                                        <ClipboardList size={45} color="#800020" className="action-card-icon" />
                                        <div className="action-card-text-content">
                                            <h3 className="action-card-title">SOLICITAR INSIGNIAS</h3>
                                            <p className="action-card-description">Realiza tu solicitud para portar una insignia en el cortejo.</p>
                                        </div>
                                    </div>
                                </div>

                                <div 
                                    className="action-card" 
                                    onClick={handleSolicitarCirios}
                                >
                                    <div className="action-card-content-wrapper">
                                        <Flame size={45} color="#800020" className="action-card-icon" />
                                        <div className="action-card-text-content">
                                            <h3 className="action-card-title">SOLICITAR CIRIOS</h3>
                                            <p className="action-card-description">Realiza tu solicitud para participar portando un cirio.</p>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                        {acto?.requiere_papeleta && acto?.modalidad === 'UNIFICADO' && (
                            <>
                                <div 
                                    className="action-card"
                                    onClick={() => navigate(`/hermano/solicitar-papeleta/${id}`)}
                                >
                                    <div className="action-card-content-wrapper">
                                        <Ticket size={45} color="#800020" className="action-card-icon" />
                                        <div className="action-card-text-content">
                                            <h3 className="action-card-title">SOLICITAR PAPELETA DE SITIO</h3>
                                            <p className="action-card-description">Realiza tu solicitud para participar y asignar tu puesto.</p>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                    </div>
                </div>
            </section> */}

            {modalPlazo.isOpen && (
                <div className="modal-overlay-observacion" onClick={() => setModalPlazo({ isOpen: false, titulo: '', mensaje: '' })}>
                    <div className="modal-content-observacion" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header-observacion">
                            <h3>{modalPlazo.titulo}</h3>
                            <X 
                                size={24} 
                                style={{ cursor: 'pointer', color: 'var(--text-muted)' }} 
                                onClick={() => setModalPlazo({ isOpen: false, titulo: '', mensaje: '' })} 
                            />
                        </div>
                        <div className="modal-body-observacion">
                            <p>{modalPlazo.mensaje}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default HermanoConsultaActo;