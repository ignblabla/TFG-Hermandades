import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";
import '../HermanoSolicitudCirio/HermanoCrearSolicitudCirio.css'
import { AlertCircle, CheckCircle, Save, CalendarX, User, ScrollText } from "lucide-react";

function HermanoCrearSolicitudCirio() {

    const { id } = useParams();

    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [isOpen, setIsOpen] = useState(false);

    const [actoInfo, setActoInfo] = useState(null); 
    const [puestosCirio, setPuestosCirio] = useState([]);
    
    const [selectedPuestoId, setSelectedPuestoId] = useState("");
    const [numeroVinculado, setNumeroVinculado] = useState(""); 

    const [ultimoAnioParticipacion, setUltimoAnioParticipacion] = useState("-");

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [successData, setSuccessData] = useState(null);

    const navigate = useNavigate();

    const getHistoryTitle = (tipoActo) => {
        switch (tipoActo) {
            case 'ESTACION_PENITENCIA':
                return 'Última estación de penitencia';
            case 'VIA_CRUCIS':
                return 'Último Vía Crucis';
            case 'ROSARIO_AURORA':
                return 'Último Rosario Aurora';
            case 'PROCESION_EXTRAORDINARIA':
                return 'Última procesión extraordinaria';
            default:
                return 'Estación';
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                setUser(resUser.data);

                const resActo = await api.get(`api/actos/${id}/`);
                const actoData = resActo.data;

                setActoInfo(actoData);

                const now = new Date();

                if (!actoData.requiere_papeleta || actoData.modalidad !== 'TRADICIONAL' || !actoData.inicio_solicitud_cirios || !actoData.fin_solicitud_cirios) {
                    setError("Este acto no está configurado para la solicitud de cirios.");
                    setLoading(false);
                    return;
                }

                const inicio = new Date(actoData.inicio_solicitud_cirios);
                const fin = new Date(actoData.fin_solicitud_cirios);
                
                if (now < inicio || now > fin) {
                    setError("El plazo para solicitar sitio en este acto está cerrado.");
                    setLoading(false);
                    return;
                }

                const ciriosDisponibles = actoData.puestos_disponibles.filter(p => {
                    return p.disponible === true && p.es_insignia === false;
                });

                if (ciriosDisponibles.length === 0) {
                    setError("No hay cupo de cirios disponible para este acto.");
                }

                setPuestosCirio(ciriosDisponibles);

                try {
                    const resPapeletas = await api.get("api/papeletas/mis-papeletas/"); 

                    const papeletas = resPapeletas.data.results || resPapeletas.data;

                    const ultimaPapeleta = papeletas.find(
                        (p) => p.tipo_acto === actoData.tipo_acto && p.estado_papeleta !== 'ANULADA' && p.estado_papeleta !== 'NO_ASIGNADA'
                    );

                    if (ultimaPapeleta) {
                        setUltimoAnioParticipacion(ultimaPapeleta.anio);
                    } else {
                        setUltimoAnioParticipacion("-");
                    }
                } catch (historialErr) {
                    console.error("Error al obtener el historial de papeletas:", historialErr);
                    setUltimoAnioParticipacion("-");
                }

            } catch (err) {
                console.error(err);
                if (err.response?.status === 401) navigate("/login");
                else if (err.response?.status === 404) setError("El acto indicado no existe.");
                else setError("Error cargando los datos del servidor.");
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchData();
        }
    }, [id, navigate]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!id || !selectedPuestoId) {
            setError("Faltan datos para realizar la solicitud.");
            return;
        }

        setSubmitting(true);
        setError("");
        setSuccess(false);

        const payload = {
            acto: parseInt(id),
            puesto: selectedPuestoId,
            numero_registro_vinculado: numeroVinculado ? parseInt(numeroVinculado) : null
        };

        try {
            const res = await api.post("api/papeletas/solicitar-cirio/", payload);
            
            setSuccess(true);
            setSuccessData(res.data); 
            
            setSelectedPuestoId("");
            setNumeroVinculado("");
            
            setTimeout(() => navigate("/mis-papeletas"), 4000); 

        } catch (err) {
            if (err.response?.data) {
                const data = err.response.data;
                if (data.detail) setError(data.detail);
                else if (data.non_field_errors) setError(data.non_field_errors[0]);
                else if (data.numero_registro_vinculado) setError(`Error vinculación: ${data.numero_registro_vinculado[0]}`);
                else if (data.puesto) setError(`Error en puesto: ${data.puesto[0]}`);
                else setError("No se pudo procesar la solicitud. Revise los datos.");
            } else {
                setError("Error de conexión con el servidor.");
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("access");
        window.location.href = "/";
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

    const formatearFechaHora = (fechaString) => {
        if (!fechaString) return "Fecha por determinar";
        
        const date = new Date(fechaString);
        const dia = date.getDate();
        const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        const mes = meses[date.getMonth()];

        const hora = date.getHours().toString().padStart(2, '0');
        const minutos = date.getMinutes().toString().padStart(2, '0');
        
        return `${dia} de ${mes}, ${hora}:${minutos}`;
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
                    <div className="dashboard-panel-main-solicitud">
                        <div className="banner-solicitud-container">
                            <div className="banner-solicitud-text">
                                <h1 className="banner-solicitud-title">
                                    SOLICITUD DE CIRIOS
                                </h1>
                                <p className="banner-solicitud-description">
                                    {getNombreTipoActo(actoInfo?.tipo_acto)} {actoInfo?.fecha ? new Date(actoInfo.fecha).getFullYear() : ""}
                                </p>
                            </div>
                            <div className="banner-solicitud-image-wrapper">
                                <img 
                                    src={actoInfo?.imagen_portada ? actoInfo.imagen_portada : "../../assets/ViaCrucis2025.jpg"} 
                                    alt={actoInfo?.nombre ? `Portada de ${actoInfo.nombre}` : "Cartel del acto"} 
                                    className="banner-solicitud-image"
                                />
                            </div>
                        </div>

                        <div className="plazos-separator">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">PLAZOS IMPRORROGABLES</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="plazos-cards-container">
                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <CalendarX size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">FIN SOLICITUD INSIGNIAS</h3>
                                    <p className="plazo-card-description">
                                        Fecha de cierre para la solicitud general de insignias y varas.
                                    </p>
                                    <div className="plazo-card-date">
                                        {formatearFechaHora(actoInfo?.fin_solicitud)}
                                    </div>
                                </div>
                            </div>

                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <CalendarX size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">INICIO SOLICITUD CIRIOS</h3>
                                    <p className="plazo-card-description">
                                        Fecha de inicio para la solicitud general de cirios y cruces.
                                    </p>
                                    <div className="plazo-card-date">
                                        {formatearFechaHora(actoInfo?.inicio_solicitud_cirios)}
                                    </div>
                                </div>
                            </div>

                            <div className="plazo-card-wrapper">
                                <div className="plazo-card-content">
                                    <div className="plazo-card-icon">
                                        <CalendarX size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="plazo-card-title">FIN SOLICITUD CIRIOS</h3>
                                    <p className="plazo-card-description">
                                        Fecha de cierre para la solicitud general de cirios y cruces.
                                    </p>
                                    <div className="plazo-card-date">
                                        {formatearFechaHora(actoInfo?.fin_solicitud_cirios)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">FORMULARIO DE SOLICITUD DE CIRIO</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="solicitud-form-container">
                            {error && (
                                <div className="form-alert form-alert-error">
                                    <AlertCircle size={20} />
                                    <span>{error}</span>
                                </div>
                            )}
                            
                            {success && (
                                <div className="form-alert form-alert-success">
                                    <CheckCircle size={20} />
                                    <span>Solicitud procesada correctamente. Redirigiendo a sus papeletas...</span>
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="solicitud-form">
                                <div className="form-group">
                                    <label htmlFor="puesto-select" className="form-label">
                                        Puesto Solicitado <span className="required">*</span>
                                    </label>
                                    <div className="input-wrapper">
                                        <select
                                            id="puesto-select"
                                            className="form-control no-icon"
                                            value={selectedPuestoId}
                                            onChange={(e) => setSelectedPuestoId(e.target.value)}
                                            required
                                            disabled={submitting || success || loading}
                                        >
                                            <option value="">-- Seleccione un puesto --</option>
                                            {puestosCirio.map(puesto => (
                                                <option key={puesto.id} value={puesto.id}>
                                                    {puesto.nombre}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="vinculo-input" className="form-label">
                                        Vincular con Hermano (Nº Registro)
                                    </label>
                                    <p className="form-help-text">
                                        Opcional. Si desea ir junto a otro hermano, indique su número de registro.
                                    </p>
                                    <div className="input-wrapper">
                                        <input
                                            type="number"
                                            id="vinculo-input"
                                            className="form-control no-icon"
                                            placeholder="Ej: 1234"
                                            value={numeroVinculado}
                                            onChange={(e) => setNumeroVinculado(e.target.value)}
                                            disabled={submitting || success || loading}
                                        />
                                    </div>
                                </div>

                                <button 
                                    type="submit" 
                                    className="submit-btn"
                                    disabled={submitting || success || loading}
                                >
                                    {submitting ? 'Procesando...' : (
                                        <>
                                            <Save size={20} />
                                            Confirmar Solicitud
                                        </>
                                    )}
                                </button>
                            </form>
                        </div>
                    </div>

                    <div className="dashboard-panel-sidebar-solicitud">
                        <div className="estado-hermano-card">
                            <div className="estado-hermano-icon">
                                <User size={44} strokeWidth={2.5} />
                            </div>
                            
                            <h2 className="estado-hermano-title">ESTADO DEL HERMANO</h2>
                            
                            <div className="estado-hermano-cuota">
                                <p>
                                    <span className="estado-ok">Al corriente de pago</span>
                                </p>
                            </div>

                            <hr className="estado-hermano-divider" />

                            <div className="estado-hermano-datos">
                                <p>
                                    Nº de registro: <span className="estado-bold">{user?.numero_registro || "-"}</span>
                                </p>
                                <p>
                                    Antigüedad: <span className="estado-bold">{user?.antiguedad_anios !== undefined ? user.antiguedad_anios : "-"} años</span>
                                </p>
                            </div>
                        </div>

                        <div className="criterios-card">
                            <div className="criterios-icon">
                                <ScrollText size={40} strokeWidth={2} />
                            </div>
                            
                            <h2 className="criterios-title">CRITERIOS DE ASIGNACIÓN</h2>
                            
                            <p className="criterios-intro">
                                Conforme a la Regla 42ª, los puestos se asignan estrictamente por <span className="criterios-bold">orden de antigüedad</span> en la nómina <span className="criterios-bold">de hermanos</span>, salvo los cargos de confianza designados por la Junta de Gobierno.
                            </p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default HermanoCrearSolicitudCirio;