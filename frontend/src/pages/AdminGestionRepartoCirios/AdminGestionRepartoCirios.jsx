import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";
import '../AdminGestionRepartoCirios/AdminGestionRepartoCirios.css';
import { Settings, CheckCircle, Flame, CalendarCheck, CalendarX, CalendarDays, AlertCircle, Download } from "lucide-react";

function GestionRepartoCirio() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false);

    const [currentUser, setCurrentUser] = useState(null);
    const [acto, setActo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const [processing, setProcessing] = useState(false);
    const [successData, setSuccessData] = useState(null);

    const [downloading, setDownloading] = useState(false);

    const navigate = useNavigate();

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

    const handleDescargarListado = async (filtroPaso = null) => {
        setDownloading(true);
        setError("");

        try {
            let url = `/api/actos/${id}/descargar-listado-cirios/`;
            if (filtroPaso) {
                url += `?paso=${filtroPaso}`;
            }

            const response = await api.get(url, {
                responseType: 'blob' 
            });

            let nombreArchivo = `asignacion_cirios_${id}.pdf`;
            if (filtroPaso === 'CRISTO') nombreArchivo = `asignacion_cirios_cristo_${id}.pdf`;
            if (filtroPaso === 'VIRGEN') nombreArchivo = `asignacion_cirios_virgen_${id}.pdf`;

            const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = blobUrl;
            link.setAttribute('download', nombreArchivo);
            document.body.appendChild(link);
            link.click();

            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
        } catch (err) {
            console.error("Error al descargar:", err);
            setError("Error al descargar el listado de cirios.");
        } finally {
            setDownloading(false);
        }
    };

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setCurrentUser(null);
        navigate("/login");
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
        });
    };

    const verificarDisponibilidad = () => {
        if (!acto || !acto.fin_solicitud_cirios) return false;
        const ahora = new Date();
        const final_solicitud_cirios = new Date(acto.fin_solicitud_cirios);
        return ahora > final_solicitud_cirios;
    };

    const fechaValida = verificarDisponibilidad();


    const handleReparto = async () => {
        if (!window.confirm(`⚠️ CONFIRMACIÓN REQUERIDA\n\n¿Estás seguro de ejecutar el algoritmo de asignación para "${acto.nombre}"?\n\nEsto borrará asignaciones de cirios previas y recalculará los tramos basándose en la antigüedad.`)) {
            return;
        }

        setProcessing(true);
        setError("");
        setSuccessData(null);
        setSuccess(false);

        try {
            const response = await api.post(`api/actos/${id}/reparto-cirios/`);

            const { pdf_base64, filename, asignadas } = response.data;
            
            setSuccessData(response.data);

            if (pdf_base64) {
                const dataUrl = `data:application/pdf;base64,${pdf_base64}`;

                const fetchResponse = await fetch(dataUrl);
                const blob = await fetchResponse.blob();

                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename || `asignacion_cirios_tramos_${id}.pdf`;
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
                            <h1 className="historical-header-title">ASIGNACIÓN DE CIRIOS</h1>
                            <p className="historical-header-subtitle">
                                {getNombreTipoActo(acto?.tipo_acto)} {acto?.fecha ? new Date(acto.fecha).getFullYear() : ""}
                            </p>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">DATOS GENERALES DE SOLICITUD</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="reparto-cards-container">
                            <div className="reparto-card-wrapper">
                                <div className="reparto-card-content">
                                    <div className="reparto-card-icon">
                                        <CalendarCheck size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="reparto-card-title">INICIO SOLICITUD CIRIOS</h3>
                                    <p className="reparto-card-description">
                                        Fecha de inicio para la solicitud general de cirios.
                                    </p>
                                    <div className="reparto-card-date">
                                        {formatearFechaHora(acto?.inicio_solicitud_cirios)}
                                    </div>
                                </div>
                            </div>

                            <div className="reparto-card-wrapper">
                                <div className="reparto-card-content">
                                    <div className="reparto-card-icon">
                                        <CalendarX size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="reparto-card-title">FIN SOLICITUD CIRIOS</h3>
                                    <p className="reparto-card-description">
                                        Fecha de cierre para la solicitud general de cirios.
                                    </p>
                                    <div className="reparto-card-date">
                                        {formatearFechaHora(acto?.fin_solicitud_cirios)}
                                    </div>
                                </div>
                            </div>

                            <div className="reparto-card-wrapper">
                                <div className="reparto-card-content">
                                    <div className="reparto-card-icon">
                                        <CalendarDays size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="reparto-card-title">FECHA DEL ACTO</h3>
                                    <p className="reparto-card-description">
                                        Fecha en la que se celebrará el acto.
                                    </p>
                                    <div className="reparto-card-date">
                                        {formatearFechaHora(acto?.fecha)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">ALGORITMO AUTOMÁTICO DE ASIGNACIÓN DE CIRIOS</span>
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
                                <span>Asignación de cirios realizada correctamente. Descargando PDF...</span>
                            </div>
                        )}

                        <div className="algorithm-execution-container">
                            <div className="algorithm-card">
                                <div className="algorithm-content">
                                    <h2 className="algorithm-title">GESTIÓN Y REPARTO DE TRAMOS Y CIRIOS</h2>
                                    <p className="algorithm-description">
                                        El algoritmo evalúa las solicitudes registradas y asigna automáticamente los cirios y tramos del cortejo basándose en las reglas de antigüedad y disponibilidad establecidas por la Hermandad.
                                    </p>
                                    <div className="algorithm-action">
                                        <button 
                                            className="algorithm-button"
                                            onClick={handleReparto}
                                            disabled={!fechaValida || processing}
                                        >
                                            <Settings size={20} />
                                            {processing ? "Procesando algoritmo..." : "Ejecutar algoritmo de asignación de tramos"}
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
                                <span className="plazos-text">RESUMEN DETALLADO DE LA ASIGNACIÓN DE TRAMOS Y CIRIOS</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="reparto-cards-container" style={{ marginTop: '20px' }}>
                            <div className="reparto-card-wrapper">
                                <div className="reparto-card-content">
                                    <div className="reparto-card-icon">
                                        <Flame size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="reparto-card-title">CIRIOS TOTALES</h3>
                                    <p className="reparto-card-description">
                                        Número total de Hermanos que han solicitado portar cirio.
                                    </p>
                                    <div className="reparto-card-date">
                                        {acto?.total_solicitantes_cirio ?? "-"}
                                    </div>
                                </div>
                            </div>

                            <div className="reparto-card-wrapper">
                                <div className="reparto-card-content">
                                    <div className="reparto-card-icon">
                                        <Flame size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="reparto-card-title">CIRIOS PASO CRISTO</h3>
                                    <p className="reparto-card-description">
                                        Número total de Hermanos que han solicitado portar cirio en el paso de Cristo.
                                    </p>
                                    <div className="reparto-card-date">
                                        {acto?.total_cirios_cristo ?? "-"}
                                    </div>
                                </div>
                            </div>

                            <div className="reparto-card-wrapper">
                                <div className="reparto-card-content">
                                    <div className="reparto-card-icon">
                                        <Flame size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="reparto-card-title">CIRIOS PASO VIRGEN</h3>
                                    <p className="reparto-card-description">
                                        Número total de Hermanos que han solicitado portar cirio en el paso de Virgen.
                                    </p>
                                    <div className="reparto-card-date">
                                        {acto?.total_cirios_virgen ?? "-"}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {(successData || acto?.fecha_ejecucion_cirios) && (
                            <div className="download-buttons-container-cirios">
                                <button 
                                    className="algorithm-button-cirios"
                                    onClick={() => handleDescargarListado()}
                                    disabled={downloading}
                                >
                                    <Download size={20} />
                                    {downloading ? "Generando..." : "Descargar Listado Completo"}
                                </button>

                                <button 
                                    className="algorithm-button-cirios"
                                    onClick={() => handleDescargarListado('CRISTO')}
                                    disabled={downloading}
                                >
                                    <Download size={20} />
                                    {downloading ? "Generando..." : "Descargar cirios Cristo"}
                                </button>

                                <button 
                                    className="algorithm-button-cirios"
                                    onClick={() => handleDescargarListado('VIRGEN')}
                                    disabled={downloading}
                                >
                                    <Download size={20} />
                                    {downloading ? "Generando..." : "Descargar cirios Virgen"}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default GestionRepartoCirio;