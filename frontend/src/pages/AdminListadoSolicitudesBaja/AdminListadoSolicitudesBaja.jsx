import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import { AlertCircle, CheckCircle, MessageCircle, X, Clock, FileText, XCircle } from "lucide-react";

function AdminListadoSolicitudesBaja() {
    const navigate = useNavigate();
    const [isOpen, setIsOpen] = useState(false);

    const [currentUser, setCurrentUser] = useState(null);
    const [solicitudes, setSolicitudes] = useState([]);

    const [resumen, setResumen] = useState({
        total_pendientes: 0,
        total_aprobadas: 0,
        total_denegadas: 0
    });

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [refresh, setRefresh] = useState(0); 

    const [textoModal, setTextoModal] = useState({ isOpen: false, titulo: '', texto: '' });

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    const renderEstado = (estado) => {
        const estadoClass = {
            'APROBADA': 'success',
            'PENDIENTE': 'warning',
            'DENEGADA': 'error'
        }[estado] || 'neutral';

        const textoLegible = estado ? estado.replace(/_/g, ' ') : estado;
        return <span className={`status-badge ${estadoClass}`}>{textoLegible}</span>;
    };

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            setLoading(true);
            setError("");
            
            try {
                if (!currentUser) {
                    const userRes = await api.get("api/me/");
                    if (isMounted) setCurrentUser(userRes.data);

                    if (userRes.data && !userRes.data.esAdmin) {
                        alert("Acceso denegado. Esta sección es solo para Secretaría/Administradores.");
                        navigate("/");
                        return;
                    }
                }

                const res = await api.get(`api/solicitudes-baja/?page=${currentPage}`);
                
                if (isMounted) {
                    setSolicitudes(res.data.results || res.data);
                    
                    if (res.data.count) {
                        setTotalPages(Math.ceil(res.data.count / 10));
                    }

                    if (res.data.resumen) {
                        setResumen(res.data.resumen);
                    } else {
                        const listado = res.data.results || res.data;
                        setResumen({
                            total_pendientes: listado.filter(s => s.estado === 'PENDIENTE').length,
                            total_aprobadas: listado.filter(s => s.estado === 'APROBADA').length,
                            total_denegadas: listado.filter(s => s.estado === 'DENEGADA').length,
                        });
                    }
                }
            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar las solicitudes. Comprueba tu conexión.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [currentPage, currentUser, navigate, refresh]);

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(prev => prev + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(prev => prev - 1);
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

    const formatDate = (dateString) => {
        if (!dateString) return "-";
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();

        return `${day}-${month}-${year}`;
    };

    const abrirModalTexto = (titulo, texto) => {
        if (!texto) return;
        setTextoModal({ isOpen: true, titulo, texto });
    };

    const handleResolverSolicitud = async (id, accion) => {
        const confirmar = window.confirm(`¿Estás seguro de que deseas ${accion} esta solicitud de baja?`);
        if (!confirmar) return;

        try {
            await api.post(`api/solicitudes-baja/${id}/resolver/`, { accion: accion });
            alert(`Solicitud ${accion.toLowerCase()}a correctamente.`);
            setRefresh(prev => prev + 1);
        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.error || err.response?.data?.detail || "Ocurrió un error al procesar la resolución.";
            alert(`Error: ${msg}`);
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
                    <div className="dashboard-panel-cuotas">
                        
                        <div className="historical-header-container-cuotas">
                            <h1 className="historical-header-title-cuotas">SOLICITUDES DE BAJA</h1>
                        </div>

                        {error && (
                            <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#721c24', backgroundColor: '#f8d7da', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Resumen del estado de peticiones</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="cuotas-cards-container">
                            <div className="cuotas-card-wrapper">
                                <div className="cuotas-card-content">
                                    <div className="cuotas-card-icon" style={{ color: '#ffc107' }}>
                                        <Clock size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="cuotas-card-title">PENDIENTES</h3>
                                    <p className="cuotas-card-description">
                                        Solicitudes que esperan revisión de Secretaría.
                                    </p>
                                    <div className="cuotas-card-date" style={{ color: '#ffc107' }}>
                                        {resumen.total_pendientes}
                                    </div>
                                </div>
                            </div>

                            <div className="cuotas-card-wrapper">
                                <div className="cuotas-card-content">
                                    <div className="cuotas-card-icon" style={{ color: '#28a745' }}>
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="cuotas-card-title">APROBADAS</h3>
                                    <p className="cuotas-card-description">
                                        Bajas tramitadas y hechas efectivas en el censo.
                                    </p>
                                    <div className="cuotas-card-date" style={{ color: '#28a745' }}>
                                        {resumen.total_aprobadas}
                                    </div>
                                </div>
                            </div>

                            <div className="cuotas-card-wrapper">
                                <div className="cuotas-card-content">
                                    <div className="cuotas-card-icon" style={{ color: '#dc3545' }}>
                                        <XCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="cuotas-card-title">DENEGADAS</h3>
                                    <p className="cuotas-card-description">
                                        Solicitudes rechazadas o puestas en pausa.
                                    </p>
                                    <div className="cuotas-card-date" style={{ color: '#dc3545' }}>
                                        {resumen.total_denegadas}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Listado de peticiones</span>
                            <div className="plazos-line"></div>
                        </div>

                        <section className="historial-cuotas-section">
                            {solicitudes.length > 0 ? (
                                <div className="table-responsive">
                                    <table className="cuotas-table">
                                        <thead>
                                            <tr>
                                                <th>Nombre y apellidos</th>
                                                <th>Fecha solicitud</th>
                                                <th>Estado</th>
                                                <th>Fecha resolución</th>
                                                <th>Motivo</th>
                                                <th>Acciones</th></tr> 
                                        </thead>
                                        <tbody>
                                            {solicitudes.map((s) => (
                                                <tr key={s.id}>
                                                    <td className="fw-bold">{s.nombre_completo}</td>
                                                    <td>{formatDate(s.fecha_solicitud)}</td>
                                                    <td>{renderEstado(s.estado)}</td>
                                                    <td>{formatDate(s.fecha_resolucion)}</td>

                                                    <td>
                                                        {s.motivo ? (
                                                            <button 
                                                                className="btn-ver-observacion"
                                                                onClick={() => abrirModalTexto('Motivo de la baja', s.motivo)}
                                                                title="Ver motivo"
                                                                style={{ border: 'none', background: 'none', cursor: 'pointer' }}
                                                            >
                                                                <FileText size={18} />
                                                            </button>
                                                        ) : (
                                                            <span className="text-muted">-</span>
                                                        )}
                                                    </td>
                                                    <td>
                                                        {s.estado === 'PENDIENTE' ? (
                                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                                <button
                                                                    onClick={() => handleResolverSolicitud(s.id, 'ACEPTAR')}
                                                                    title="Aceptar baja"
                                                                    style={{ background: '#28a745', color: '#fff', border: 'none', borderRadius: '4px', padding: '4px 8px', cursor: 'pointer' }}
                                                                >
                                                                    <CheckCircle size={18} />
                                                                </button>
                                                                <button
                                                                    onClick={() => handleResolverSolicitud(s.id, 'DENEGAR')}
                                                                    title="Denegar baja"
                                                                    style={{ background: '#dc3545', color: '#fff', border: 'none', borderRadius: '4px', padding: '4px 8px', cursor: 'pointer' }}
                                                                >
                                                                    <XCircle size={18} />
                                                                </button>
                                                            </div>
                                                        ) : (
                                                            <span style={{ fontSize: '0.85rem', color: '#6c757d' }}>Resuelta</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <AlertCircle size={48} className="empty-icon" />
                                    <p>No se encontraron solicitudes de baja en el sistema.</p>
                                </div>
                            )}

                            {totalPages > 1 && (
                                <div className="pagination-controls-cuotas">
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

            {textoModal.isOpen && (
                <div className="modal-overlay-observacion" onClick={() => setTextoModal({ isOpen: false, titulo: '', texto: '' })}>
                    <div className="modal-content-observacion" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header-observacion">
                            <h3>{textoModal.titulo}</h3>
                            <X 
                                size={24} 
                                style={{ cursor: 'pointer', color: 'var(--text-muted)' }} 
                                onClick={() => setTextoModal({ isOpen: false, titulo: '', texto: '' })} 
                            />
                        </div>
                        <div className="modal-body-observacion">
                            <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{textoModal.texto}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminListadoSolicitudesBaja;