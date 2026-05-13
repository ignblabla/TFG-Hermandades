import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../api';
import '../AdminListadoAsistentesActos/AdminListadoAsistentesActos.css'
import { AlertCircle, CheckCircle, ListTodo, CreditCard, MessageCircle, X, Dock } from "lucide-react";


function ListadoAsistentes() {
    const { actoId } = useParams();
    const navigate = useNavigate();

    const [asistentes, setAsistentes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [isOpen, setIsOpen] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);

    const [accesoDenegado, setAccesoDenegado] = useState(false);

    const [nombreActo, setNombreActo] = useState("");

    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [estadisticas, setEstadisticas] = useState({
        total_papeletas: 0,
        papeletas_leidas: 0,
        papeletas_pendientes: 0
    });

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(prev => prev + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(prev => prev - 1);
    };

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            if (!actoId) {
                if (isMounted) {
                    setError("No se ha proporcionado un ID de acto válido.");
                    setLoading(false);
                }
                return;
            }

            setLoading(true);
            setError("");

            try {
                let userData = currentUser;
                
                if (!userData) {
                    const userRes = await api.get("api/me/");
                    userData = userRes.data;
                    if (isMounted) setCurrentUser(userData);
                }

                if (!userData.esAdmin) {
                    if (isMounted) {
                        setAccesoDenegado(true);
                        setLoading(false);
                    }
                    return;
                }

                const [actoRes, asistentesRes, statsRes] = await Promise.all([
                    api.get(`/api/actos/${actoId}/`),
                    api.get(`/api/actos/${actoId}/asistentes-leidos/?page=${currentPage}`),
                    api.get(`/api/actos/${actoId}/estadisticas-asistencia/`)
                ]);
                
                if (isMounted) {
                    setNombreActo(actoRes.data.nombre);

                    setAsistentes(asistentesRes.data.results); 
                    setTotalPages(Math.ceil(asistentesRes.data.count / 20));

                    setEstadisticas(statsRes.data); 
                }
            } catch (err) {
                if (isMounted) {
                    if (err.response && err.response.status === 403) {
                        setAccesoDenegado(true);
                    } else {
                        setError("Error al obtener los datos de la nómina de asistentes.");
                    }
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        fetchData();

        return () => { isMounted = false; };
    }, [actoId, currentUser, currentPage]);

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
                    <div className="dashboard-panel-asistentes">
                        <div className="historical-header-container-asistentes">
                            <h1 className="historical-header-title-asistentes">ASISTENTES {nombreActo && `- ${nombreActo.toUpperCase()}`}</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Resumen de asistencia</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="asistentes-cards-container">
                            <div className="asistentes-card-wrapper">
                                <div className="asistentes-card-content">
                                    <div className="asistentes-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="asistentes-card-title">PAPELETAS TOTALES</h3>
                                    <p className="asistentes-card-description">
                                        Número total de papeletas de sitio emitidas.
                                    </p>
                                    <div className="asistentes-card-date">
                                        {estadisticas.total_papeletas}
                                    </div>
                                </div>
                            </div>

                            <div className="asistentes-card-wrapper">
                                <div className="asistentes-card-content">
                                    <div className="asistentes-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="asistentes-card-title">PAPELETAS LEÍDAS</h3>
                                    <p className="asistentes-card-description">
                                        Número total de papeletas de sitio que han sido leídas hasta el momento.
                                    </p>
                                    <div className="asistentes-card-date">
                                        {estadisticas.papeletas_leidas}
                                    </div>
                                </div>
                            </div>

                            <div className="asistentes-card-wrapper">
                                <div className="asistentes-card-content">
                                    <div className="asistentes-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="asistentes-card-title">PAPELETAS PENDIENTES</h3>
                                    <p className="asistentes-card-description">
                                        Número total de papeletas que aún no han sido leídas.
                                    </p>
                                    <div className="asistentes-card-date">
                                        {estadisticas.papeletas_pendientes}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Listado de asistentes</span>
                            <div className="plazos-line"></div>
                        </div>

                        <section className="historial-asistentes-section">
                            {asistentes.length > 0 ? (
                                <div className="table-responsive">
                                    <table className="asistentes-table">
                                        <thead>
                                            <tr>
                                                <th className="col-num-reg">Nº Reg.</th>
                                                <th>DNI</th>
                                                <th>Nombre y apellidos</th>
                                                <th>Tramo</th>
                                                <th>Puesto</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {asistentes.map((asistente) => (
                                                <tr key={asistente.id}>
                                                    <td className="fw-bold">
                                                        <span className="badge-reg-censo">
                                                            {asistente.hermano?.numero_registro || '-'}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        {asistente.hermano?.dni || '-'}
                                                    </td>
                                                    <td style={{ fontWeight: 'bold' }}>
                                                        {asistente.hermano?.nombre_completo || 'Desconocido'}
                                                    </td>
                                                    <td>
                                                        {asistente.tramo?.numero_orden ? `${asistente.tramo.numero_orden}º Tramo - ` : ''}
                                                        {asistente.tramo?.nombre || '-'} <br />
                                                        <small className="text-muted">{asistente.tramo?.paso_display || ''}</small>
                                                    </td>
                                                    <td>
                                                        {asistente.puesto?.nombre || 'General'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <AlertCircle size={48} className="empty-icon" />
                                    <p>No se han registrado papeletas leídas para este acto.</p>
                                </div>
                            )}

                            {typeof totalPages !== 'undefined' && totalPages > 1 && (
                                <div className="pagination-controls-asistentes">
                                    <button 
                                        onClick={handlePrevPage} 
                                        disabled={currentPage === 1}
                                        className={currentPage === 1 ? 'disabled' : ''}
                                    >
                                        Anterior
                                    </button>
                                    <span>Página {currentPage} de {totalPages}</span>
                                    <button 
                                        onClick={handleNextPage} 
                                        disabled={currentPage === totalPages}
                                        className={currentPage === totalPages ? 'disabled' : ''}
                                    >
                                        Siguiente
                                    </button>
                                </div>
                            )}
                        </section>

                    </div>
                </div>
            </section>
        </div>
    )

}

export default ListadoAsistentes;