import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api';
import '../HermanoListadoPuestos/HermanoListadoPuestos.css'
import { ArrowLeft, CheckCircle2, XCircle, CheckCircle, AlertCircle } from "lucide-react";

function HermanoListadoPuestos() {
    const { actoId } = useParams(); 
    const navigate = useNavigate();
    const [isOpen, setIsOpen] = useState(false);

    const [currentUser, setCurrentUser] = useState(null);
    const [puestos, setPuestos] = useState([]);
    
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            setLoading(true);
            setError("");
            
            try {
                if (!currentUser) {
                    const userRes = await api.get("api/me/");
                    if (isMounted) setCurrentUser(userRes.data);
                }

                const puestosRes = await api.get(`api/actos/${actoId}/puestos/?page=${currentPage}`);
                
                if (isMounted) {
                    if (puestosRes.data && puestosRes.data.results) {
                        setPuestos(puestosRes.data.results);
                        setTotalPages(Math.ceil(puestosRes.data.count / 5));
                    } else {
                        setPuestos(puestosRes.data);
                        setTotalPages(1);
                    }
                }
            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar los puestos. Comprueba tu conexión.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [actoId, currentUser, currentPage]);

    const handleVincularTelegram = (e) => {
        e.preventDefault();

        if (currentUser && currentUser.enlace_vinculacion_telegram) {
            window.open(currentUser.enlace_vinculacion_telegram, '_blank');
        } else {
            console.error("El enlace de Telegram no está disponible.");
            alert("Hubo un problema al cargar tu enlace personal de Telegram.");
        }
    };

    const getNombreTipoActo = (tipo) => {
        if (!tipo) return "de Sitio";

        const tipoStr = typeof tipo === 'object' ? tipo.tipo : tipo;

        const diccionarioTipos = {
            'ESTACION_PENITENCIA': 'Estación de Penitencia',
            'CABILDO_GENERAL': 'Cabildo General',
            'CABILDO_EXTRAORDINARIO': 'Cabildo Extraordinario',
            'VIA_CRUCIS': 'Vía Crucis',
            'QUINARIO': 'Quinario',
            'TRIDUO': 'Triduo',
            'ROSARIO_AURORA': 'Rosario de la Aurora',
            'CONVIVENCIA': 'Convivencia',
            'PROCESION_EUCARISTICA': 'Procesión Eucarística',
            'PROCESION_EXTRAORDINARIA': 'Procesión Extraordinaria'
        };

        return diccionarioTipos[tipoStr] || "de Sitio";
    };

    const infoActo = puestos.length > 0 ? puestos[0] : null;
    const tituloActo = infoActo ? infoActo.acto_nombre : `Acto #${actoId}`;

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(prev => prev + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(prev => prev - 1);
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
                        <a href="/editar-mi-perfil">
                            <i className="bx bx-user"></i>
                            <span className="link_name-dashboard">Mi perfil</span>
                        </a>
                        <span className="tooltip-dashboard">Mi perfil</span>
                    </li>
                    <li>
                        <a href="/noticias">
                            <i className="bx bx-news"></i>
                            <span className="link_name-dashboard">Mis noticias</span>
                        </a>
                        <span className="tooltip-dashboard">Mis noticias</span>
                    </li>
                    <li>
                        <a href="/listado-cuotas">
                            <i className="bx bx-wallet"></i>
                            <span className="link_name-dashboard">Mis cuotas</span>
                        </a>
                        <span className="tooltip-dashboard">Mis cuotas</span>
                    </li>
                    <li>
                        <a href="/mis-papeletas-de-sitio">
                            <i className="bx bx-file"></i>
                            <span className="link_name-dashboard">Mis papeletas</span>
                        </a>
                        <span className="tooltip-dashboard">Mis papeletas</span>
                    </li>
                    <li>
                        <a href="/listado-actos">
                            <i className="bx bx-calendar-event"></i>
                            <span className="link_name-dashboard">Actos</span>
                        </a>
                        <span className="tooltip-dashboard">Actos</span>
                    </li>
                    <li>
                        <a href="/areas-de-interes">
                            <i className="bx bx-list-ul"></i>
                            <span className="link_name-dashboard">Áreas de Interés</span>
                        </a>
                        <span className="tooltip-dashboard">Áreas de Interés</span>
                    </li>
                    <li>
                        <a 
                            href="#" 
                            onClick={!currentUser?.telegram_chat_id ? handleVincularTelegram : (e) => e.preventDefault()}
                            style={{ 
                                cursor: currentUser?.telegram_chat_id ? 'default' : 'pointer',
                                opacity: currentUser?.telegram_chat_id ? 0.6 : 1
                            }}
                        >
                            <i className="bx bxl-telegram"></i>
                            <span className="link_name-dashboard">
                                {currentUser?.telegram_chat_id ? "Telegram Vinculado ✅" : "Vincular Telegram"}
                            </span>
                        </a>
                        <span className="tooltip-dashboard">
                            {currentUser?.telegram_chat_id ? "Ya vinculado" : "Vincular Telegram"}
                        </span>
                    </li>
                    {currentUser?.esAdmin && (
                        <li>
                            <a href="/censo-hermanos">
                                <i className="bx bx-group"></i>
                                <span className="link_name-dashboard">Censo</span>
                            </a>
                            <span className="tooltip-dashboard">Censo</span>
                        </li>
                    )}
                    
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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                <div className="dashboard-split-layout-solicitud">
                    <div className="dashboard-panel-puestos">
                        <div className="historical-header-container-puestos">
                            <h1 className="historical-header-title-puestos">LISTADO DE PUESTOS</h1>
                            <p className="historical-header-subtitle">
                                {getNombreTipoActo(infoActo?.acto_tipo)} {infoActo?.acto_fecha ? new Date(infoActo.acto_fecha).getFullYear() : ""}
                            </p>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Resumen de puestos</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="puestos-cards-container">
                            <div className="puestos-card-wrapper">
                                <div className="puestos-card-content">
                                    <div className="puestos-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="puestos-card-title">TOTAL CUOTAS PAGADAS</h3>
                                    <p className="puestos-card-description">
                                        Número total de cuotas pagadas que constan actualmente en tu historial.
                                    </p>
                                    <div className="puestos-card-date">
                                        100
                                    </div>
                                </div>
                            </div>

                            <div className="puestos-card-wrapper">
                                <div className="puestos-card-content">
                                    <div className="puestos-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="puestos-card-title">TOTAL CUOTAS PAGADAS</h3>
                                    <p className="puestos-card-description">
                                        Número total de cuotas pagadas que constan actualmente en tu historial.
                                    </p>
                                    <div className="puestos-card-date">
                                        100
                                    </div>
                                </div>
                            </div>

                            <div className="puestos-card-wrapper">
                                <div className="puestos-card-content">
                                    <div className="puestos-card-icon">
                                        <CheckCircle size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="puestos-card-title">TOTAL CUOTAS PAGADAS</h3>
                                    <p className="puestos-card-description">
                                        Número total de cuotas pagadas que constan actualmente en tu historial.
                                    </p>
                                    <div className="puestos-card-date">
                                        100
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Listado de puestos</span>
                            <div className="plazos-line"></div>
                        </div>

                        <section className="historial-puestos-section">
                            {puestos.length > 0 ? (
                                <div className="table-responsive">
                                    <table className="puestos-table">
                                        <thead>
                                            <tr>
                                                <th>Nombre del puesto</th>
                                                <th>Tipo de puesto</th>
                                                <th>Cortejo</th>
                                                <th>Cupo máximo</th>
                                                <th>Disponible</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {puestos.map((puesto) => (
                                                <tr key={puesto.id}>
                                                    <td className="fw-bold">{puesto.nombre}</td>
                                                    <td>{puesto.tipo_puesto?.nombre_tipo || 'N/A'}</td>
                                                    <td>
                                                        <span className={`badge-cortejo ${puesto.cortejo_cristo ? 'cristo' : 'virgen'}`}>
                                                            {puesto.cortejo_cristo ? 'Cristo' : 'Virgen'}
                                                        </span>
                                                    </td>
                                                    <td className="fw-bold">{puesto.numero_maximo_asignaciones}</td>
                                                    <td>
                                                        {puesto.disponible ? (
                                                            <CheckCircle2 size={20} color="#16a34a" title="Disponible" style={{ display: 'inline-block' }} />
                                                        ) : (
                                                            <XCircle size={20} color="#dc2626" title="No disponible" style={{ display: 'inline-block' }} />
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <AlertCircle size={48} className="empty-icon" />
                                    <p>No hay puestos registrados para este acto.</p>
                                </div>
                            )}

                            {totalPages > 1 && (
                                <div className="pagination-controls-puestos">
                                    <button 
                                        onClick={handlePrevPage} 
                                        disabled={currentPage === 1}
                                        className={currentPage === 1 ? 'disabled' : ''}
                                    >
                                        Anterior
                                    </button>
                                    <span>Página {currentPage} de {totalPages}</span>
                                    <button 
                                        onClick={handleNextPage} 
                                        disabled={currentPage === totalPages}
                                        className={currentPage === totalPages ? 'disabled' : ''}
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

export default HermanoListadoPuestos;