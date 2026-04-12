import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminGestionRepartoInsignias/AdminGestionRepartoInsignias.css';
import { CalendarX, User, Users, AlertCircle, CheckCircle, Download, Settings } from "lucide-react";

import 'react-calendar/dist/Calendar.css';

function GestionRepartoInsignias() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false);
    
    const [currentUser, setCurrentUser] = useState(null);
    const [acto, setActo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [accesoDenegado, setAccesoDenegado] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const [processing, setProcessing] = useState(false); 
    const [successData, setSuccessData] = useState(null);

    const [downloading, setDownloading] = useState(false);
    const [downloadingVacantes, setDownloadingVacantes] = useState(false);

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
        if (error) {
            const timer = setTimeout(() => {
                setError("");
            }, 3000);

            return () => clearTimeout(timer);
        }
    }, [error]);

    useEffect(() => {
        if (success) {
            const timer = setTimeout(() => {
                setSuccess(false);
            }, 3000);

            return () => clearTimeout(timer);
        }
    }, [success]);

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
        if (!window.confirm(`¿Estás seguro de generar el reparto para "${acto.nombre}"?\n\nEsta acción asignará los puestos disponibles a los hermanos según su antigüedad y descargará el listado resultante.`)) {
            return;
        }

        setProcessing(true);
        setError("");
        setSuccessData(null);
        setSuccess(false);

        try {
            const response = await api.post(`/api/actos/${id}/reparto-automatico/`);
            
            const { pdf_base64, filename, detalle_algoritmo } = response.data;

            if (detalle_algoritmo) {
                setSuccessData(detalle_algoritmo);
            }

            if (pdf_base64) {
                const dataUrl = `data:application/pdf;base64,${pdf_base64}`;

                const fetchResponse = await fetch(dataUrl);
                const blob = await fetchResponse.blob();

                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename || `asignacion_insignias_${id}.pdf`;
                document.body.appendChild(link);
                link.click();

                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else {
                setError("El servidor respondió con éxito, pero no incluyó el documento PDF.");
            }

            setSuccess(true);
        } catch (err) {
            console.error("Error capturado:", err);
            
            if (err.response && err.response.data) {
                setError(err.response.data.error || err.response.data.detail || "Error al procesar el reparto.");
            } else {
                setError("Error de red al intentar conectar con el servidor.");
            }
        } finally {
            setProcessing(false);
        }
    };

    const handleDescargarListado = async () => {
        setDownloading(true);
        setError("");

        try {
            const response = await api.get(`/api/actos/${id}/descargar-listado-insignias/`, {
                responseType: 'blob' 
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `asignacion_insignias_${id}.pdf`);
            document.body.appendChild(link);
            link.click();

            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Error al descargar:", err);
            setError("Error al descargar el listado de insignias.");
        } finally {
            setDownloading(false);
        }
    };

    const handleDescargarVacantes = async () => {
        setDownloadingVacantes(true);
        setError("");

        try {
            const response = await api.get(`/api/actos/${id}/descargar-listado-vacantes/`, {
                responseType: 'blob' 
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `insignias_vacantes_${id}.pdf`);
            document.body.appendChild(link);
            link.click();

            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Error al descargar vacantes:", err);
            setError("Error al descargar el listado de insignias vacantes.");
        } finally {
            setDownloadingVacantes(false);
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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                <div className="dashboard-split-layout-solicitud">
                    <div className="dashboard-panel-gestion-solicitud">
                        <div className="historical-header-container">
                            <h1 className="historical-header-title">ASIGNACIÓN DE INSIGNIAS</h1>
                            <p className="historical-header-subtitle">
                                {getNombreTipoActo(acto?.tipo_acto)} {acto?.fecha ? new Date(acto.fecha).getFullYear() : ""}
                            </p>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">DATOS GENERALES DE SOLICITUD</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="plazos-cards-container">
                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <CalendarX size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">FIN SOLICITUD INSIGNIAS</h3>
                                    <p className="plazo-card-description">
                                        Fecha de cierre para la solicitud general de insignias, varas y maniguetas.
                                    </p>
                                    <div className="plazo-card-date">
                                        {formatearFechaHora(acto?.fin_solicitud)}
                                    </div>
                                </div>
                            </div>

                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <User size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">HERMANOS SOLICITANTES</h3>
                                    <p className="plazo-card-description">
                                        Censo total de hermanos con solicitud de insignia debidamente registrada y tramitada.
                                    </p>
                                    <div className="plazo-card-date">
                                        {acto?.total_solicitantes_insignia ?? 0}
                                    </div>
                                </div>
                            </div>

                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <Users size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">SOLICITUDES DE INSIGNIAS</h3>
                                    <p className="plazo-card-description">
                                        Número total de solicitudes de insignia registradas.
                                    </p>
                                    <div className="plazo-card-date">
                                        {acto?.total_solicitudes_insignias ?? 0}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">ALGORITMO AUTOMÁTICO DE ASIGNACIÓN DE INSIGNIAS</span>
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
                                <span>Asignación de insignias realizada correctamente. Descargando PDF...</span>
                            </div>
                        )}

                        <div className="algorithm-execution-container">
                            <div className="algorithm-card">
                                <div className="algorithm-content">
                                    <h2 className="algorithm-title">GESTIÓN Y REPARTO DE INSIGNIAS</h2>
                                    <p className="algorithm-description">
                                        El algoritmo evalúa las solicitudes registradas y asigna automáticamente los puestos e insignias del cortejo basándose en las reglas de antigüedad y disponibilidad establecidas por la hermandad.
                                    </p>
                                    <div className="algorithm-action">
                                        <button 
                                            className="algorithm-button"
                                            onClick={handleReparto}
                                            disabled={!fechaValida || processing}
                                        >
                                            <Settings size={20} />
                                            {processing ? "Procesando algoritmo..." : "Ejecutar algoritmo de asignación"}
                                        </button>
                                        {!fechaValida && (
                                            <span className="algorithm-warning">
                                                (Esta acción estará disponible al finalizar el plazo de solicitud)
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">RESUMEN DETALLADO DE LA ASIGNACIÓN DE INSIGNIAS</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="plazos-cards-container" style={{ marginTop: '20px' }}>
                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <Users size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">TOTAL INSIGNIAS</h3>
                                    <p className="plazo-card-description">
                                        Cupo máximo de insignias y puestos disponibles en el acto.
                                    </p>
                                    <div className="plazo-card-date">
                                        {acto?.total_insignias ?? "-"}
                                    </div>
                                </div>
                            </div>

                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">INSIGNIAS ASIGNADAS</h3>
                                    <p className="plazo-card-description">
                                        Total de puestos e insignias cubiertas tras el proceso de asignación.
                                    </p>
                                    <div className="plazo-card-date">
                                        {successData?.total_asignados ?? acto?.total_asignados ?? "-"}
                                    </div>
                                </div>
                            </div>

                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <AlertCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">INSIGNIAS VACANTES</h3>
                                    <p className="plazo-card-description">
                                        Listado de vacantes desiertas por falta de solicitudes o incumplimiento de requisitos.
                                    </p>
                                    <div className="plazo-card-date">
                                        {successData?.total_no_asignados ?? acto?.total_no_asignados ?? "-"}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {(successData || acto?.fecha_ejecucion_reparto) && (
                            <div className="download-buttons-container">
                                <button 
                                    className="algorithm-button"
                                    onClick={handleDescargarListado}
                                    disabled={downloading || downloadingVacantes}
                                >
                                    <Download size={20} />
                                    {downloading ? "Generando..." : "Descargar insignias asignadas (PDF)"}
                                </button>

                                <button 
                                    className="algorithm-button"
                                    onClick={handleDescargarVacantes}
                                    disabled={downloading || downloadingVacantes}
                                >
                                    <Download size={20} />
                                    {downloadingVacantes ? "Generando..." : "Descargar insignias vacantes (PDF)"}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default GestionRepartoInsignias;