import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminConsultaActo/AdminConsultaActo.css';
import '../HermanoConsultaActo/HermanoConsultaActo.css'
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
        return date.toLocaleString('es-ES', { 
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
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
                                <div className="designation-dashboard">{currentUser?.esAdmin ? "Administrador" : "Hermano"}</div>
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

            <section className="home-section-dashboard">
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

                            {acto?.descripcion && (
                                <div className="info-description">
                                    <Info size={22} className="info-icon" />
                                    <div style={{ width: '100%' }}>
                                        <span className="info-label">Descripción</span>
                                        <p 
                                            className="info-value-text" 
                                            style={{ whiteSpace: 'pre-wrap' }}
                                        >
                                            {acto.descripcion}
                                        </p>
                                    </div>
                                </div>
                            )}
                            
                            <div className="info-card-grid">
                                <div className="info-item">
                                    <MapPin size={22} className="info-icon" />
                                    <div>
                                        <span className="info-label">Lugar</span>
                                        <span className="info-value">{acto?.lugar || "No especificado"}</span>
                                    </div>
                                </div>

                                <div className="info-item">
                                    <Calendar size={22} className="info-icon" />
                                    <div>
                                        <span className="info-label">Fecha y Hora</span>
                                        <span className="info-value">{formatearFechaHora(acto?.fecha)}</span>
                                    </div>
                                </div>

                                <div className="info-item">
                                    <Ticket size={22} className="info-icon" />
                                    <div>
                                        <span className="info-label">Papeleta de Sitio</span>
                                        <span className="info-value">
                                            {acto?.requiere_papeleta ? (
                                                <span className="badge-yes">Obligatoria</span>
                                            ) : (
                                                <span className="badge-no">No requerida</span>
                                            )}
                                        </span>
                                    </div>
                                </div>
                            </div>

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

                            {acto?.requiere_papeleta && acto.modalidad === 'TRADICIONAL' && (
                                <div className="info-item">
                                    <Clock size={22} className="info-icon" />
                                    <div style={{ width: '100%' }}>
                                        <span className="info-label">Plazo Cirios</span>
                                        <div className="plazos-fechas-wrapper">
                                            <span className="info-value plazo-fecha">
                                                <strong>Inicio:</strong> {formatearFechaHora(acto.inicio_solicitud_cirios)}
                                            </span>
                                            <span className="info-value plazo-fecha">
                                                <strong>Fin:</strong> {formatearFechaHora(acto.fin_solicitud_cirios)}
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
            </section>

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