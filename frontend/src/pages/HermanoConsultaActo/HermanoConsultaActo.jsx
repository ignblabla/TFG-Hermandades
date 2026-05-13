import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminConsultaActo/AdminConsultaActo.css';
import '../HermanoConsultaActo/HermanoConsultaActo.css'
import '../HermanoConsultaNoticia/HermanoConsultaNoticia.css'
import { AlertCircle, Calendar, MapPin, Info, Ticket, ClipboardList, Award, Flame, ListOrdered, Clock, X, Edit, Trash2, Users, Plus, CheckCircle  } from "lucide-react";

import ReactCalendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';

function HermanoConsultaActo() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false);
    
    const [currentUser, setCurrentUser] = useState(null);
    const [acto, setActo] = useState(null);
    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    const [fechaSeleccionada, setFechaSeleccionada] = useState(new Date());

    const [showConfirmDeleteModal, setShowConfirmDeleteModal] = useState(false);

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
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [error]);

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

    const handleEliminarActo = () => {
        setShowConfirmDeleteModal(true);
    };

    const handleConfirmEliminar = async () => {
        setShowConfirmDeleteModal(false);
        try {
            await api.delete(`/api/actos/${id}/`);
            setSuccessMsg("Acto eliminado correctamente.");
            setTimeout(() => {
                setSuccessMsg("");
                navigate("/listado-actos");
            }, 3000);
        } catch (err) {
            const errorData = err.response?.data;
            if (typeof errorData === 'object' && errorData !== null && !Array.isArray(errorData)) {
                const mensajes = Object.entries(errorData)
                    .map(([_, errores]) => Array.isArray(errores) ? errores.join(', ') : String(errores))
                    .join(' | ');
                setError(mensajes || "Error al eliminar el acto.");
            } else {
                setError("Hubo un error al intentar eliminar el acto.");
            }
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

            {showConfirmDeleteModal && (
                <div className="modal-overlay-confirmacion">
                    <div className="modal-content-confirmacion">
                        <div className="modal-header-confirmacion">
                            <Trash2 className="modal-icon-warning" size={28} />
                            <h3>Confirmar eliminación</h3>
                        </div>
                        <div className="modal-body-confirmacion">
                            <p>
                                ¿Estás seguro de que deseas eliminar el acto <strong>"{acto?.nombre}"</strong>?
                                <br /><br />
                                Esta acción <strong>no se puede deshacer</strong>.
                            </p>
                            <div className="modal-actions-confirmacion">
                                <button
                                    className="btn-cancelar-modal"
                                    onClick={() => setShowConfirmDeleteModal(false)}
                                >
                                    Cancelar
                                </button>
                                <button
                                    className="btn-confirmar-modal"
                                    onClick={handleConfirmEliminar}
                                >
                                    Sí, eliminar
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
                    <div className="dashboard-panel-evento">
                        <div className="historical-header-container-evento">
                            <h1 className="historical-header-title-evento">{acto.nombre}</h1>
                                    {currentUser?.esAdmin && (
                                        <div className="header-tags-container" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '8px' }}>
                                            <div 
                                                className="header-tag-pill-editar" 
                                                onClick={() => navigate(`/admin/editar-acto/${id}`)}
                                                title="Editar este acto"
                                            >
                                                <Edit size={14} />
                                                <span>Editar acto</span>
                                            </div>

                                            <div 
                                                className="header-tag-pill-editar" 
                                                onClick={handleEliminarActo}
                                                title="Eliminar acto"
                                            >
                                                <Trash2 size={14} />
                                                <span>Eliminar acto</span>
                                            </div>

                                            {acto?.requiere_papeleta && acto?.modalidad === 'TRADICIONAL' && (
                                                <>
                                                    <div 
                                                        className="header-tag-pill-editar" 
                                                        onClick={() => navigate(`/admin/crear-puesto`)}
                                                        title="Crear puesto"
                                                    >
                                                        <Plus size={14} />
                                                        <span>Crear puesto</span>
                                                    </div>

                                                    <div className="header-tag-pill-editar" onClick={() => navigate(`/admin/gestion-reparto-insignias/${id}`)} title="Gestión de asignación de insignias">
                                                        <ListOrdered size={14} />
                                                        <span>Asignar insignias</span>
                                                    </div>

                                                    <div className="header-tag-pill-editar" onClick={() => navigate(`/admin/gestion-reparto-cirios/${id}`)} title="Gestión de asignación de cirios y tramos">
                                                        <ListOrdered size={14} />
                                                        <span>Asignar tramos</span>
                                                    </div>

                                                    <div 
                                                        className="header-tag-pill-editar" 
                                                        onClick={() => navigate(`/actos/${id}/asistentes`)}
                                                        title="Ver listado de asistentes"
                                                    >
                                                        <Users size={14} />
                                                        <span>Listado de asistentes</span>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    )}

                                    {/* Fila 2: acciones de hermano */}
                                    {acto?.requiere_papeleta && acto?.modalidad === 'TRADICIONAL' && (
                                        <div className="header-tags-container" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                            <div 
                                                className="header-tag-pill-editar" 
                                                onClick={() => navigate(`/actos/${id}/puestos`)}
                                                title="Listado de puestos"
                                            >
                                                <ListOrdered size={14} />
                                                <span>Listado de puestos</span>
                                            </div>

                                            <div 
                                                className="header-tag-pill-editar" 
                                                onClick={handleSolicitarInsignias}
                                                title="Solicitud de insignias"
                                            >
                                                <ClipboardList size={14} />
                                                <span>Solicitar insignias</span>
                                            </div>

                                            <div 
                                                className="header-tag-pill-editar" 
                                                onClick={handleSolicitarCirios}
                                                title="Solicitud de cirios"
                                            >
                                                <Flame size={14} />
                                                <span>Solicitar cirio</span>
                                            </div>
                                        </div>
                                    )}
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