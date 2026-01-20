import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api"; 
import "../styles/MisPapeletas.css"; 
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, FileText, CheckCircle, Clock, AlertCircle, Download, Calendar } from "lucide-react";

function MisPapeletas() {
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [papeletas, setPapeletas] = useState([]);
    const [error, setError] = useState("");

    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                setUser(resUser.data);

                const resPapeletas = await api.get("api/papeletas/mis-papeletas/");
                setPapeletas(resPapeletas.data);

            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response && err.response.status === 401) {
                    localStorage.removeItem("access");
                    navigate("/login");
                } else {
                    setError("No se pudo cargar el historial de papeletas.");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/";
    };

    const formatearFecha = (fechaISO) => {
        if (!fechaISO) return "Fecha por determinar";
        const fecha = new Date(fechaISO);
        return fecha.toLocaleDateString('es-ES', { 
            day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute:'2-digit' 
        });
    };

    const getEstadoBadge = (estado) => {
        switch (estado) {
            case 'SOLICITADA':
                return { class: 'badge-warning', icon: <Clock size={14} />, text: 'Solicitada' };
            case 'EMITIDA':
                return { class: 'badge-info', icon: <AlertCircle size={14} />, text: 'Emitida' };
            case 'RECOGIDA':
                return { class: 'badge-success', icon: <CheckCircle size={14} />, text: 'Recogida' };
            case 'LEIDA':
                return { class: 'badge-success', icon: <CheckCircle size={14} />, text: 'Completada' };
            case 'ANULADA':
                return { class: 'badge-danger', icon: <AlertCircle size={14} />, text: 'Anulada' };
            default:
                return { class: 'badge-default', icon: <FileText size={14} />, text: estado };
        }
    };

    if (loading) return <div className="site-wrapper loading-screen">Cargando tus papeletas...</div>;

    return (
        <div className="site-wrapper">
            <nav className="navbar">
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo San Gonzalo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SEVILLA</span>
                    </div>
                </div>
                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
                <ul className={`nav-links ${menuOpen ? "active" : ""}`}>
                    <li><a href="/home">Inicio</a></li>
                    <li><a href="/agenda">Agenda</a></li>
                    <div className="nav-buttons-mobile">
                        {user && <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>}
                    </div>
                </ul>
                <div className="nav-buttons-desktop">
                    {user && (
                        <>
                            <button className="btn-outline" onClick={() => navigate("/perfil")}>Hermano: {user.dni}</button>
                            <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                        </>
                    )}
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area full-width-card">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Mis Papeletas de Sitio</h1>
                            <button className="btn-back-area" onClick={() => navigate("/home")}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Consulta el historial detallado de tus solicitudes y asignaciones.
                        </p>
                    </header>

                    {error && <div className="alert-box error">{error}</div>}

                    {papeletas.length === 0 && !error ? (
                        <div className="empty-state">
                            <FileText size={48} color="#cbd5e1" />
                            <p>No hay registros de papeletas.</p>
                            <button className="btn-purple mt-4" onClick={() => navigate("/agenda")}>
                                Ver Actos Disponibles
                            </button>
                        </div>
                    ) : (
                        // --- CAMBIO PRINCIPAL: TABLA EN LUGAR DE CARDS ---
                        <div className="table-responsive">
                            <table className="custom-table">
                                <thead>
                                    <tr>
                                        <th style={{width: '60px'}}>Año</th>
                                        <th>Acto / Fecha</th>
                                        <th>Detalle Sitio</th>
                                        <th style={{width: '120px'}}>Estado</th>
                                        <th style={{width: '140px'}}>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {papeletas.map((papeleta) => {
                                        const estadoInfo = getEstadoBadge(papeleta.estado_papeleta);
                                        const tieneSitio = papeleta.nombre_puesto; 
                                        const puedeDescargar = papeleta.estado_papeleta === 'EMITIDA' || papeleta.estado_papeleta === 'RECOGIDA';

                                        return (
                                            <tr key={papeleta.id}>
                                                <td className="text-center font-bold text-muted">{papeleta.anio}</td>
                                                
                                                <td>
                                                    <div className="fw-bold">{papeleta.nombre_acto}</div>
                                                    <div className="text-small text-muted flex-center">
                                                        <Calendar size={12} style={{marginRight: '4px'}}/> 
                                                        {formatearFecha(papeleta.fecha_acto)}
                                                    </div>
                                                </td>

                                                {/* DETALLE DEL SITIO */}
                                                <td>
                                                    {tieneSitio ? (
                                                        <div className="info-cell-assigned">
                                                            <span className="puesto-highlight">{papeleta.nombre_puesto}</span>
                                                            {papeleta.tramo_display && <span className="tramo-text">{papeleta.tramo_display}</span>}
                                                            {papeleta.numero_papeleta && <span className="numero-badge">#{papeleta.numero_papeleta}</span>}
                                                        </div>
                                                    ) : (
                                                        <div className="info-cell-requested">
                                                            <span className="pref-label">Solicitado:</span>
                                                            <ul className="pref-list-inline">
                                                                {papeleta.preferencias && papeleta.preferencias.length > 0 ? (
                                                                    papeleta.preferencias.map(pref => (
                                                                        <li key={pref.id}>
                                                                            <span className="pref-number">{pref.orden_prioridad}</span> {pref.nombre_puesto}
                                                                        </li>
                                                                    ))
                                                                ) : (
                                                                    <li>Cirio (Solicitud General)</li>
                                                                )}
                                                            </ul>
                                                        </div>
                                                    )}
                                                </td>

                                                {/* ESTADO */}
                                                <td>
                                                    <div className={`status-badge ${estadoInfo.class}`}>
                                                        {estadoInfo.icon}
                                                        <span>{estadoInfo.text}</span>
                                                    </div>
                                                </td>

                                                {/* ACCIONES */}
                                                <td>
                                                    {puedeDescargar ? (
                                                        <button className="btn-table-action">
                                                            <Download size={16} /> PDF
                                                        </button>
                                                    ) : (
                                                        <span className="text-muted text-small">-</span>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default MisPapeletas;