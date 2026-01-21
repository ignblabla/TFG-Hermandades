import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'
import '../styles/AdminListadoHermanos.css';
import { ArrowLeft, ChevronLeft, ChevronRight, Search, UserCheck, Users } from "lucide-react";

function AdminListadoHermanos() {
    const [isOpen, setIsOpen] = useState(false);
    
    const [error, setError] = useState("");
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [nextUrl, setNextUrl] = useState(null);
    const [prevUrl, setPrevUrl] = useState(null);
    const [accesoDenegado, setAccesoDenegado] = useState(false);

    const navigate = useNavigate();

    const [hermanos, setHermanos] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalRegistros, setTotalRegistros] = useState(0);

    useEffect(() => {
        let isMounted = true; 

        const fetchData = async () => {
            setLoading(true);
            try {
                let userData = user;
                if (!userData) {
                    const resUser = await api.get("api/me/");
                    userData = resUser.data;
                    if (isMounted) setUser(userData);
                }

                console.log("DATOS USUARIO:", userData);
                console.log("ES ADMIN?:", userData?.esAdmin);
                console.log("TIPO DE DATO:", typeof userData?.esAdmin);

                if (!userData.esAdmin) {
                    setAccesoDenegado(true);
                    setLoading(false);
                    return;
                }

                const resListado = await api.get(`api/hermanos/listado/?page=${page}`);
                
                if (isMounted) {
                    setHermanos(resListado.data.results);
                    setTotalRegistros(resListado.data.count);
                    
                    setNextUrl(resListado.data.next);
                    setPrevUrl(resListado.data.previous);
                    
                    const pageSize = 20; 
                    setTotalPages(Math.ceil(resListado.data.count / pageSize));
                }

            } catch (err) {
                console.error("Error:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else {
                    if (isMounted) setError("No se pudo cargar el listado.");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => {
            isMounted = false;
        };
    }, [page, navigate]);

    const toggleSidebar = () => {
        setIsOpen(!isOpen);
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        navigate("/login");
    };

    const handlePrev = () => {
        if (page > 1) setPage(page - 1);
    };

    const handleNext = () => {
        if (page < totalPages) setPage(page + 1);
    };

    if (loading && !user) return <div className="site-wrapper loading-screen">Cargando censo...</div>;

    if (accesoDenegado) {
        return (
            <div className="site-wrapper" style={{textAlign: 'center', marginTop: '50px'}}>
                <h2 style={{color: 'red'}}>🚫 Acceso Restringido</h2>
                <p>Esta sección es exclusiva para la Secretaría.</p>
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
                                <div className="name-dashboard">{user ? `${user.nombre} ${user.primer_apellido}` : "Usuario"}</div>
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
                
                <div className="text-dashboard">Gestión de Usuarios</div>

                <div style={{ padding: '0 20px 40px 20px' }}>
                    
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        <header className="content-header-area">
                            <div className="title-row-area">
                                <div style={{display:'flex', alignItems:'center', gap: '10px'}}>
                                    <Users size={28} className="text-purple" />
                                    <h2>Censo de Hermanos</h2>
                                </div>
                            </div>
                            <p className="description-area">
                                Total registros encontrados: <strong>{totalRegistros}</strong>
                            </p>
                        </header>

                        <div className="table-responsive">
                            {loading ? (
                                <div className="loading-state">Cargando censo...</div>
                            ) : (
                                <table className="hermanos-table">
                                    <thead>
                                        <tr>
                                            <th>Nº Reg.</th>
                                            <th>DNI</th>
                                            <th>Apellidos y Nombre</th>
                                            <th>Teléfono</th>
                                            <th>Estado</th>
                                            <th>Perfil</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {hermanos.length > 0 ? (
                                            hermanos.map((hermano) => (
                                                <tr key={hermano.id}>
                                                    <td><span className="badge-reg">{hermano.numero_registro || "-"}</span></td>
                                                    <td>{hermano.dni}</td>
                                                    <td className="fw-bold">
                                                        {hermano.primer_apellido} {hermano.segundo_apellido}, {hermano.nombre}
                                                    </td>
                                                    <td>{hermano.telefono}</td>
                                                    <td>
                                                        {hermano.estado_hermano === 'ALTA' ? (
                                                            <span className="status-badge success"><UserCheck size={14}/> Alta</span>
                                                        ) : (
                                                            <span className="status-badge error"><UserX size={14}/> Baja</span>
                                                        )}
                                                    </td>
                                                    <td>
                                                        {hermano.esAdmin && <span className="admin-tag">ADMIN</span>}
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="6" className="text-center">No se encontraron hermanos.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            )}
                        </div>

                        <footer className="pagination-footer">
                            <span className="page-info">
                                Página {page} de {totalPages}
                            </span>
                            <div className="pagination-controls">
                                <button 
                                    className="btn-pagination" 
                                    onClick={handlePrev} 
                                    disabled={!prevUrl || loading}
                                >
                                    <ChevronLeft size={16} /> Anterior
                                </button>
                                
                                <button 
                                    className="btn-pagination" 
                                    onClick={handleNext} 
                                    disabled={!nextUrl || loading}
                                >
                                    Siguiente <ChevronRight size={16} />
                                </button>
                            </div>
                        </footer>

                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminListadoHermanos;