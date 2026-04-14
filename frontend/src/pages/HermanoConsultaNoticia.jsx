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

        const dia = String(date.getDate()).padStart(2, '0');
        const mes = String(date.getMonth() + 1).padStart(2, '0');
        const anio = date.getFullYear();

        const horas = String(date.getHours()).padStart(2, '0');
        const minutos = String(date.getMinutes()).padStart(2, '0');

        return `${dia}-${mes}-${anio} a las ${horas}:${minutos}`;
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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                {noticia && (
                    <div className="dashboard-split-layout-solicitud">

                        <div className="dashboard-panel-noticias">
                            <div className="historical-header-container-noticias">
                                <h1 className="historical-header-title-noticias">{noticia.titulo}</h1>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Publicada el {formatearFecha(noticia.fecha_emision)}</span>
                                <div className="plazos-line"></div>
                            </div>

                            <div className="noticia-cuerpo-contenedor">
                                <div className="noticia-texto">
                                    {noticia.contenido ? (
                                        noticia.contenido.split('\n').map((parrafo, index) => {
                                            if (parrafo.trim() !== '') {
                                                return (
                                                    <p key={index} className="noticia-parrafo">
                                                        {parrafo}
                                                    </p>
                                                );
                                            }
                                            return null;
                                        })
                                    ) : (
                                        <p className="noticia-parrafo">No hay contenido disponible para este comunicado.</p>
                                    )}
                                </div>
                            </div>

                            <div className="plazos-separator-asignacion">
                                <div className="plazos-line"></div>
                                    <span className="plazos-text">Últimas noticias de tu interés</span>
                                <div className="plazos-line"></div>
                            </div>

                            {ultimasNoticias && ultimasNoticias.length > 0 && (
                                <div className="ultimas-noticias-grid">
                                    {ultimasNoticias.slice(0, 3).map((item) => (
                                        <NewsCard 
                                            key={item.id} 
                                            item={adaptarNoticiaACard(item)} 
                                        />
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="dashboard-panel-imagen-lateral">
                            <img 
                                src={noticia.imagen_portada || "/portada-comunicado.png"} 
                                alt={`Portada de ${noticia.titulo}`} 
                                className="imagen-lateral-noticia"
                            />
                        </div>

                    </div>
                )}
            </section>
        </div>
    );
}

export default HermanoConsultaNoticia;