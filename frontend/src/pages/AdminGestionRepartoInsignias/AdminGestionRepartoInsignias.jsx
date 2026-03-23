import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminGestionRepartoInsignias/AdminGestionRepartoInsignias.css';
import { AlertCircle, Calendar, MapPin, Info, Ticket, ClipboardList, Award, Flame, ListOrdered, Clock } from "lucide-react";

import 'react-calendar/dist/Calendar.css';

function GestionRepartoInsignias() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false);
    
    const [currentUser, setCurrentUser] = useState(null);
    const [acto, setActo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [accesoDenegado, setAccesoDenegado] = useState(false);
    const [error, setError] = useState("");

    const [processing, setProcessing] = useState(false); 
    const [successData, setSuccessData] = useState(null); 

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

                if (!userData.esAdmin) {
                    if (isMounted) {
                        setAccesoDenegado(true);
                        setLoading(false);
                    }
                    return;
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

    const verificarDisponibilidad = () => {
        if (!acto || !acto.fin_solicitud) return false;
        const ahora = new Date();
        const finSolicitud = new Date(acto.fin_solicitud);
        return ahora > finSolicitud;
    };

    const handleReparto = async () => {
        if (!window.confirm(`¿Estás seguro de generar el reparto para "${acto.nombre}"?\n\nEsta acción asignará los puestos disponibles a los hermanos según su antigüedad.`)) {
            return;
        }

        setProcessing(true);
        setError("");
        setSuccessData(null);

        try {
            const response = await api.post(`/api/actos/${id}/reparto-automatico/`);
            setSuccessData(response.data); 
        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                setError(data.error || data.detail || "Error al procesar el reparto.");
            } else {
                setError("Error de red al intentar conectar con el servidor.");
            }
        } finally {
            setProcessing(false);
        }
    };

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setCurrentUser(null);
        navigate("/login");
    };

    if (loading) {
        return <div className="site-wrapper" style={{textAlign: 'center', marginTop: '50px'}}>Cargando...</div>;
    }

    if (accesoDenegado) {
        return (
            <div className="site-wrapper" style={{textAlign: 'center', marginTop: '50px'}}>
                <h2 style={{color: 'red'}}>🚫 Acceso Restringido</h2>
                <p>Esta sección es exclusiva para Administradores.</p>
                <button onClick={() => navigate("/home")} className="btn-purple">Volver al inicio</button>
            </div>
        );
    }

    const fechaValida = verificarDisponibilidad();

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

            <section className="home-section-dashboard">
                <div className="text-dashboard">Asignación de insignias</div>

                <div className="consulta-acto-content-layout">

                    <div className="consulta-acto-main-info">
                        {error && (
                            <div style={{padding: '15px', backgroundColor: '#fee2e2', color: '#b91c1c', marginBottom: '15px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '10px'}}>
                                <AlertCircle size={20}/> 
                                <span>{error}</span>
                            </div>
                        )}

                        {successData && (
                            <div style={{padding: '15px', backgroundColor: '#dcfce7', color: '#15803d', marginBottom: '15px', borderRadius: '6px', border: '1px solid #86efac'}}>
                                <div style={{display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 'bold', marginBottom: '10px'}}>
                                    <CheckCircle size={20}/> 
                                    <span>{successData.mensaje}</span>
                                </div>
                                <ul style={{marginLeft: '30px', listStyleType: 'disc', fontSize: '14px', lineHeight: '1.5'}}>
                                    <li>Puestos asignados correctamente: <strong>{successData.asignaciones}</strong></li>
                                    <li>Hermanos en lista de espera (sin cupo): <strong>{successData.sin_asignar_count}</strong></li>
                                </ul>
                            </div>
                        )}

                        <div className="consulta-acto-info-card">
                            <h3 className="consulta-acto-info-title">{acto?.nombre}</h3>

                            {acto?.imagen_portada && (
                                <img 
                                    src={acto.imagen_portada} 
                                    alt={`Portada de ${acto.nombre}`} 
                                    className="consulta-acto-card-cover-image"
                                />
                            )}

                            {acto?.descripcion && (
                                <div className="consulta-acto-info-description">
                                    <Info size={22} className="consulta-acto-info-icon" />
                                    <div style={{ width: '100%' }}>
                                        <span className="consulta-acto-info-label">Descripción</span>
                                        <p 
                                            className="consulta-acto-info-value-text" 
                                            style={{ whiteSpace: 'pre-wrap' }}
                                        >
                                            {acto.descripcion}
                                        </p>
                                    </div>
                                </div>
                            )}
                            
                            <div className="consulta-acto-info-grid">
                                <div className="consulta-acto-info-item">
                                    <MapPin size={22} className="consulta-acto-info-icon" />
                                    <div>
                                        <span className="consulta-acto-info-label">Lugar</span>
                                        <span className="consulta-acto-info-value">{acto?.lugar || "No especificado"}</span>
                                    </div>
                                </div>

                                <div className="consulta-acto-info-item">
                                    <Calendar size={22} className="consulta-acto-info-icon" />
                                    <div>
                                        <span className="consulta-acto-info-label">Fecha y Hora</span>
                                        <span className="consulta-acto-info-value">{formatearFechaHora(acto?.fecha)}</span>
                                    </div>
                                </div>

                                <div className="consulta-acto-info-item">
                                    <Ticket size={22} className="consulta-acto-info-icon" />
                                    <div>
                                        <span className="consulta-acto-info-label">Papeleta de Sitio</span>
                                        <span className="consulta-acto-info-value">
                                            {acto?.requiere_papeleta ? (
                                                <span className="consulta-acto-badge-yes">Obligatoria</span>
                                            ) : (
                                                <span className="consulta-acto-badge-no">No requerida</span>
                                            )}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {acto?.requiere_papeleta && (
                                <div className="consulta-acto-info-item">
                                    <Clock size={22} className="consulta-acto-info-icon" />
                                    <div style={{ width: '100%' }}>
                                        <span className="consulta-acto-info-label">
                                            {acto.modalidad === 'TRADICIONAL' ? 'Plazo Insignias' : 'Plazo Solicitudes'}
                                        </span>
                                        <div className="consulta-acto-plazos-fechas-wrapper">
                                            <span className="consulta-acto-info-value consulta-acto-plazo-fecha">
                                                <strong>Inicio:</strong> {formatearFechaHora(acto.inicio_solicitud)}
                                            </span>
                                            <span className="consulta-acto-info-value consulta-acto-plazo-fecha">
                                                <strong>Fin:</strong> {formatearFechaHora(acto.fin_solicitud)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {acto?.requiere_papeleta && acto.modalidad === 'TRADICIONAL' && (
                                <div className="consulta-acto-info-item">
                                    <Clock size={22} className="consulta-acto-info-icon" />
                                    <div style={{ width: '100%' }}>
                                        <span className="consulta-acto-info-label">Plazo Cirios</span>
                                        <div className="consulta-acto-plazos-fechas-wrapper">
                                            <span className="consulta-acto-info-value consulta-acto-plazo-fecha">
                                                <strong>Inicio:</strong> {formatearFechaHora(acto.inicio_solicitud_cirios)}
                                            </span>
                                            <span className="consulta-acto-info-value consulta-acto-plazo-fecha">
                                                <strong>Fin:</strong> {formatearFechaHora(acto.fin_solicitud_cirios)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                    </div>

                    <div className="consulta-acto-calendar-sidebar">
                        <div className="consulta-acto-algorithm-card">
                            <Award size={110} color="#ffffff" strokeWidth={1.5} className="consulta-acto-algorithm-icon" />
                            <h2 className="consulta-acto-algorithm-title">GESTIÓN DE INSIGNIAS</h2>
                            <p className="consulta-acto-algorithm-description">
                                Asigna y organiza los puestos e<br />insignias del cortejo.
                            </p>

                            <button 
                                className="consulta-acto-algorithm-button"
                                onClick={handleReparto}
                                disabled={!fechaValida || processing}
                                style={{
                                    backgroundColor: (!fechaValida || processing) ? '#94a3b8' : '#ffffff',
                                    cursor: (!fechaValida || processing) ? 'not-allowed' : 'pointer',
                                    color: (!fechaValida || processing) ? '#ffffff' : '#800020'
                                }}
                            >
                                {processing ? "Procesando algoritmos..." : "Ejecutar Algoritmo de Asignación"}
                            </button>
                            
                            {!fechaValida && (
                                <span style={{fontSize: '12px', color: '#e2e8f0', marginTop: '10px'}}>
                                    (Disponible al finalizar el plazo)
                                </span>
                            )}
                        </div>

                        {acto?.requiere_papeleta && acto?.modalidad === 'TRADICIONAL' && (
                            <div className="consulta-acto-actions-wrapper">
                                <div 
                                    className="consulta-acto-action-card"
                                    onClick={() => navigate(`/admin/listado-solicitudes-insignias/${id}`)}
                                >
                                    <div className="consulta-acto-action-card-content-wrapper">
                                        <ClipboardList size={45} color="#800020" className="consulta-acto-action-card-icon" />
                                        <div className="consulta-acto-action-card-text-content">
                                            <h3 className="consulta-acto-action-card-title">SOLICITUDES DE INSIGNIAS</h3>
                                            <p className="consulta-acto-action-card-description">Consulta el total de solicitudes de insignias.</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="consulta-acto-action-card">
                                    <div className="consulta-acto-action-card-content-wrapper">
                                        <Flame size={45} color="#800020" className="consulta-acto-action-card-icon" />
                                        <div className="consulta-acto-action-card-text-content">
                                            <h3 className="consulta-acto-action-card-title">SOLICITUDES DE CIRIOS</h3>
                                            <p className="consulta-acto-action-card-description">Consulta el total de solicitudes de cirios.</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="consulta-acto-action-card">
                                    <div className="consulta-acto-action-card-content-wrapper">
                                        <ListOrdered size={45} color="#800020" className="consulta-acto-action-card-icon" />
                                        <div className="consulta-acto-action-card-text-content">
                                            <h3 className="consulta-acto-action-card-title">ASIGNACIÓN DE CIRIOS</h3>
                                            <p className="consulta-acto-action-card-description">Asigna y organiza a los hermanos con cirio en el cortejo.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {acto?.requiere_papeleta && acto?.modalidad === 'UNIFICADO' && (
                            <div className="consulta-acto-actions-wrapper">
                                <div className="consulta-acto-action-card">
                                    <div className="consulta-acto-action-card-content-wrapper">
                                        <ClipboardList size={45} color="#800020" className="consulta-acto-action-card-icon" />
                                        <div className="consulta-acto-action-card-text-content">
                                            <h3 className="consulta-acto-action-card-title">SOLICITUDES DE PUESTOS</h3>
                                            <p className="consulta-acto-action-card-description">Consulta el total de solicitudes de puestos.</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="consulta-acto-action-card">
                                    <div className="consulta-acto-action-card-content-wrapper">
                                        <Award size={45} color="#800020" className="consulta-acto-action-card-icon" />
                                        <div className="consulta-acto-action-card-text-content">
                                            <h3 className="consulta-acto-action-card-title">GESTIÓN DE PUESTOS</h3>
                                            <p className="consulta-acto-action-card-description">Asigna y organiza los puestos del cortejo.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </section>
        </div>
    );
}

export default GestionRepartoInsignias;