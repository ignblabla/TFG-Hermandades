import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../AdminListadoSolicitudesInsigniasActoConcreto/AdminListadoSolicitudesInsigniasActoConcreto.css';

function AdminListadoSolicitudesInsigniasActoConcreto() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false);
    
    const [currentUser, setCurrentUser] = useState(null);
    const [acto, setActo] = useState(null);
    const [solicitudes, setSolicitudes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [accesoDenegado, setAccesoDenegado] = useState(false);
    const [error, setError] = useState("");

    // ESTADOS PARA LA PAGINACIÓN
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const itemsPerPage = 20;

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

                const resSolicitudes = await api.get(`/api/actos/${id}/solicitudes-insignias/`);
                if (isMounted) {
                    const data = resSolicitudes.data;
                    setSolicitudes(data);
                    setTotalPages(Math.ceil(data.length / itemsPerPage));
                }

            } catch (err) {
                console.error("Error:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else {
                    if (isMounted) setError("No se pudo cargar la información.");
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

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setCurrentUser(null);
        navigate("/login");
    };

    // FUNCIONES DE PAGINACIÓN
    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(prev => prev + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(prev => prev - 1);
    };

    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentItems = solicitudes.slice(indexOfFirstItem, indexOfLastItem);

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

    return (
        <div>
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} id="btn" onClick={toggleSidebar}></i>
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
                        <i className="bx bx-log-out" id="log_out" onClick={handleLogout} style={{cursor: 'pointer'}}></i>
                    </li>
                </ul>
            </div>

            <section className="home-section-dashboard">
                <div className="text-dashboard" style={{ marginTop: '20px', marginBottom: '8px' }}>
                    Listado de solicitudes de insignias - {acto?.nombre}
                </div>

                <div style={{ padding: '10px 20px 12px 20px' }}>
                    {error && <div className="error-message" style={{ color: 'red', marginBottom: '15px' }}>{error}</div>}

                    <div className="insignias-table-responsive">
                        {solicitudes.length === 0 ? (
                            <p style={{ textAlign: 'center', padding: '20px' }}>No hay solicitudes de insignias registradas para este acto.</p>
                        ) : (
                            <table className="insignias-table">
                                <thead>
                                    <tr>
                                        <th>DNI</th>
                                        <th>Estado</th>
                                        <th>Fecha Solicitud</th>
                                        <th>Acto</th>
                                        <th>Orden</th>
                                        <th>Puesto Solicitado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {currentItems.map((solicitud, index) => {
                                        const estadoClase = solicitud.estado?.toLowerCase().replace(' ', '-');
                                        const estaEmitida = solicitud.estado === "Emitida" || solicitud.estado === "Recogida" || solicitud.estado === "Leída";

                                        // LÓGICA DE SEPARACIÓN DE COLUMNAS
                                        let orden = "-";
                                        let puesto = solicitud.preferencia;

                                        if (solicitud.preferencia && solicitud.preferencia.includes(" - ")) {
                                            const partes = solicitud.preferencia.split(" - ");
                                            orden = partes[0]; // Ej: "1º"
                                            // En caso de que el nombre del puesto también tenga un guion, volvemos a unir el resto
                                            puesto = partes.slice(1).join(" - "); 
                                        }

                                        return (
                                            <tr key={index}>
                                                <td>{solicitud.dni}</td>
                                                <td>
                                                    <span className={`badge-estado-insignia ${estadoClase}`}>
                                                        {solicitud.estado}
                                                    </span>
                                                </td>
                                                <td>{solicitud.fecha_solicitud || '-'}</td>
                                                <td>{solicitud.acto}</td>
                                                <td>{orden}</td>
                                                <td>
                                                    {estaEmitida ? (
                                                        <strong>{puesto}</strong>
                                                    ) : (
                                                        puesto
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        )}
                    </div>

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
        </div>
    );
}

export default AdminListadoSolicitudesInsigniasActoConcreto;