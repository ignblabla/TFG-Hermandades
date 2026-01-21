import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'
import '../styles/AdminListadoHermanos.css';
import { ArrowLeft, ChevronLeft, ChevronRight, Search, UserCheck, UserX } from "lucide-react";

function AdminListadoHermanos() {
    const [isOpen, setIsOpen] = useState(false);
    
    const [error, setError] = useState("");
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const navigate = useNavigate();

    const [hermanos, setHermanos] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalRegistros, setTotalRegistros] = useState(0);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                let userData = user;
                if (!userData) {
                    const resUser = await api.get("api/me/");
                    userData = resUser.data;
                    setUser(userData);
                }

                if (!userData.esAdmin) {
                    alert("Acceso denegado. Solo administradores.");
                    navigate("/home");
                    return;
                }

                const resListado = await api.get(`api/hermanos/listado/?page=${page}`);
                
                setHermanos(resListado.data.results);
                setTotalRegistros(resListado.data.count);
                
                const pageSize = 20; 
                setTotalPages(Math.ceil(resListado.data.count / pageSize));

            } catch (err) {
                console.error("Error cargando listado:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else {
                    setError("No se pudo cargar el listado de hermanos.");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchData();
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

    const handlePrevPage = () => {
        if (page > 1) setPage(page - 1);
    };

    const handleNextPage = () => {
        if (page < totalPages) setPage(page + 1);
    };

    if (loading && !user) return <div className="site-wrapper loading-screen">Cargando censo...</div>;

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
                <div className="text-dashboard">Panel de administración</div>
                <div style={{padding: '0 18px'}}>
                    <p>Bienvenido al panel de control, {user.nombre || "Administrador"}.</p>
                </div>
                <main className="main-container-area">
                    <div className="card-container-listado"> {/* Clase CSS específica para tabla ancha */}
                        
                        <header className="content-header-area">
                            <div className="title-row-area">
                                <h1>Censo de Hermanos</h1>
                                <button className="btn-back-area" onClick={() => navigate(-1)}>
                                    <ArrowLeft size={16} /> Volver
                                </button>
                            </div>
                            <p className="description-area">
                                Listado general de la nómina de hermanos. Total registros: <strong>{totalRegistros}</strong>.
                            </p>
                        </header>

                        {error && <div className="error-banner">{error}</div>}

                        {/* --- TABLA DE DATOS --- */}
                        <div className="table-responsive">
                            <table className="hermanos-table">
                                <thead>
                                    <tr>
                                        <th>Nº Reg.</th>
                                        <th>DNI</th>
                                        <th>Apellidos</th>
                                        <th>Nombre</th>
                                        <th>Teléfono</th>
                                        <th>Estado</th>
                                        <th>Rol</th>
                                        <th style={{textAlign: 'center'}}>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {hermanos.length > 0 ? (
                                        hermanos.map((hermano) => (
                                            <tr key={hermano.id}>
                                                <td className="fw-bold">#{hermano.numero_registro || "-"}</td>
                                                <td>{hermano.dni}</td>
                                                <td>{hermano.primer_apellido} {hermano.segundo_apellido}</td>
                                                <td>{hermano.nombre}</td>
                                                <td>{hermano.telefono}</td>
                                                <td>
                                                    <span className={`badge status-${hermano.estado_hermano?.toLowerCase()}`}>
                                                        {hermano.estado_hermano}
                                                    </span>
                                                </td>
                                                <td>
                                                    {hermano.esAdmin ? (
                                                        <span className="badge badge-admin" title="Administrador">Admin</span>
                                                    ) : (
                                                        <span className="text-muted">-</span>
                                                    )}
                                                </td>
                                                <td style={{textAlign: 'center'}}>
                                                    <button 
                                                        className="btn-icon-action" 
                                                        title="Ver detalle"
                                                        onClick={() => navigate(`/hermanos/${hermano.id}`)}
                                                    >
                                                        <Search size={18} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="8" className="text-center">No se encontraron hermanos.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* --- PAGINACIÓN --- */}
                        <div className="pagination-container">
                            <span className="pagination-info">
                                Página <strong>{page}</strong> de <strong>{totalPages}</strong>
                            </span>
                            
                            <div className="pagination-controls">
                                <button 
                                    className="btn-pagination" 
                                    onClick={handlePrevPage} 
                                    disabled={page === 1}
                                >
                                    <ChevronLeft size={20} /> Anterior
                                </button>

                                <button 
                                    className="btn-pagination" 
                                    onClick={handleNextPage} 
                                    disabled={page === totalPages}
                                >
                                    Siguiente <ChevronRight size={20} />
                                </button>
                            </div>
                        </div>

                    </div>
                </main>
            </section>
        </div>
    );
}

export default AdminListadoHermanos;