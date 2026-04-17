import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";
import '../HermanoSolicitudCirio/HermanoCrearSolicitudCirio.css'
import { AlertCircle, CheckCircle, Save, CalendarX, ScrollText, Shirt, X, Info, CalendarCheck, Flame } from "lucide-react";

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

    // ESTADOS DE MODALES
    const [modalBloqueo, setModalBloqueo] = useState(false);
    const [modalNoActivo, setModalNoActivo] = useState(false);
    const [modalFueraPlazoConSolicitud, setModalFueraPlazoConSolicitud] = useState(false);
    const [fechaSolicitudRealizada, setFechaSolicitudRealizada] = useState(null);

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
        let isMounted = true;

        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                if (isMounted) setUser(resUser.data);

                try {
                    const resActo = await api.get(`api/actos/${id}/`);
                    if (isMounted) {
                        const actoData = resActo.data;
                        setActoInfo(actoData);

                        if (!actoData.requiere_papeleta || actoData.modalidad !== 'TRADICIONAL' || !actoData.inicio_solicitud_cirios || !actoData.fin_solicitud_cirios) {
                            setError("Este acto no está configurado para la solicitud de cirios.");
                            setModalNoActivo(true);
                            return;
                        }

                        const now = new Date();
                        const inicioPlazo = new Date(actoData.inicio_solicitud_cirios);
                        const finPlazo = new Date(actoData.fin_solicitud_cirios);
                        const enPlazo = now >= inicioPlazo && now <= finPlazo;

                        const ciriosDisponibles = actoData.puestos_disponibles.filter(p => {
                            return p.disponible === true && p.es_insignia === false;
                        });
                        setPuestosCirio(ciriosDisponibles);

                        try {
                            const resPapeletas = await api.get("api/papeletas/mis-papeletas/"); 
                            const papeletas = resPapeletas.data.results || resPapeletas.data;

                            const papeletaActiva = papeletas.find(p => {
                                const coincideActo = Number(p.acto) === Number(id); 
                                const estado = String(p.estado_papeleta || '').toUpperCase();
                                const estaActiva = estado !== 'ANULADA' && estado !== 'NO_ASIGNADA';
                                return coincideActo && estaActiva;
                            });

                            const ultimaPapeleta = papeletas.find(
                                (p) => p.tipo_acto === actoData.tipo_acto && p.estado_papeleta !== 'ANULADA' && p.estado_papeleta !== 'NO_ASIGNADA' && Number(p.acto) !== Number(id)
                            );

                            if (ultimaPapeleta) {
                                setUltimoAnioParticipacion(ultimaPapeleta.anio);
                            } else {
                                setUltimoAnioParticipacion("-");
                            }

                            if (papeletaActiva) {
                                if (enPlazo) {
                                    setModalBloqueo(true);
                                } else {
                                    setFechaSolicitudRealizada(papeletaActiva.fecha_solicitud || papeletaActiva.fecha_emision || papeletaActiva.created_at);
                                    setModalFueraPlazoConSolicitud(true);
                                }
                            } else {
                                if (!enPlazo) {
                                    setModalNoActivo(true);
                                }
                            }

                        } catch (historialErr) {
                            console.error("Error al obtener el historial de papeletas:", historialErr);
                            setUltimoAnioParticipacion("-");
                        }
                    }
                } catch (errActo) {
                    if (errActo.response && errActo.response.status === 404) {
                        if (isMounted) {
                            setActoInfo(null);
                            setModalNoActivo(true);
                        }
                    } else {
                        console.error("Error obteniendo el acto activo:", errActo);
                    }
                }
            } catch (err) {
                console.error(err);
                if (err.response?.status === 401) navigate("/login");
                else setError("Error cargando los datos del servidor.");
            } finally {
                setTimeout(() => {
                    if (isMounted) setLoading(false);
                }, 2000);
            }
        };

        if (id) {
            fetchData();
        }
        return () => { isMounted = false; };
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
            
            setTimeout(() => navigate("/mis-papeletas-de-sitio"), 4000); 

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

    const formatearFechaHora = (dateString) => {
        if (!dateString) return "-";
        const date = new Date(dateString);

        return date.toLocaleString('es-ES', { 
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        }).replaceAll('/', '-');
    };

    if (loading) {
        const loadingText = "Comprobando estado de la solicitud...";
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#FAF9F6' }}>
                <h3 className="loading-animated-text" style={{ color: '#800020' }}>
                    {loadingText.split("").map((char, index) => (
                        <span key={index} style={{ animationDelay: `${index * 0.05}s` }}>
                            {char === " " ? "\u00A0" : char}
                        </span>
                    ))}
                </h3>
            </div>
        );
    }

    return (
        <div>
            {modalBloqueo && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Solicitud ya realizada</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            <p>
                                Ya consta una solicitud activa de papeleta de sitio para el acto <strong>{actoInfo?.nombre}</strong>.
                                <br/><br/>
                                Le recordamos que <strong>no es posible realizar múltiples solicitudes para un mismo acto</strong> (salvo que su solicitud anterior haya sido rechazada o anulada). Si desea hacer cambios, por favor contacte con secretaría.
                            </p>
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {modalFueraPlazoConSolicitud && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Solicitud ya registrada</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            <p>
                                Usted ya realizó una solicitud para el acto <strong>{actoInfo?.nombre}</strong> el día <strong>{formatearFechaHora(fechaSolicitudRealizada)}</strong>.
                                <br/><br/>
                                Actualmente el plazo de modificación o nuevas solicitudes se encuentra cerrado.
                            </p>
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {modalNoActivo && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Plazo cerrado</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            {actoInfo && actoInfo.inicio_solicitud_cirios && actoInfo.fin_solicitud_cirios ? (
                                new Date() < new Date(actoInfo.inicio_solicitud_cirios) ? (
                                    <p>
                                        El plazo para solicitar cirios aún no se encuentra abierto. Comenzará el próximo <strong>{formatearFechaHora(actoInfo.inicio_solicitud_cirios)}</strong>. Por favor, vuelva a intentarlo más adelante.
                                    </p>
                                ) : (
                                    <p>
                                        El plazo para solicitar cirios ya ha concluido (finalizó el <strong>{formatearFechaHora(actoInfo.fin_solicitud_cirios)}</strong>).
                                    </p>
                                )
                            ) : (
                                <p>
                                    Actualmente el plazo para solicitar cirios no se encuentra abierto o ya ha concluido. Por favor, manténgase atento a los comunicados oficiales de la Hermandad.
                                </p>
                            )}
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {!modalBloqueo && !modalNoActivo && !modalFueraPlazoConSolicitud && (
                <>
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
                            <div className="dashboard-panel-solicitud">
                                <div className="historical-header-container-solicitud">
                                    <h1 className="historical-header-title-solicitud">SOLICITUD DE CIRIOS</h1>
                                    <p className="historical-header-subtitle-solicitud">
                                        {getNombreTipoActo(actoInfo?.tipo_acto)} {actoInfo?.fecha ? new Date(actoInfo.fecha).getFullYear() : ""}
                                    </p>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Plazos improrrogables</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="solicitud-cards-container">
                                    <div className="solicitud-card-wrapper">
                                        <div className="solicitud-card-content">
                                            <div className="solicitud-card-icon">
                                                <Flame size={32} strokeWidth={2.5} />
                                            </div>
                                            <h3 className="solicitud-card-title">TIPOS DE CIRIOS</h3>
                                            <p className="solicitud-card-description">
                                                Número total de puestos de cirio configurados para este acto.
                                            </p>
                                            <div className="solicitud-card-date">
                                                {actoInfo?.total_puestos_cirios ?? 0}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="solicitud-card-wrapper">
                                        <div className="solicitud-card-content">
                                            <div className="solicitud-card-icon">
                                                <CalendarCheck size={32} strokeWidth={2.5} />
                                            </div>
                                            <h3 className="solicitud-card-title">INICIO SOLICITUD CIRIOS</h3>
                                            <p className="solicitud-card-description">
                                                Fecha de inicio para la solicitud general de cirios y cruces.
                                            </p>
                                            <div className="solicitud-card-date">
                                                {formatearFechaHora(actoInfo?.inicio_solicitud_cirios)}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="solicitud-card-wrapper">
                                        <div className="solicitud-card-content">
                                            <div className="solicitud-card-icon">
                                                <CalendarX size={32} strokeWidth={2.5} />
                                            </div>
                                            <h3 className="solicitud-card-title">FIN SOLICITUD CIRIOS</h3>
                                            <p className="solicitud-card-description">
                                                Fecha de cierre para la solicitud general de cirios y cruces.
                                            </p>
                                            <div className="solicitud-card-date">
                                                {formatearFechaHora(actoInfo?.fin_solicitud_cirios)}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Formulario de solicitud de cirios</span>
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
                                        <div className="form-row-solicitud">
                                            <div className="form-group-solicitud">
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

                                            <div className="form-group-solicitud">
                                                <label htmlFor="vinculo-input" className="form-label">
                                                    Vincular a otro Hermano (OPCIONAL)
                                                </label>
                                                <div className="input-wrapper">
                                                    <input
                                                        type="number"
                                                        id="vinculo-input"
                                                        className="form-control no-icon"
                                                        placeholder="Indique el número de registro del otro Hermano. Ej: 1358"
                                                        value={numeroVinculado}
                                                        onChange={(e) => setNumeroVinculado(e.target.value)}
                                                        disabled={submitting || success || loading}
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        {user && !user.esta_al_corriente && (
                                            <div className="form-help-text" style={{ color: '#D32F2F', fontWeight: '600', marginBottom: '0px' }}>
                                                * No puedes realizar la solicitud porque tienes cuotas pendientes.
                                            </div>
                                        )}

                                        <button 
                                            type="submit" 
                                            className="submit-btn"
                                            disabled={submitting || success || loading || (user && !user.esta_al_corriente)}
                                        >
                                            {submitting ? 'Procesando...' : (
                                                <>
                                                    <Save size={20} />
                                                    Confirmar la solicitud de cirio
                                                </>
                                            )}
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </section>
                </>
            )}
        </div>
    );
}

export default HermanoCrearSolicitudCirio;