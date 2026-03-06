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
    const [tiposActo, setTiposActo] = useState([]);
    
    const [currentUser, setCurrentUser] = useState(null);

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                const user = resUser.data;
                
                if (isMounted) setCurrentUser(user);

                if (!user.esAdmin) {
                    alert("No tienes permisos para crear actos.");
                    navigate("/home");
                    return;
                }

                const resTipos = await api.get("api/tipos-acto/"); 
                if (isMounted) setTiposActo(resTipos.data);

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar configuración inicial.");
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

    const imagenNoticia = "/portada-comunicado.png"

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
                        <h2 className="cultos-section-title">Próximos actos y cultos</h2>
                        <div className="cultos-section-dashboard">
                            <div className="cultos-list">
                                <CultoCard 
                                    mes="MAYO"
                                    dia="15"
                                    titulo="Misa de Hermandad"
                                    hora="20:30h"
                                    lugar="Capilla de la Hermandad"
                                />

                                <CultoCard 
                                    mes="MAYO"
                                    dia="20"
                                    titulo="Triduo a San Gonzalo"
                                    hora="20:00h"
                                    lugar="Parroquia de San Gonzalo"
                                />
                                <CultoCard 
                                    mes="MAYO"
                                    dia="21"
                                    titulo="Triduo a San Gonzalo"
                                    hora="20:00h"
                                    lugar="Parroquia de San Gonzalo"
                                />
                            </div>
                        </div>
                    </div>

                    {/* COLUMNA DERECHA: NOTICIAS */}
                    <div className="new-home-dashboard-news-column">
                        <h2 className="cultos-section-title">Noticias recientes</h2>
                        <div className="new-home-news-grid-container">
                            <NewsCardHome 
                                imagen={imagenNoticia}
                                titulo="Nuevo horario de apertura de la Capilla para la época estival"
                                fecha="10 de Mayo, 2026"
                                contenido="A partir de la próxima semana, la Capilla abrirá sus puertas en horario de tarde desde las 19:00h hasta las 21:30h. Durante las mañanas el horario permanecerá igual."
                                enlace="/noticias/horario-verano"
                            />
                            
                            <NewsCardHome 
                                imagen={imagenNoticia}
                                titulo="Convocatoria de Cabildo General Ordinario"
                                fecha="05 de Mayo, 2026"
                                contenido="Se convoca a todos los hermanos mayores de 18 años y con al menos un año de antigüedad al Cabildo General que tendrá lugar el próximo día 28."
                                enlace="/noticias/cabildo-ordinario"
                            />
                            <NewsCardHome 
                                imagen={imagenNoticia}
                                titulo="Convocatoria de Cabildo General Ordinario"
                                fecha="05 de Mayo, 2026"
                                contenido="Se convoca a todos los hermanos mayores de 18 años y con al menos un año de antigüedad al Cabildo General que tendrá lugar el próximo día 28."
                                enlace="/noticias/cabildo-ordinario"
                            />
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default HermanoNewHome;