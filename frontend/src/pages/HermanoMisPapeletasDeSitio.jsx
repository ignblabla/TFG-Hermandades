import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; 
import '../styles/HermanoMisPapeletasDeSitio.css'; 
import { ChevronLeft, ChevronRight, Scroll, Download } from "lucide-react";

function MisPapeletas() {
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
        return horaString.substring(0, 5);
    };

    // --- DESCARGAR PDF ---
    const handleDownloadPDF = async (papeletaId, anio) => {
        setDownloadingId(papeletaId);
        try {
            const response = await api.get(`api/papeletas/${papeletaId}/descargar/`, {
                responseType: 'blob', 
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `Papeleta_SanGonzalo_${anio}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Error descargando PDF:", err);
            alert("No se pudo descargar el documento. Inténtelo más tarde.");
        } finally {
            setDownloadingId(null);
        }
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
        if (papeleta.es_insignia) {
            return (
                <span className="badge-insignia">
                    {papeleta.nombre_puesto || "Insignia asignada"}
                </span>
            );
        } else {
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
                <div className="text-dashboard">Histórico de papeletas de sitio</div>
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
                                Número total de papeletas de sitio encontradas: <strong>{totalRegistros}</strong>
                            </p>
                        </header>

                        <div className="table-responsive">
                            {loading ? (
                                <div className="loading-state">Cargando censo...</div>
                            ) : (
                                <table className="papeletas-table">
                                    <thead>
                                        <tr>
                                            <th>Año</th>
                                            <th>Acto</th>
                                            <th>Fecha acto</th>
                                            <th>Sitio / Puesto</th>
                                            <th>Lugar</th>
                                            <th>Hora</th>
                                            <th>Fecha emisión</th>
                                            <th>Estado</th>
                                            <th>Acciones</th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {papeletas.length > 0 ? (
                                            papeletas.map((papeleta) => {
                                                const puedeDescargar = ['EMITIDA', 'RECOGIDA', 'LEIDA'].includes(papeleta.estado_papeleta);
                                                
                                                return (
                                                    <tr key={papeleta.id} style={{borderBottom: '1px solid #f1f5f9', cursor: 'pointer'}} className="row-hover">
                                                        <td>{papeleta.anio}</td>
                                                        <td className="cell-nombre-acto" title={papeleta.nombre_acto}>
                                                            {papeleta.nombre_acto || ""}
                                                        </td>
                                                        <td><div>{formatearFecha(papeleta.fecha_acto)}</div></td>

                                                        <td className="cell-nombre-acto">{renderSitio(papeleta)}</td>

                                                        <td className="cell-nombre-acto" title={papeleta.lugar_citacion}>
                                                            {papeleta.lugar_citacion ? (<div>{papeleta.lugar_citacion}</div>) : (<span className="text-muted">-</span>)}
                                                        </td>
                                                        <td>{papeleta.hora_citacion ? (<div>{formatearHora(papeleta.hora_citacion)}</div>) : (<span className="text-muted">-</span>)}
                                                        </td>
                                                        <td>
                                                            <div>{papeleta.fecha_emision ? (<>{formatearFecha(papeleta.fecha_emision)}</>) : '-'}</div>
                                                        </td>

                                                        <td>{renderEstado(papeleta.estado_papeleta)}</td>

                                                        <td>
                                                            {puedeDescargar ? (
                                                                <button 
                                                                    className="btn-download-action"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleDownloadPDF(papeleta.id, papeleta.anio);
                                                                    }}
                                                                    disabled={downloadingId === papeleta.id}
                                                                    title="Descargar PDF con código QR"
                                                                >
                                                                    {downloadingId === papeleta.id ? (
                                                                        <span className="loader-dots">...</span>
                                                                    ) : (
                                                                        <>
                                                                            <Download size={16} /> 
                                                                            <span>PDF</span>
                                                                        </>
                                                                    )}
                                                                </button>
                                                            ) : (
                                                                <span className="text-muted text-small" style={{fontSize: '0.8em'}}>No disponible</span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                );
                                            })
                                        ) : (
                                            <tr>
                                                <td colSpan="9" className="text-center" style={{padding: '40px'}}>
                                                    No tienes papeletas de sitio registradas.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default MisPapeletas;