import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import '../styles/HermanoListadoCuotas.css'
import { AlertCircle, CheckCircle, ListTodo, CreditCard, MessageCircle, X } from "lucide-react";
import HomeCard from '../components/HomeCard';


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
                    setTotalPages(Math.ceil(cuotasRes.data.count / 10));

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

            <section className="home-section-dashboard">
                <div className="text-dashboard">Resumen de cuotas</div>
                <div className="home-cards-container">
                    <HomeCard 
                        title="Total Cuotas" 
                        value={resumen.total_cuotas} 
                        icon={ListTodo} 
                    />
                    <HomeCard 
                        title="Cuotas Pagadas" 
                        value={resumen.total_pagadas} 
                        icon={CheckCircle} 
                    />
                    <HomeCard 
                        title="Cuotas Pendientes" 
                        value={resumen.total_pendientes} 
                        icon={AlertCircle} 
                    />
                    <HomeCard 
                        title="Total Deuda" 
                        value={`${Number(resumen.total_pendiente_euros).toFixed(2)} €`} 
                        icon={CreditCard} 
                    />
                </div>

                <div className="text-dashboard" style={{ marginTop: '20px', marginBottom: '8px', fontSize: '1.5rem' }}>
                    Histórico de movimientos
                </div>

                <div style={{ padding: '10px 20px 12px 20px' }}>
                    {error && <div className="error-message" style={{ color: 'red', marginBottom: '15px' }}><AlertCircle size={16} /> {error}</div>}

                    <div className="table-responsive">
                        <table className="cuotas-table">
                            <thead>
                                <tr>
                                    <th>Año</th>
                                    <th>Tipo</th>
                                    <th>Descripción</th>
                                    <th>Fecha de emisión</th>
                                    <th>Fecha de pago</th>
                                    <th>Importe</th>
                                    <th>Estado</th>
                                    <th>Método de pago</th>
                                    <th>Observaciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {cuotas.length > 0 ? (
                                    cuotas.map((cuota) => (
                                        <tr key={cuota.id}>
                                            <td>{cuota.anio}</td>
                                            <td>{cuota.tipo}</td>
                                            <td>{cuota.descripcion}</td>
                                            <td>{formatDate(cuota.fechaEmision || cuota.fecha_emision)}</td>
                                            <td>{formatDate(cuota.fechaPago || cuota.fecha_pago)}</td>
                                            <td>{cuota.importe}</td>
                                            <td>
                                                <span className={`badge-estado ${cuota.estado?.toLowerCase() || 'pendiente'}`}>
                                                    {cuota.estado || 'Pendiente'}
                                                </span>
                                            </td>
                                            <td>{cuota.metodoPago || cuota.metodo_pago}</td>
                                            <td style={{ color: !cuota.observaciones?.trim() ? '#9ca3af' : 'inherit', fontStyle: !cuota.observaciones?.trim() ? 'italic' : 'normal', textAlign: 'center' }}>
                                                {cuota.observaciones?.trim() ? (
                                                    <MessageCircle 
                                                        className="icon-observacion"
                                                        size={22} 
                                                        onClick={() => setObservacionModal({ isOpen: true, texto: cuota.observaciones })}
                                                        style={{ cursor: 'pointer', color: 'var(--burgundy-primary)' }}
                                                    />
                                                ) : (
                                                    "Sin observaciones"
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="9" style={{ textAlign: 'center', padding: '20px' }}>
                                            No se encontraron cuotas registradas.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Controles de Paginación */}
                    {totalPages > 1 && (
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', gap: '15px' }}>
                            <button 
                                onClick={handlePrevPage} 
                                disabled={currentPage === 1}
                                className="btn-cancel-crear-acto"
                            >
                                Anterior
                            </button>
                            <span>Página {currentPage} de {totalPages}</span>
                            <button 
                                onClick={handleNextPage} 
                                disabled={currentPage === totalPages}
                                className="btn-save-crear-acto"
                            >
                                Siguiente
                            </button>
                        </div>
                    )}
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