import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; 
import NewsCard from '../components/NewsCard';

const getCategoryColor = (tipo) => {
    const colors = {
        'GENERAL': '#5e5ce6',
        'INFORMATIVO': '#3498db',
        'CULTOS': '#9b59b6',
        'SECRETARIA': '#f1c40f',
        'URGENTE': '#e74c3c',
        'EVENTOS': '#27a070',
    };
    return colors[tipo] || '#95a5a6';
};

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
    if (!content) return '1 min read';
    const wordsPerMinute = 200;
    const words = content.trim().split(/\s+/).length;
    const time = Math.ceil(words / wordsPerMinute);
    return `${time} min read`;
};

// --- FIN FUNCIONES AUXILIARES ---

function NoticiasHermano() {
    const [isOpen, setIsOpen] = useState(false); 
    
    // Estados de datos
    const [user, setUser] = useState(null);
    const [noticias, setNoticias] = useState([]); 
    const [loading, setLoading] = useState(true);
    
    const navigate = useNavigate();

    // --- EFECTO DE CARGA ---
    useEffect(() => {
        let isMounted = true; 
        const fetchData = async () => {
            setLoading(true);
            try {
                // 1. Cargar Usuario
                let userData = user;
                if (!userData) {
                    const resUser = await api.get("api/me/");
                    userData = resUser.data;
                    if (isMounted) setUser(userData);
                }

                const resNoticias = await api.get("api/comunicados/");
                
                if (isMounted) {
                    console.log("Datos recibidos de API:", resNoticias.data);

                    const noticiasFormateadas = resNoticias.data.map(item => ({
                        id: item.id,
                        category: item.tipo_display || item.tipo_comunicacion, 
                        categoryColor: getCategoryColor(item.tipo_comunicacion),
                        image: item.imagen_portada || 'https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?auto=format&fit=crop&q=80&w=500', 
                        time: getTimeAgo(item.fecha_emision),
                        readTime: getReadTime(item.contenido),
                        title: item.titulo,
                        description: item.contenido ? item.contenido.replace(/<[^>]+>/g, '').substring(0, 100) + '...' : '', 
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
    }, [navigate, user]); 

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

            <section className="home-section-dashboard">
                <div className="text-dashboard">Noticias y Comunicados</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    {noticias.length === 0 ? (
                        <div style={{ textAlign: 'center', color: '#666', marginTop: '20px' }}>
                            <p>No hay noticias recientes.</p>
                        </div>
                    ) : (
                        <div className="card-container-listado-noticias" style={{ margin: '0', maxWidth: '100%' }}>
                            {noticias.map(item => (
                                <NewsCard key={item.id} item={item} />
                            ))}
                        </div>
                    )}

                </div>
            </section>
        </div>
    );
}

export default NoticiasHermano;