import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; // Asegúrate de que tu instancia de axios está aquí
import '../styles/AdminListadoHermanos.css'; // Reutilizamos estilos
import { 
    ChevronLeft, 
    ChevronRight, 
    Scroll, // Icono para papeleta/pergamino
    MapPin, 
    Calendar,
    Clock
} from "lucide-react";

function MisPapeletas() {
    const [isOpen, setIsOpen] = useState(false); // Sidebar state
    
    // Estados de datos
    const [user, setUser] = useState(null);
    const [papeletas, setPapeletas] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Estados de paginación
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalRegistros, setTotalRegistros] = useState(0);
    const [nextUrl, setNextUrl] = useState(null);
    const [prevUrl, setPrevUrl] = useState(null);

    const navigate = useNavigate();

    // --- FORMATEADORES ---
    const formatearFecha = (fechaString) => {
        if (!fechaString) return "-";
        const fecha = new Date(fechaString);
        return fecha.toLocaleDateString('es-ES', {
            day: '2-digit', month: '2-digit', year: 'numeric'
        });
    };

    const formatearHora = (horaString) => {
        if (!horaString) return "-";
        // Si viene HH:MM:SS, cortamos los segundos
        return horaString.substring(0, 5);
    };

    // --- EFECTO DE CARGA ---
    useEffect(() => {
        let isMounted = true; 

        const fetchData = async () => {
            setLoading(true);
            try {
                // 1. Cargar Usuario (para la sidebar y verificar sesión)
                let userData = user;
                if (!userData) {
                    const resUser = await api.get("api/me/");
                    userData = resUser.data;
                    if (isMounted) setUser(userData);
                }

                // 2. Cargar Papeletas
                // NOTA: Usamos el endpoint que definimos en urls.py
                const resListado = await api.get(`api/papeletas/mis-papeletas/?page=${page}`);
                
                if (isMounted) {
                    setPapeletas(resListado.data.results);
                    setTotalRegistros(resListado.data.count);
                    setNextUrl(resListado.data.next);
                    setPrevUrl(resListado.data.previous);
                    
                    // Calculamos páginas totales (PageSize definido en backend como 20)
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

    // --- HANDLERS ---
    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        navigate("/login");
    };

    const handlePrev = () => { if (prevUrl) setPage(page - 1); };
    const handleNext = () => { if (nextUrl) setPage(page + 1); };

    // --- RENDERIZADO CONDICIONAL DE SITIO ---
    const renderSitio = (papeleta) => {
        // Lógica visual basada en tus campos del Serializer
        if (papeleta.es_insignia) {
            return (
                <span className="badge-insignia">
                    {papeleta.nombre_puesto || "Insignia asignada"}
                </span>
            );
        } else {
            // Es Cirio
            if (!papeleta.nombre_tramo) return <span className="text-muted">Sin asignar</span>;
            return (
                <span>
                    {papeleta.numero_tramo ? <strong>{papeleta.numero_tramo}º </strong> : ''}
                    {papeleta.nombre_tramo}
                </span>
            );
        }
    };

    // --- RENDERIZADO DE ESTADO ---
    const renderEstado = (estado) => {
        const estadoClass = {
            'EMITIDA': 'success',
            'RECOGIDA': 'purple',
            'LEIDA': 'info',
            'ANULADA': 'error',
            'SOLICITADA': 'warning',
            'NO_SOLICITADA': 'neutral'
        }[estado] || 'neutral';

        return <span className={`status-badge ${estadoClass}`}>{estado}</span>;
    };

    if (loading && !user) return <div className="site-wrapper loading-screen">Cargando histórico...</div>;

    return (
        <div>
            {/* --- SIDEBAR (Mismo código que AdminListadoHermanos) --- */}
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} id="btn" onClick={toggleSidebar}></i>
                </div>
                <ul className="nav-list-dashboard">
                    {/* ... (Aquí irían tus enlaces de navegación habituales) ... */}
                    <li>
                         <a href="#" onClick={() => navigate("/dashboard")}>
                            <i className="bx bx-grid-alt"></i>
                            <span className="link_name-dashboard">Inicio</span>
                        </a>
                        <span className="tooltip-dashboard">Inicio</span>
                    </li>
                    
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            <img src="/profile.jpeg" alt="profile" /> 
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{user ? `${user.nombre} ${user.primer_apellido}` : "Hermano"}</div>
                                <div className="designation-dashboard">Hermano</div>
                            </div>
                        </div>
                        <i className="bx bx-log-out" id="log_out" onClick={handleLogout} style={{cursor: 'pointer'}}></i>
                    </li>
                </ul>
            </div>

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Histórico de Sitios</div>

                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        <header className="content-header-area">
                            <div className="title-row-area">
                                <div style={{display:'flex', alignItems:'center', gap: '10px'}}>
                                    <Scroll size={28} className="text-purple" />
                                    <h2>Mis Papeletas de Sitio</h2>
                                </div>
                            </div>
                            <p className="description-area">
                                Has realizado estación de penitencia o participado en <strong>{totalRegistros}</strong> actos.
                            </p>
                        </header>

                        <div className="table-responsive">
                            {loading ? (
                                <div className="loading-state">Cargando datos...</div>
                            ) : (
                                <table className="hermanos-table">
                                    <thead>
                                        <tr>
                                            <th>Año</th>
                                            <th>Acto</th>
                                            <th>Sitio / Puesto</th>
                                            <th>Citación</th>
                                            <th>Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {papeletas.length > 0 ? (
                                            papeletas.map((papeleta) => (
                                                <tr key={papeleta.id} className="row-hover">
                                                    
                                                    {/* AÑO */}
                                                    <td style={{fontWeight: 'bold', color: '#555'}}>{papeleta.anio}</td>
                                                    
                                                    {/* ACTO */}
                                                    <td>
                                                        <div style={{display:'flex', flexDirection:'column'}}>
                                                            <span style={{fontWeight:'600'}}>{papeleta.nombre_acto}</span>
                                                            <span style={{fontSize:'0.85em', color:'#888'}}>
                                                                <Calendar size={12} style={{marginRight:'4px'}}/>
                                                                {formatearFecha(papeleta.fecha_acto)}
                                                            </span>
                                                        </div>
                                                    </td>

                                                    {/* SITIO (Lógica Insignia vs Cirio) */}
                                                    <td>
                                                        {renderSitio(papeleta)}
                                                    </td>

                                                    {/* CITACIÓN */}
                                                    <td>
                                                        {papeleta.lugar_citacion ? (
                                                            <div style={{fontSize:'0.9em'}}>
                                                                <div style={{display:'flex', alignItems:'center', gap:'5px'}}>
                                                                    <MapPin size={14} className="text-muted"/> 
                                                                    {papeleta.lugar_citacion}
                                                                </div>
                                                                {papeleta.hora_citacion && (
                                                                    <div style={{display:'flex', alignItems:'center', gap:'5px', marginTop:'2px'}}>
                                                                        <Clock size={14} className="text-muted"/> 
                                                                        {formatearHora(papeleta.hora_citacion)}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ) : (
                                                            <span className="text-muted">-</span>
                                                        )}
                                                    </td>

                                                    {/* ESTADO */}
                                                    <td>{renderEstado(papeleta.estado_papeleta)}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="5" className="text-center" style={{padding: '40px'}}>
                                                    No tienes papeletas de sitio registradas en el histórico.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            )}
                        </div>

                        {/* --- PAGINACIÓN --- */}
                        {totalRegistros > 0 && (
                            <footer className="pagination-footer">
                                <span className="page-info">
                                    Página {page} de {totalPages}
                                </span>
                                <div className="pagination-controls">
                                    <button 
                                        className="btn-pagination" 
                                        onClick={handlePrev} 
                                        disabled={!prevUrl || loading}
                                    >
                                        <ChevronLeft size={16} /> Anterior
                                    </button>
                                    
                                    <button 
                                        className="btn-pagination" 
                                        onClick={handleNext} 
                                        disabled={!nextUrl || loading}
                                    >
                                        Siguiente <ChevronRight size={16} />
                                    </button>
                                </div>
                            </footer>
                        )}

                    </div>
                </div>
            </section>
        </div>
    );
}

export default MisPapeletas;