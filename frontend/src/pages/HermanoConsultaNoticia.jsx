import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api'; 
import '../styles/HermanoConsultaNoticia.css';
import NewsCard from '../components/NewsCard';
import AreasAsociadas from '../components/areas_asociadas/AreasAsociadas';
import { Users, Heart, Hammer, Church, Sun, BookOpen, Crown, Landmark, Bell } from "lucide-react";

function HermanoConsultaNoticia() {
    const { id } = useParams();
    const [isOpen, setIsOpen] = useState(false); 

    const [user, setUser] = useState(null);
    const [noticia, setNoticia] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [ultimasNoticias, setUltimasNoticias] = useState([]);

    const navigate = useNavigate();

    // --- FORMATEADORES ---
    const formatearFecha = (fechaInput) => {
        if (!fechaInput) return '';
        
        let date = new Date(fechaInput);

        if (isNaN(date.getTime()) && typeof fechaInput === 'string' && fechaInput.includes('/')) {
            const partes = fechaInput.split('/');
            if (partes.length === 3) {
                const dia = parseInt(partes[0], 10);
                const mes = parseInt(partes[1], 10) - 1;
                let anio = parseInt(partes[2], 10);

                if (anio < 100) {
                    anio += anio > 50 ? 1900 : 2000;
                }
                date = new Date(anio, mes, dia);
            }
        }

        if (isNaN(date.getTime())) return fechaInput;

        return new Intl.DateTimeFormat('es-ES', {
            day: 'numeric', 
            month: 'long', 
            year: 'numeric'
        }).format(date);
    };

    const adaptarNoticiaACard = (item) => {
        const wordCount = item.contenido ? item.contenido.split(/\s+/).length : 0;
        const readTimeMinutes = Math.max(1, Math.ceil(wordCount / 200));

        const descripcionCorta = item.contenido 
            ? item.contenido.substring(0, 120) + '...'
            : 'Sin descripción disponible.';

        return {
            id: item.id,
            title: item.titulo,
            image: item.imagen_portada || "/portada-comunicado.png",
            time: formatearFecha(item.fecha_emision),
            readTime: `${readTimeMinutes} min lectura`,
            description: descripcionCorta
        };
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

                const [resNoticia, resUltimas] = await Promise.all([
                    api.get(`api/comunicados/${id}/`),
                    api.get(`api/comunicados/${id}/relacionados/`)
                ]);
                
                if (isMounted) {
                    setNoticia(resNoticia.data);
                    setUltimasNoticias(resUltimas.data); 
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
                <div style={{ padding: '0 20px 40px 20px' }}>
                    {error && <p className="error-msg">{error}</p>}
                    
                    {noticia && (
                        <div className="noticia-detalle-container">

                            <header className="noticia-detalle-header">
                                <h1 className="noticia-detalle-titulo">{noticia.titulo}</h1>
                                <p className="noticia-detalle-fecha">
                                    {formatearFecha(noticia.fecha_emision)}
                                </p>
                            </header>
                            
                            <div className="noticia-cuerpo-columnas">
                                <div className="noticia-detalle-texto-layout">
                                    <img 
                                        src={noticia.imagen_portada || "/portada-comunicado.png"} 
                                        alt={`Portada de ${noticia.titulo}`} 
                                        className="noticia-detalle-imagen-flotante"
                                    />

                                    {noticia.contenido.split('\n').map((parrafo, index) => {
                                        if (parrafo.trim() !== '') {
                                            return (
                                                <p key={index} className="noticia-parrafo">
                                                    {parrafo}
                                                </p>
                                            );
                                        }
                                        return null;
                                    })}
                                </div>

                                <AreasAsociadas areas={noticia?.areas_interes} />
                            </div>

                            {ultimasNoticias.length > 0 && (
                                <div className="ultimas-noticias-seccion">
                                    <h2 className="ultimas-noticias-titulo">Últimas noticias de tu interés</h2>
                                    <div className="ultimas-noticias-grid">
                                        {ultimasNoticias.map((item) => (
                                            <NewsCard 
                                                key={item.id} 
                                                item={adaptarNoticiaACard(item)} 
                                            />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}

export default HermanoConsultaNoticia;