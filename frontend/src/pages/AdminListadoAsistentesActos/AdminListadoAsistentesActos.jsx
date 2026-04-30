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

                const actoRes = await api.get(`/api/actos/${actoId}/`);
                if (isMounted) {
                    setNombreActo(actoRes.data.nombre);
                }

                const response = await api.get(`/api/actos/${actoId}/asistentes-leidos/?page=${currentPage}`);
                
                if (isMounted) {
                    setAsistentes(response.data.results); 

                    setTotalPages(Math.ceil(response.data.count / 20));
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
                                    <h3 className="asistentes-card-title">TOTAL CUOTAS PAGADAS</h3>
                                    <p className="asistentes-card-description">
                                        Número total de cuotas pagadas que constan actualmente en tu historial.
                                    </p>
                                    <div className="asistentes-card-date">
                                        100
                                    </div>
                                </div>
                            </div>

                            <div className="asistentes-card-wrapper">
                                <div className="asistentes-card-content">
                                    <div className="asistentes-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="asistentes-card-title">TOTAL CUOTAS PAGADAS</h3>
                                    <p className="asistentes-card-description">
                                        Número total de cuotas pagadas que constan actualmente en tu historial.
                                    </p>
                                    <div className="asistentes-card-date">
                                        100
                                    </div>
                                </div>
                            </div>

                            <div className="asistentes-card-wrapper">
                                <div className="asistentes-card-content">
                                    <div className="asistentes-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="asistentes-card-title">TOTAL CUOTAS PAGADAS</h3>
                                    <p className="asistentes-card-description">
                                        Número total de cuotas pagadas que constan actualmente en tu historial.
                                    </p>
                                    <div className="asistentes-card-date">
                                        100
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