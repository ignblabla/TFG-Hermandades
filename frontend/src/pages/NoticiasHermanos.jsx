import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; 
import NewsCard from '../components/NewsCard';
import MisAreasCard from '../components/mis_areas_card/MisAreasCard';
import '../styles/ListadoNoticias.css'
import portadaDefecto from '../assets/portada-comunicado.png';
import { Users, Heart, Hammer, Church, Sun, BookOpen, Crown, Landmark, Bell } from "lucide-react";

const getTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    let interval = seconds / 31536000;
    if (interval > 1) return `Hace ${Math.floor(interval)} años`;
    interval = seconds / 2592000;
    if (interval > 1) return `Hace ${Math.floor(interval)} meses`;
    interval = seconds / 86400;
    if (interval > 1) return `Hace ${Math.floor(interval)} días`;
    interval = seconds / 3600;
    if (interval > 1) return `Hace ${Math.floor(interval)} horas`;
    interval = seconds / 60;
    if (interval > 1) return `Hace ${Math.floor(interval)} min`;
    return "Hace unos instantes";
};

const getReadTime = (content) => {
    if (!content) return '1 min lectura';
    const wordsPerMinute = 200;
    const words = content.trim().split(/\s+/).length;
    const time = Math.ceil(words / wordsPerMinute);
    return `${time} min lectura`;
};

function NoticiasHermano() {
    const [isOpen, setIsOpen] = useState(false); 

    const [user, setUser] = useState(null);
    const [noticias, setNoticias] = useState([]); 
    const [loading, setLoading] = useState(true);

    const [currentPage, setCurrentPage] = useState(1);
    const [hasNext, setHasNext] = useState(false);
    const [hasPrevious, setHasPrevious] = useState(false);
    
    const navigate = useNavigate();

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

                const resNoticias = await api.get(`api/comunicados/?page=${currentPage}`);
                
                if (isMounted) {
                    console.log("Datos recibidos de API:", resNoticias.data);

                    const dataList = resNoticias.data.results || resNoticias.data;

                    setHasNext(resNoticias.data.next !== null);
                    setHasPrevious(resNoticias.data.previous !== null);

                    const noticiasFormateadas = dataList.map(item => ({
                        id: item.id,
                        image: item.imagen_portada || portadaDefecto, 
                        time: getTimeAgo(item.fecha_emision),
                        readTime: getReadTime(item.contenido),
                        title: item.titulo,
                        description: item.contenido ? item.contenido.replace(/<[^>]+>/g, '').substring(0, 150) + '...' : '', 
                        author: item.autor_nombre
                    }));

                    setNoticias(noticiasFormateadas);
                }

            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        fetchData();
        return () => { isMounted = false; };
    }, [navigate, user, currentPage]);

    const toggleSidebar = () => setIsOpen(!isOpen);
    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        navigate("/login");
    };

    const irPaginaSiguiente = () => {
        if (hasNext) setCurrentPage(prev => prev + 1);
    };

    const irPaginaAnterior = () => {
        if (hasPrevious) setCurrentPage(prev => prev - 1);
    };

    if (loading && !user) return <div className="site-wrapper loading-screen">Cargando histórico...</div>;

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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                <div className="dashboard-split-layout-solicitud">
                    <div className="dashboard-panel-noticias">
                        <div className="historical-header-container-noticias">
                            <h1 className="historical-header-title-noticias">NOTICIAS</h1>
                        </div>

                        {loading && noticias.length === 0 ? (
                            <div style={{ textAlign: 'center', padding: '3rem', color: '#555' }}>
                                Cargando comunicados...
                            </div>
                        ) : (
                            <>
                                <div className="noticias-grid-4">
                                    {noticias.map((item) => (
                                        <NewsCard 
                                            key={item.id} 
                                            item={item} 
                                        />
                                    ))}
                                </div>

                                {noticias.length > 0 && (
                                    <div className="paginacion-controles">
                                        <button 
                                            className="btn-paginacion" 
                                            onClick={irPaginaAnterior} 
                                            disabled={!hasPrevious}
                                        >
                                            <i className="bx bx-chevron-left"></i> Anterior
                                        </button>
                                        
                                        <span className="paginacion-texto">
                                            Página {currentPage}
                                        </span>

                                        <button 
                                            className="btn-paginacion" 
                                            onClick={irPaginaSiguiente} 
                                            disabled={!hasNext}
                                        >
                                            Siguiente <i className="bx bx-chevron-right"></i>
                                        </button>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </section>

            {/* <section className="home-section-dashboard">
                <div className="text-dashboard">Noticias</div>

                <div style={{ padding: '0 20px 40px 20px', display: 'flex', gap: '30px', alignItems: 'flex-start', flexWrap: 'wrap' }}>

                    <div style={{ flex: '1 1 70%', maxWidth: '100%' }}>
                        {noticias.length === 0 ? (
                            <div style={{ textAlign: 'center', color: '#666', marginTop: '20px' }}>
                                <p>No hay noticias recientes.</p>
                            </div>
                        ) : (
                            <div className="card-container-listado-noticias">
                                {noticias.map(item => (
                                    <NewsCard key={item.id} item={item} />
                                ))}
                            </div>
                        )}
                    </div>

                    <MisAreasCard userAreas={user?.areas_interes} />

                </div>
            </section> */}
        </div>
    );
}

export default NoticiasHermano;