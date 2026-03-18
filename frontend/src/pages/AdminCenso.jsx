import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'
import '../styles/AdminCenso.css';
import { ChevronLeft, ChevronRight, UserCheck, Users, UserX, AlertCircle } from "lucide-react";

function AdminCenso() {
    const [isOpen, setIsOpen] = useState(false);
    
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

    const [error, setError] = useState("");

    const formatearFecha = (dateString) => {
        if (!dateString) return "-";
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();

        return `${day}-${month}-${year}`;
    };

    useEffect(() => {
        let isMounted = true; 

        const fetchData = async () => {
            setLoading(true);
            try {
                let userData = user;
                if (!userData) {
                    const resUser = await api.get("/api/me/");
                    userData = resUser.data;
                    if (isMounted) setUser(userData);
                }

                if (!userData.esAdmin) {
                    setAccesoDenegado(true);
                    setLoading(false);
                    return;
                }

                const resListado = await api.get(`/api/hermanos/listado/?page=${page}`);
                
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

    const irAlDetalle = (id) => {
        navigate(`/gestion/hermanos/${id}`);
    };

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
                <div className="text-dashboard">Censo de la Hermandad</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    {error && <div className="error-message" style={{ color: 'red', marginBottom: '15px' }}><AlertCircle size={16} /> {error}</div>}
                    <div className="table-responsive-censo">
                        <table className="censo-table">
                            <thead>
                                <tr>
                                    <th className="col-num-reg">Nº Reg.</th>
                                    <th>DNI</th>
                                    <th>Apellidos y Nombre</th>
                                    <th>F. Nacimiento</th>
                                    <th>F. Ingreso</th>
                                    <th>Dirección</th>
                                    <th>Teléfono</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {hermanos.length > 0 ? (
                                    hermanos.map((hermano) => (
                                        <tr key={hermano.id} onClick={() => irAlDetalle(hermano.id)} style={{ cursor: 'pointer' }}>
                                            <td className="col-num-reg">
                                                <span className="badge-reg-censo">{hermano.numero_registro || "-"}</span>
                                            </td>
                                            <td>{hermano.dni}</td>
                                            <td style={{ fontWeight: 'bold' }}>
                                                {hermano.primer_apellido} {hermano.segundo_apellido}, {hermano.nombre}
                                            </td>
                                            <td>{formatearFecha(hermano.fecha_nacimiento)}</td>
                                            <td>{formatearFecha(hermano.fecha_ingreso_corporacion)}</td>
                                            <td title={hermano.direccion}>
                                                {hermano.direccion && hermano.direccion.length > 20 ? hermano.direccion.substring(0, 20) + '...' : hermano.direccion || "-"}
                                            </td>
                                            <td>{hermano.telefono}</td>
                                            <td>
                                                {hermano.estado_hermano === 'ALTA' ? (
                                                    <span className="badge-estado-censo alta"><UserCheck size={14} style={{verticalAlign: 'middle', marginRight: '4px'}}/> Alta</span>
                                                ) : (
                                                    <span className="badge-estado-censo baja"><UserX size={14} style={{verticalAlign: 'middle', marginRight: '4px'}}/> Baja</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="8" style={{ textAlign: 'center', padding: '20px' }}>No se encontraron hermanos.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>  

                    {totalPages > 1 && (
                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', gap: '15px' }}>
                                <button 
                                    onClick={handlePrev} 
                                    disabled={!prevUrl || loading}
                                    className="btn-paginacion-censo cancel"
                                >
                                    <ChevronLeft size={16} style={{verticalAlign: 'middle'}}/> Anterior
                                </button>
                                <span>Página {page} de {totalPages}</span>
                                <button 
                                    onClick={handleNext} 
                                    disabled={!nextUrl || loading}
                                    className="btn-paginacion-censo save"
                                >
                                    Siguiente <ChevronRight size={16} style={{verticalAlign: 'middle'}}/>
                                </button>
                            </div>
                        )}
                </div>
            </section>
        </div>
    );
}

export default AdminCenso;