import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
// import '../styles/AdminCreacionActo.css';
import '../styles/HomeCard.css';
import '../styles/HermanoNewHome.css'
import HomeCard from '../components/HomeCard';
import CultoCard from '../components/CultoCard';
import ProfileCard from '../components/ProfileCard';
import ContadorCard from '../components/ContadorCard';
import NewsCard from '../components/NewsCard';
import ChatBot from '../components/chatbot/chatbot';
import { Medal, CreditCard, Bookmark, ListOrdered, ScrollText, Ticket, Map } from "lucide-react";

function HermanoNewHome() {
    const navigate = useNavigate();

    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [successMsg, setSuccessMsg] = useState("");
    const [error, setError] = useState("");

    const [currentUser, setCurrentUser] = useState(null);
    const [proximosActos, setProximosActos] = useState([]);

    const [ultimosComunicados, setUltimosComunicados] = useState([]);

    const areaInfoEstatica = {
        'TODOS_HERMANOS': { title: 'Todos los Hermanos' },
        'COSTALEROS': { title: 'Costaleros' },
        'CARIDAD': { title: 'Diputación de Caridad' },
        'JUVENTUD': { title: 'Juventud' },
        'PRIOSTIA': { title: 'Priostía' },
        'CULTOS_FORMACION': { title: 'Cultos y Formación' },
        'PATRIMONIO': { title: 'Patrimonio' },
        'ACOLITOS': { title: 'Acólitos' },
        'DIPUTACION_MAYOR_GOBIERNO': { title: 'Diputación Mayor de Gobierno' },
    };

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

    const adaptarNoticiaACard = (item) => {
        let categoryName = "General";
        let categoryColor = "#800020";

        if (item.areas_interes && item.areas_interes.length > 0) {
            const firstArea = item.areas_interes[0];
            const areaKey = typeof firstArea === 'object' ? (firstArea.nombre_area || firstArea.nombre) : firstArea;
            
            let visualInfo = areaInfoEstatica[areaKey];
            if (!visualInfo) {
                const foundKey = Object.keys(areaInfoEstatica).find(key => areaInfoEstatica[key].title === areaKey);
                if (foundKey) visualInfo = areaInfoEstatica[foundKey];
            }

            if (visualInfo) {
                categoryName = visualInfo.title;
                if (visualInfo.color) categoryColor = visualInfo.color;
            } else {
                categoryName = areaKey;
            }
        }

        const wordCount = item.contenido ? item.contenido.split(/\s+/).length : 0;
        const readTimeMinutes = Math.max(1, Math.ceil(wordCount / 200));

        const descripcionCorta = item.contenido 
            ? item.contenido.substring(0, 120) + '...'
            : 'Sin descripción disponible.';

        return {
            id: item.id,
            title: item.titulo,
            image: item.imagen_portada || imagenFallback,
            category: categoryName,
            categoryColor: categoryColor,
            time: formatearFechaNoticia(item.fecha_emision),
            readTime: `${readTimeMinutes} min lectura`,
            description: descripcionCorta
        };
    };

    const imagenFallback = "/portada-comunicado.png";

    const formatearFechaNoticia = (fechaString) => {
        const opciones = { day: 'numeric', month: 'long', year: 'numeric' };
        return new Date(fechaString).toLocaleDateString('es-ES', opciones);
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

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Panel del Hermano</div>

                <div className="profile-card-wrapper" style={{ margin: '0 20px 12px 20px' }}>
                    <ProfileCard hermano={currentUser || {}} />
                </div>
                
                <div className="home-cards-container">
                    <HomeCard 
                        icon={ListOrdered}
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
                        value={currentUser?.areas_interes?.length || 1} 
                    />
                </div>

                <div className="new-home-dashboard-bottom-section">
                    <div className="new-home-dashboard-cultos-column">
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
                    </div>

                    {/* 2. COLUMNA DERECHA: PAPELETA */}
                    <div className="new-home-dashboard-profile-column">
                        <h2 className="cultos-section-title">Estación de penitencia</h2>
                        <ContadorCard />
                    </div>

                    {/* 3. NUEVA FILA: NOTICIAS (Fuera de la columna de eventos) */}
                    <div className="new-home-dashboard-news-column">
                        <h2 className="cultos-section-title">Últimas noticias</h2>
                        <div className="new-home-news-horizontal-container">
                            {ultimosComunicados && ultimosComunicados.length > 0 ? (
                                ultimosComunicados.map((comunicado) => (
                                    <NewsCard 
                                        key={comunicado.id} 
                                        item={adaptarNoticiaACard(comunicado)} 
                                    />
                                ))
                            ) : (
                                <p style={{ color: '#666', fontStyle: 'italic' }}>
                                    No hay comunicados recientes para mostrar.
                                </p>
                            )}
                        </div>
                    </div>

                    <div className="new-home-dashboard-extra-column">
                        <h2 className="cultos-section-title">Papeleta de sitio</h2>
                        <div className="extra-rectangles-wrapper">

                            <div 
                                className="independent-rectangle" 
                                onClick={() => navigate('/solicitud-insignias')}
                                style={{ cursor: 'pointer' }}
                            >
                                <div className="independent-rectangle-content-wrapper">
                                    <Ticket size={90} color="#800020" className="independent-rectangle-icon rotate-icon-vertical" />
                                    
                                    <div className="independent-rectangle-text-content">
                                        <h3 className="independent-rectangle-title">
                                            SOLICITUD DE PAPELETA <br /> DE SITIO
                                        </h3>
                                        <p className="independent-rectangle-description">
                                            Formulario para solicitar su lugar de la cofradía en la Estación de Penitencia.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="independent-rectangle">
                                <div className="independent-rectangle-content-wrapper">
                                    <ScrollText size={90} color="#800020" className="independent-rectangle-icon" />
                                    
                                    <div className="independent-rectangle-text-content">
                                        <h3 className="independent-rectangle-title">
                                            REGLAS DE LA ESTACIÓN <br /> DE PENITENCIA
                                        </h3>
                                        <p className="independent-rectangle-description">
                                            Normas y directrices para la correcta participación en la Estación de penitencia.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="independent-rectangle">
                                <div className="independent-rectangle-content-wrapper">
                                    <Map size={90} color="#800020" className="independent-rectangle-icon" />
                                    
                                    <div className="independent-rectangle-text-content">
                                        <h3 className="independent-rectangle-title">
                                            HORARIO E ITINERARIO DE LA <br /> ESTACIÓN DE PENITENCIA
                                        </h3>
                                        <p className="independent-rectangle-description">
                                            Información detallada sobre el recorrido, calles y horarios de la Estación de Penitencia.
                                        </p>
                                    </div>
                                </div>
                            </div>
                            
                        </div>
                    </div>
                </div>
            </section>

            <ChatBot />
        </div>
    );
}

export default HermanoNewHome;