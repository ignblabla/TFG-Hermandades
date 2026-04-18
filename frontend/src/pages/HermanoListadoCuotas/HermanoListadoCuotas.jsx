import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../HermanoListadoCuotas/HermanoListadoCuotas.css'
import { AlertCircle, CheckCircle, ListTodo, CreditCard, MessageCircle, X, Dock } from "lucide-react";


function HermanoListadoCuotas() {
    const navigate = useNavigate();
    const [isOpen, setIsOpen] = useState(false);

    const [currentUser, setCurrentUser] = useState(null);
    const [cuotas, setCuotas] = useState([]);

    const [resumen, setResumen] = useState({
        total_cuotas: 0,
        total_pagadas: 0,
        total_pendientes: 0,
        total_pendiente_euros: 0
    });

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [observacionModal, setObservacionModal] = useState({ isOpen: false, texto: '' });

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    const renderEstado = (estado) => {
        const estadoClass = {
            'PAGADA': 'success',
            'PENDIENTE': 'warning',
            'EN_REMESA': 'info',
            'DEVUELTA': 'error',
            'EXENTO': 'purple'
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
                }

                const cuotasRes = await api.get(`api/mis-cuotas/?page=${currentPage}`);
                
                if (isMounted) {
                    setCuotas(cuotasRes.data.results);
                    setTotalPages(Math.ceil(cuotasRes.data.count / 5));

                    if (cuotasRes.data.resumen) {
                        setResumen(cuotasRes.data.resumen);
                    }
                }
            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar las cuotas. Comprueba tu conexión.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [currentPage]);

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(prev => prev + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(prev => prev - 1);
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
                    <div className="dashboard-panel-cuotas">
                        <div className="historical-header-container-cuotas">
                            <h1 className="historical-header-title-cuotas">HISTORIAL DE CUOTAS</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Resumen de tu historial de cuotas</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="cuotas-cards-container">
                            <div className="cuotas-card-wrapper">
                                <div className="cuotas-card-content">
                                    <div className="cuotas-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="cuotas-card-title">TOTAL CUOTAS PAGADAS</h3>
                                    <p className="cuotas-card-description">
                                        Número total de cuotas pagadas que constan actualmente en tu historial.
                                    </p>
                                    <div className="cuotas-card-date">
                                        {resumen.total_pagadas !== undefined && resumen.total_pagadas !== null ? resumen.total_pagadas : '-'}
                                    </div>
                                </div>
                            </div>

                            <div className="cuotas-card-wrapper">
                                <div className="cuotas-card-content">
                                    <div className="cuotas-card-icon">
                                        <AlertCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="cuotas-card-title">TOTAL CUOTAS PENDIENTES</h3>
                                    <p className="cuotas-card-description">
                                        Número total de cuotas pendientes de abonar según tu registro histórico.
                                    </p>
                                    <div className="cuotas-card-date">
                                        {resumen.total_pendientes !== undefined && resumen.total_pendientes !== null ? resumen.total_pendientes : '-'}
                                    </div>
                                </div>
                            </div>

                            <div className="cuotas-card-wrapper">
                                <div className="cuotas-card-content">
                                    <div className="cuotas-card-icon">
                                        <CreditCard size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="cuotas-card-title">TOTAL DEUDA</h3>
                                    <p className="cuotas-card-description">
                                        Importe total acumulado de las cuotas y recibos pendientes de pago.
                                    </p>
                                    <div className="cuotas-card-date">
                                        {resumen.total_pendiente_euros !== undefined && resumen.total_pendiente_euros !== null ? `${Number(resumen.total_pendiente_euros).toFixed(2)} €` : '-'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Historial de cuotas</span>
                            <div className="plazos-line"></div>
                        </div>

                        <section className="historial-cuotas-section">
                            {cuotas.length > 0 ? (
                                <div className="table-responsive">
                                    <table className="cuotas-table">
                                        <thead>
                                            <tr>
                                                <th>Descripción</th>
                                                <th>Tipo</th>
                                                <th>Fecha emisión</th>
                                                <th>Fecha pago</th>
                                                <th>Importe</th>
                                                <th>Estado</th>
                                                <th>Método</th>
                                                <th>Observaciones</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {cuotas.map((c) => (
                                                <tr key={c.id}>
                                                    <td className="fw-bold">{c.descripcion}</td>
                                                    <td>{c.tipo_display || c.tipo}</td>
                                                    <td>{formatDate(c.fecha_emision)}</td>
                                                    <td>{formatDate(c.fecha_pago)}</td>
                                                    <td className="fw-bold">{c.importe} €</td>
                                                    <td>{renderEstado(c.estado)}</td>
                                                    <td>{c.metodo_pago_display || c.metodo_pago}</td>
                                                    <td>
                                                        {c.observaciones ? (
                                                            <button 
                                                                className="btn-ver-observacion"
                                                                onClick={() => setObservacionModal({ isOpen: true, texto: c.observaciones })}
                                                                title="Ver observaciones"
                                                            >
                                                                <MessageCircle size={18} />
                                                            </button>
                                                        ) : (
                                                            <span className="text-muted">-</span>
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
                                    <p>No se encontraron cuotas en tu historial.</p>
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

            {observacionModal.isOpen && (
                <div className="modal-overlay-observacion" onClick={() => setObservacionModal({ isOpen: false, texto: '' })}>
                    <div className="modal-content-observacion" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header-observacion">
                            <h3>Observaciones</h3>
                            <X 
                                size={24} 
                                style={{ cursor: 'pointer', color: 'var(--text-muted)' }} 
                                onClick={() => setObservacionModal({ isOpen: false, texto: '' })} 
                            />
                        </div>
                        <div className="modal-body-observacion">
                            <p>{observacionModal.texto}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default HermanoListadoCuotas;