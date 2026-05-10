import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";
import '../AdminGestionRepartoCirios/AdminGestionRepartoCirios.css';
import { Settings, CheckCircle, Flame, CalendarCheck, CalendarX, CalendarDays, AlertCircle, Download, AlertTriangle } from "lucide-react";

function GestionRepartoCirio() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false);

    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [accesoDenegado, setAccesoDenegado] = useState(false);

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

    const verificarDisponibilidad = () => {
        if (!acto || !acto.fin_solicitud_cirios) return false;
        const ahora = new Date();
        const final_solicitud_cirios = new Date(acto.fin_solicitud_cirios);
        return ahora > final_solicitud_cirios;
    };

    const fechaValida = verificarDisponibilidad();


    const handleReparto = () => {
        setShowConfirmModal(true);
    };

    const handleConfirmReparto = async () => {
        setShowConfirmModal(false);
        setProcessing(true);
        setError("");
        setSuccessData(null);
        setSuccess(false);

        try {
            const response = await api.post(`api/actos/${id}/reparto-cirios/`);
            const { pdf_base64, filename } = response.data;

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
                <p>Esta sección es exclusiva para la Secretaría.</p>
                <button onClick={() => navigate("/new-home")} className="btn-purple">Volver al inicio</button>
            </div>
        );
    }

    return (
        <div>
            <div className="toast-container-crear-comunicado">
                {success && (
                    <div className="toast-message-crear-comunicado toast-success-crear-comunicado">
                        <CheckCircle size={24} />
                        <span>Asignación de cirios realizada correctamente. Descargando PDF...</span>
                    </div>
                )}
                {error && (
                    <div className="toast-message-crear-comunicado toast-error-crear-comunicado">
                        <AlertCircle size={24} />
                        <span>{error}</span>
                    </div>
                )}
            </div>

            {showConfirmModal && (
                <div className="modal-overlay-confirmacion">
                    <div className="modal-content-confirmacion">
                        <div className="modal-header-confirmacion">
                            <AlertTriangle className="modal-icon-warning" size={28} />
                            <h3>Confirmar asignación</h3>
                        </div>
                        <div className="modal-body-confirmacion">
                            <p>
                                ¿Estás seguro de ejecutar el algoritmo de asignación para <strong>"{acto?.nombre}"</strong>?
                                <br /><br />
                                Esta acción <strong>borrará las asignaciones de cirios previas</strong> y recalculará los tramos basándose en la antigüedad de los Hermanos.
                            </p>
                            <div className="modal-actions-confirmacion">
                                <button
                                    className="btn-cancelar-modal"
                                    onClick={() => setShowConfirmModal(false)}
                                >
                                    Cancelar
                                </button>
                                <button
                                    className="btn-confirmar-modal"
                                    onClick={handleConfirmReparto}
                                >
                                    Confirmar y ejecutar
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
                                    {downloading ? "Generando..." : "Descargar listado completo"}
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