import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
// import '../styles/AdminCreacionActo.css';
import '../styles/HomeCard.css';
import '../styles/HermanoNewHome.css'
import HomeCard from '../components/HomeCard';
import CultoCard from '../components/CultoCard';
import NewsCardHome from '../components/NewsCardHome';
import { User, Medal, CreditCard, Church, Bookmark } from "lucide-react";

function HermanoNewHome() {
    const navigate = useNavigate();

    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [successMsg, setSuccessMsg] = useState("");
    const [error, setError] = useState("");

    const [currentUser, setCurrentUser] = useState(null);
    const [proximosActos, setProximosActos] = useState([]);

    const [ultimosComunicados, setUltimosComunicados] = useState([]);

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                if (isMounted) setCurrentUser(resUser.data);

                const resProximos = await api.get("api/actos/proximos/");
                if (isMounted) setProximosActos(resProximos.data);

            } catch (err) {
                console.error("Error al cargar configuración inicial:", err);
                if (isMounted) setError("Error al cargar configuración inicial.");

                if (err.response && err.response.status === 401) {
                    navigate("/login");
                }
            } 

            try {
                const resNoticia = await api.get("api/comunicados/ultimos-area-interes/");
                if (isMounted) setUltimosComunicados(resNoticia.data);
            } catch (err) {
                if (err.response && err.response.status === 404) {
                    if (isMounted) setUltimoComunicado(null);
                } else {
                    console.error("Error al cargar la última noticia:", err);
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [navigate]);

    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    const imagenFallback = "/portada-comunicado.png";

    const formatearFechaNoticia = (fechaString) => {
        const opciones = { day: 'numeric', month: 'long', year: 'numeric' };
        return new Date(fechaString).toLocaleDateString('es-ES', opciones);
    };

    if (loading) return <div className="loading-screen">Cargando configuración...</div>;

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

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Panel del Hermano</div>
                
                <div className="home-cards-container">
                    <HomeCard 
                        icon={User}
                        title="Número de registro" 
                        value={currentUser?.numero_registro || "-"}
                    />

                    <HomeCard
                        icon={Medal}
                        title="Años de antigüedad" 
                        value={currentUser?.antiguedad_anios ?? "-"} 
                    />
                    
                    <HomeCard
                        icon={CreditCard}
                        title="Cuotas Pendientes" 
                        value={
                            currentUser?.historial_cuotas
                                ? currentUser.historial_cuotas.filter(
                                    (cuota) => cuota.estado === 'PENDIENTE' || cuota.estado === 'DEVUELTA'
                                ).length
                                : 0
                        } 
                    />

                    <HomeCard
                        icon={Bookmark}
                        title="Áreas de interés" 
                        value={currentUser?.areas_interes?.length ?? 0} 
                    />
                </div>

                <div className="new-home-dashboard-bottom-section">
                    <div className="new-home-dashboard-cultos-column">
                        
                        {/* 1. SECCIÓN DE EVENTOS */}
                        <h2 className="cultos-section-title">Próximos eventos</h2>
                        <div className="cultos-section-dashboard">
                            <div className="cultos-list">
                                {proximosActos.length > 0 ? (
                                    proximosActos.map((acto) => {
                                        const fechaObj = new Date(acto.fecha);
                                        const mesStr = fechaObj.toLocaleString('es-ES', { month: 'short' }).toUpperCase().replace('.', '');
                                        const diaStr = fechaObj.getDate().toString();
                                        const horaStr = fechaObj.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) + 'h';

                                        return (
                                            <CultoCard 
                                                key={acto.id}
                                                mes={mesStr}
                                                dia={diaStr}
                                                titulo={acto.nombre}
                                                hora={horaStr}
                                                lugar={acto.lugar || "Lugar por determinar"}
                                            />
                                        );
                                    })
                                ) : (
                                    <p style={{ color: '#666', fontStyle: 'italic' }}>
                                        No hay actos próximos programados en este momento.
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* 2. SECCIÓN DE NOTICIAS MOVIDA AQUÍ */}
                        <h2 className="cultos-section-title" style={{ marginTop: '30px', marginBottom: '15px' }}>Últimas noticias</h2>
                        <div className="new-home-news-horizontal-container">
                            {ultimosComunicados && ultimosComunicados.length > 0 ? (
                                ultimosComunicados.map((comunicado) => (
                                    <NewsCardHome 
                                        key={comunicado.id}
                                        imagen={comunicado.imagen_portada || imagenFallback}
                                        titulo={comunicado.titulo}
                                        fecha={formatearFechaNoticia(comunicado.fecha_emision)}
                                        contenido={comunicado.contenido}
                                        enlace={`/comunicados/${comunicado.id}`}
                                    />
                                ))
                            ) : (
                                <p style={{ color: '#666', fontStyle: 'italic' }}>
                                    No hay comunicados recientes para mostrar.
                                </p>
                            )}
                        </div>

                        {/* 3. PAPELETAS DE SITIO */}
                        <h2 className="cultos-section-title" style={{ marginTop: '25px' }}>Papeletas de sitio</h2>
                    </div>

                    {/* COLUMNA DERECHA: NOTICIAS */}
                    <div className="new-home-dashboard-profile-column">
                        <h2 className="cultos-section-title">Perfil del Hermano</h2>
                        
                    </div>
                </div>
            </section>
        </div>
    );
}

export default HermanoNewHome;