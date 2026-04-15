import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; 
import '../styles/HermanoMisPapeletasDeSitio.css'; 
import { Calendar, CalendarX, Dock, FileCheck, Download } from "lucide-react";

function MisPapeletas() {
    const [isOpen, setIsOpen] = useState(false); 

    const [user, setUser] = useState(null);
    const [papeletas, setPapeletas] = useState([]);
    const [ultimaPapeleta, setUltimaPapeleta] = useState(null);
    const [loading, setLoading] = useState(true);
    const [downloadingId, setDownloadingId] = useState(null);

    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalRegistros, setTotalRegistros] = useState(0);
    const [nextUrl, setNextUrl] = useState(null);
    const [prevUrl, setPrevUrl] = useState(null);

    const navigate = useNavigate();

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

                try {
                    const resUltima = await api.get("api/papeletas/ultima/");
                    if (isMounted) setUltimaPapeleta(resUltima.data);
                } catch (err) {
                    if (err.response?.status !== 404) {
                        console.error("Error cargando la última papeleta:", err);
                    }
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
    }, [page, navigate]);

    const toggleSidebar = () => setIsOpen(!isOpen);
    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        navigate("/login");
    };
    const handlePrev = () => { if (prevUrl) setPage(page - 1); };
    const handleNext = () => { if (nextUrl) setPage(page + 1); };

    const renderSitio = (papeleta) => {
        if (!papeleta.nombre_puesto && !papeleta.nombre_tramo) {
            return <span className="text-muted">Sin asignar</span>;
        }

        if (papeleta.es_insignia) {
            return (
                <span className="badge-insignia">
                    {papeleta.nombre_puesto || "Insignia asignada"}
                </span>
            );
        } else {
            return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <strong>{papeleta.nombre_puesto || "Cirio"}</strong>

                    <span style={{ fontSize: '0.85rem', color: '#666' }}>
                        {papeleta.numero_tramo ? `${papeleta.numero_tramo}º Tramo - ` : ''}
                        {papeleta.nombre_tramo || ''}
                        {papeleta.orden_en_tramo ? ` (Orden: ${papeleta.orden_en_tramo})` : ''}
                    </span>
                </div>
            );
        }
    };

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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                <div className="dashboard-split-layout-solicitud">
                    <div className="dashboard-panel-papeletas">
                        <div className="historical-header-container-papeletas">
                            <h1 className="historical-header-title-papeletas">HISTÓRICO DE PAPELETAS DE SITIO</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Resumen de tu historial de papeletas de sitio</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="papeletas-cards-container">
                            <div className="papeletas-card-wrapper">
                                <div className="papeletas-card-content">
                                    <div className="papeletas-card-icon">
                                        <Dock size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="papeletas-card-title">TOTAL PAPELETAS DE SITIO</h3>
                                    <p className="papeletas-card-description">
                                        Recuento histórico de las papeletas de sitio emitidas a tu nombre.
                                    </p>
                                    <div className="papeletas-card-date">
                                        {user ? user.total_papeletas_historicas : '0'}
                                    </div>
                                </div>
                            </div>

                            <div className="papeletas-card-wrapper">
                                <div className="papeletas-card-content">
                                    <div className="papeletas-card-icon">
                                        <FileCheck size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="papeletas-card-title">ESTADO ÚLTIMA PAPELETA</h3>
                                    <p className="papeletas-card-description">
                                        Estado de la última papeleta de sitio que solicitaste.
                                    </p>
                                    <div className="papeletas-card-date">
                                        {ultimaPapeleta ? ultimaPapeleta.estado_papeleta.replace('_', ' ') : <span style={{ fontSize: '1rem', color: '#666' }}>Sin registros</span>}
                                    </div>
                                </div>
                            </div>

                            <div className="papeletas-card-wrapper">
                                <div className="papeletas-card-content">
                                    <div className="papeletas-card-icon">
                                        <Calendar size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="papeletas-card-title">FECHA ÚLTIMA SOLICITUD</h3>
                                    <p className="papeletas-card-description">
                                        Fecha correspondiente a la última vez que solicitaste una papeleta de sitio.
                                    </p>
                                    <div className="papeletas-card-date">
                                        {ultimaPapeleta 
                                            ? (ultimaPapeleta.fecha_solicitud ? formatearFecha(ultimaPapeleta.fecha_solicitud) : ultimaPapeleta.anio) 
                                            : <span style={{ fontSize: '1rem', color: '#666' }}>Sin registros</span>
                                        }
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Últimas papeletas de sitio</span>
                            <div className="plazos-line"></div>
                        </div>

                        <section className="historial-section">
                                {papeletas.length > 0 ? (
                                    <div className="table-responsive">
                                        <table className="papeletas-table">
                                            <thead>
                                                <tr>
                                                    <th>Año</th>
                                                    <th>Acto</th>
                                                    <th>Fecha del Acto</th>
                                                    <th>Sitio Asignado</th>
                                                    <th>Estado</th>
                                                    <th>Acciones</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {papeletas.map((p) => (
                                                    <tr key={p.id}>
                                                        <td className="fw-bold">{p.anio}</td>
                                                        <td>{p.nombre_acto}</td>
                                                        <td>{formatearFecha(p.fecha_acto)}</td>
                                                        <td>{renderSitio(p)}</td>
                                                        <td>{renderEstado(p.estado_papeleta)}</td>
                                                        <td>
                                                            {['EMITIDA', 'RECOGIDA', 'LEIDA'].includes(p.estado_papeleta) ? (
                                                                <button 
                                                                    className="btn-descargar-pdf" 
                                                                    onClick={() => handleDownloadPDF(p.id, p.anio)}
                                                                    title="Descargar PDF"
                                                                    disabled={downloadingId === p.id}
                                                                >
                                                                    <Download size={20} />
                                                                </button>
                                                            ) : (
                                                                <span className="text-muted" style={{ fontSize: '0.85rem' }}>No disp.</span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="empty-state">
                                        <CalendarX size={48} className="empty-icon" />
                                        <p>No tienes histórico de papeletas de sitio.</p>
                                    </div>
                                )}

                                {/* Paginación */}
                                {totalPages > 1 && (
                                    <div className="pagination-controls">
                                        <button 
                                            onClick={handlePrev} 
                                            disabled={!prevUrl}
                                            className={!prevUrl ? 'disabled' : ''}
                                        >
                                            Anterior
                                        </button>
                                        <span>Página {page} de {totalPages}</span>
                                        <button 
                                            onClick={handleNext} 
                                            disabled={!nextUrl}
                                            className={!nextUrl ? 'disabled' : ''}
                                        >
                                            Siguiente
                                        </button>
                                    </div>
                                )}
                            </section>

                    </div>
                </div>
            </section>
        </div>
    );
}

export default MisPapeletas;