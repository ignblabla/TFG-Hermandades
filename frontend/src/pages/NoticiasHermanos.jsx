import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; 
import NewsCard from '../components/NewsCard';

function NoticiasHermano() {
    const [isOpen, setIsOpen] = useState(false); 
    
    // Estados de datos
    const [user, setUser] = useState(null);
    const [papeletas, setPapeletas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [downloadingId, setDownloadingId] = useState(null);
    
    // Estados de paginación
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalRegistros, setTotalRegistros] = useState(0);
    const [nextUrl, setNextUrl] = useState(null);
    const [prevUrl, setPrevUrl] = useState(null);

    const navigate = useNavigate();

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

                const resListado = await api.get(`api/papeletas/mis-papeletas/?page=${page}`);
                
                if (isMounted) {
                    setPapeletas(resListado.data.results);
                    setTotalRegistros(resListado.data.count);
                    setNextUrl(resListado.data.next);
                    setPrevUrl(resListado.data.previous);
                    const pageSize = 20; 
                    setTotalPages(Math.ceil(resListado.data.count / pageSize));
                }
            } catch (err) {
                console.error("Error cargando papeletas:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        fetchData();
        return () => { isMounted = false; };
    }, [page, navigate]);

    const toggleSidebar = () => setIsOpen(!isOpen);
    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        navigate("/login");
    };

    const newsData = [
        {
            id: 1,
            category: 'TECHNOLOGY',
            categoryColor: '#5e5ce6',
            image: 'https://images.unsplash.com/photo-1639322537228-f710d846310a?auto=format&fit=crop&q=80&w=500',
            time: '45 min ago',
            readTime: '4 min read',
            title: 'AI Regulations Proposed by EU Commission',
            description: 'The new framework aims to categorize AI systems based on risk levels, imposing stricter compliance...',
            author: 'David Miller'
        },
        {
            id: 2,
            category: 'POLITICS',
            categoryColor: '#eb4432',
            image: 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&q=80&w=500',
            time: '3 hours ago',
            readTime: '6 min read',
            title: 'Senate Vote Scheduled for New Infrastructure Bill',
            description: 'After weeks of deliberation, the Senate leadership has agreed to bring the comprehensive...',
            author: 'Elena Ross'
        },
        {
            id: 3,
            category: 'BUSINESS',
            categoryColor: '#27a070',
            image: 'https://images.unsplash.com/photo-1611974714024-4607a5006300?auto=format&fit=crop&q=80&w=500',
            time: '5 hours ago',
            readTime: '3 min read',
            title: 'Quarterly Earnings Report: Shift in Consumer Trends',
            description: 'Retail giants report unexpected shifts in spending habits as consumers prioritize sustainable goods and...',
            author: 'Michael Chang'
        }
    ];

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
                <div className="text-dashboard">Noticias</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado-noticias" style={{ margin: '0', maxWidth: '100%' }}>
                        {newsData.map(item => (
                            <NewsCard key={item.id} item={item} />
                        ))}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default NoticiasHermano;