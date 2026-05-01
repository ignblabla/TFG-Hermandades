import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api'
import '../AdminCenso/AdminCenso.css';
import { ChevronLeft, ChevronRight, UserCheck, Users, UserX, AlertCircle, CheckCircle } from "lucide-react";

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

    const [estadisticas, setEstadisticas] = useState({
        total_alta: 0,
        total_baja: 0,
        ingresos_anio_actual: 0
    });

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
                const resEstadisticas = await api.get("/api/hermanos/estadisticas/");
                
                if (isMounted) {
                    setHermanos(resListado.data.results);
                    setTotalRegistros(resListado.data.count);

                    setEstadisticas(resEstadisticas.data);
                    
                    setNextUrl(resListado.data.next);
                    setPrevUrl(resListado.data.previous);
                    
                    const pageSize = 10; 
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

    const handleVincularTelegram = (e) => {
        e.preventDefault();

        if (user && user.enlace_vinculacion_telegram) {
            window.open(user.enlace_vinculacion_telegram, '_blank');
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
                            onClick={!user?.telegram_chat_id ? handleVincularTelegram : (e) => e.preventDefault()}
                            style={{ 
                                cursor: user?.telegram_chat_id ? 'default' : 'pointer',
                                opacity: user?.telegram_chat_id ? 0.6 : 1
                            }}
                        >
                            <i className="bx bxl-telegram"></i>
                            <span className="link_name-dashboard">
                                {user?.telegram_chat_id ? "Telegram Vinculado ✅" : "Vincular Telegram"}
                            </span>
                        </a>
                        <span className="tooltip-dashboard">
                            {user?.telegram_chat_id ? "Ya vinculado" : "Vincular Telegram"}
                        </span>
                    </li>
                    {user?.esAdmin && (
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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                <div className="dashboard-split-layout-solicitud">
                    <div className="dashboard-panel-censo">
                        <div className="historical-header-container-censo">
                            <h1 className="historical-header-title-censo">CENSO DE LA HERMANDAD</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Datos generales de la Hermandad</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="censo-cards-container">
                            <div className="censo-card-wrapper">
                                <div className="censo-card-content">
                                    <div className="censo-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="censo-card-title">HERMANOS DE ALTA</h3>
                                    <p className="censo-card-description">
                                        Número total de hermanos que se encuentran actualmente activos en la nómina.
                                    </p>
                                    <div className="censo-card-date">
                                        {estadisticas?.total_alta ?? 0}
                                    </div>
                                </div>
                            </div>

                            <div className="censo-card-wrapper">
                                <div className="censo-card-content">
                                    <div className="censo-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="censo-card-title">HERMANOS DE BAJA</h3>
                                    <p className="censo-card-description">
                                        Número total de hermanos que han causado baja en la corporación.
                                    </p>
                                    <div className="censo-card-date">
                                        {estadisticas?.total_baja ?? 0}
                                    </div>
                                </div>
                            </div>

                            <div className="censo-card-wrapper">
                                <div className="censo-card-content">
                                    <div className="censo-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="censo-card-title">NUEVOS INGRESOS</h3>
                                    <p className="censo-card-description">
                                        Número de hermanos admitidos durante el año natural en curso.
                                    </p>
                                    <div className="censo-card-date">
                                        {estadisticas?.ingresos_anio_actual ?? 0}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Listado histórico de Hermanos</span>
                            <div className="plazos-line"></div>
                        </div>

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
                                                    {hermano.direccion && hermano.direccion.length > 20 
                                                        ? hermano.direccion.substring(0, 20) + '...' 
                                                        : hermano.direccion || "-"}
                                                </td>
                                                <td>{hermano.telefono}</td>
                                                <td>
                                                    {hermano.estado_hermano === 'ALTA' ? (
                                                        <span className="badge-estado-censo alta">
                                                            <UserCheck size={14} style={{verticalAlign: 'middle', marginRight: '4px'}}/> Alta
                                                        </span>
                                                    ) : (
                                                        <span className="badge-estado-censo baja">
                                                            <UserX size={14} style={{verticalAlign: 'middle', marginRight: '4px'}}/> Baja
                                                        </span>
                                                    )}
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="8" style={{ textAlign: 'center', padding: '20px' }}>
                                                No se encontraron hermanos.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {totalPages > 1 && (
                            <div className="pagination-controls-cuotas">
                                <button 
                                    onClick={handlePrev} 
                                    disabled={page === 1}
                                    className={page === 1 ? 'disabled' : ''}
                                >
                                    Anterior
                                </button>
                                <span>Página {page} de {totalPages}</span>
                                <button 
                                    onClick={handleNext} 
                                    disabled={page === totalPages}
                                    className={page === totalPages ? 'disabled' : ''}
                                >
                                    Siguiente
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminCenso;