import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api'; 
import '../styles/HermanoConsultaNoticia.css';

function HermanoConsultaNoticia() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false); 

    const [user, setUser] = useState(null);
    const [noticia, setNoticia] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const navigate = useNavigate();

    // --- FORMATEADORES ---
    const formatearFecha = (fechaISO) => {
        if (!fechaISO) return '';
        const date = new Date(fechaISO);
        return new Intl.DateTimeFormat('es-ES', {
            day: 'numeric', month: 'long', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        }).format(date);
    };

    // --- EFECTO DE CARGA ---
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
                const resNoticia = await api.get(`api/comunicados/${id}/`);
                
                if (isMounted) {
                    setNoticia(resNoticia.data);
                }
            } catch (err) {
                console.error("Error cargando noticia:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else {
                    setError("No se pudo cargar la noticia.");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        fetchData();
        return () => { isMounted = false; };
    }, [id, navigate, user]);

    // --- HANDLERS ---
    const toggleSidebar = () => setIsOpen(!isOpen);
    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        navigate("/login");
    };


    if (loading && !user) return <div className="site-wrapper loading-screen">Cargando histórico...</div>;

    return (
        <div>
            {/* --- SIDEBAR --- */}
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

            {/* --- SECCIÓN PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Comunicados</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>

                        {error && (
                            <div style={{ padding: 20, textAlign: 'center', color: '#761818' }}>
                                <h3>{error}</h3>
                            </div>
                        )}

                        {!loading && noticia && (
                            <div>
                                {/* --- TÍTULO DE LA NOTICIA (Aquí, dentro del contenedor) --- */}
                                    <h1 className="comunicado-title" style={{ 
                                        fontFamily: "'Playfair Display', serif", 
                                        color: '#761818', 
                                        fontSize: '2.2rem', 
                                        marginBottom: '10px', 
                                        lineHeight: '1.2' 
                                    }}>
                                        {noticia.titulo}
                                    </h1>
                                {/* Cabecera con Imagen */}
                                <header className="comunicado-header">
                                    {noticia.imagen_portada ? (
                                        <img 
                                            src={noticia.imagen_portada} 
                                            alt={noticia.titulo} 
                                            className="comunicado-img"
                                        />
                                    ) : (
                                        <div className="comunicado-img-placeholder">
                                            <span>{noticia.tipo_display}</span>
                                        </div>
                                    )}
                                    
                                    <div className="comunicado-meta-overlay">
                                        <span className={`badge badge-${noticia.tipo_comunicacion ? noticia.tipo_comunicacion.toLowerCase() : 'general'}`}>
                                            {noticia.tipo_display}
                                        </span>
                                        <time dateTime={noticia.fecha_emision}>
                                            {formatearFecha(noticia.fecha_emision)}
                                        </time>
                                    </div>
                                </header>

                                {/* Cuerpo de la Noticia */}
                                <div className="comunicado-body">

                                    {/* Contenido Texto */}
                                    <div className="comunicado-content">
                                        {noticia.contenido.split('\n').map((parrafo, index) => (
                                            parrafo.trim() !== "" && <p key={index}>{parrafo}</p>
                                        ))}
                                    </div>
                                </div>

                                {/* Pie: Etiquetas */}
                                <footer className="comunicado-footer">
                                    <div className="comunicado-info">
                                        <span className="author">Publicado por: <strong>{noticia.autor_nombre}</strong></span>
                                    </div>
                                    {noticia.areas_interes && noticia.areas_interes.length > 0 && (
                                        <div className="tags-container">
                                            <span className="tags-label">Temas:</span>
                                            <div className="tags-list">
                                                {noticia.areas_interes.map((area, idx) => (
                                                    <span key={idx} className="tag-chip">
                                                        {area}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </footer>
                            </div>
                        )}
                    </div>
                </div>
            </section>

        </div>
    );
}

export default HermanoConsultaNoticia;