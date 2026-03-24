import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";
import '../HermanoSolicitudCirio/HermanoCrearSolicitudCirio.css'
import HomeCard from "../../components/HomeCard";
// Importamos los nuevos iconos necesarios
import { Medal, CreditCard, Bookmark, ListOrdered, History, FileText, AlertCircle, CheckCircle, Save } from "lucide-react";

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

            <section className="home-section-dashboard">
                <div className="text-dashboard">
                    {"Solicitud de cirios"}
                </div>

                <div className="home-cards-container">
                    <HomeCard 
                        icon={ListOrdered}
                        title="Número de registro" 
                        value={user?.numero_registro || "-"}
                    />

                    <HomeCard
                        icon={Medal}
                        title="Años de antigüedad" 
                        value={user?.antiguedad_anios ?? "-"} 
                    />
                    
                    <HomeCard
                        icon={CreditCard}
                        title="Cuotas Pendientes" 
                        value={
                            user?.historial_cuotas
                                ? user.historial_cuotas.filter(
                                    (cuota) => cuota.estado === 'PENDIENTE' || cuota.estado === 'DEVUELTA'
                                ).length
                                : 0
                        } 
                    />

                    <HomeCard
                        icon={History} 
                        title={getHistoryTitle(actoInfo?.tipo_acto)} 
                        value={ultimoAnioParticipacion} 
                    />
                </div>
                    
                    <div className="solicitud-cirio-boxes-wrapper">
                        <div 
                            className="solicitud-cirio-half-box image-bg-box"
                            style={{
                                backgroundImage: actoInfo?.imagen_portada 
                                    ? `url(${actoInfo.imagen_portada})` 
                                    : 'none',
                                backgroundColor: actoInfo?.imagen_portada 
                                    ? 'transparent' 
                                    : '#800020'
                            }}
                        >
                            <div className="title-blur-wrapper">
                                <h3 className="section-title-solicitud-cirio white-text">
                                    {actoInfo ? actoInfo.nombre : "Información Adicional"}
                                </h3>
                            </div>
                        </div>

                        <div className="solicitud-cirio-half-box">
                            <form onSubmit={handleSubmit}>
                                
                                <h3 className="section-title-solicitud-cirio">
                                    <FileText size={18} /> Datos de Solicitud
                                </h3>
                                
                                {error && (
                                    <div style={{ 
                                        backgroundColor: '#fee2e2', 
                                        color: '#dc2626', 
                                        padding: '15px', 
                                        borderRadius: '8px', 
                                        marginBottom: '20px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '10px'
                                    }}>
                                        <AlertCircle size={20} />
                                        <div>{error}</div>
                                    </div>
                                )}

                                {success && (
                                    <div style={{ 
                                        backgroundColor: '#dcfce3', 
                                        color: '#16a34a', 
                                        padding: '15px', 
                                        borderRadius: '8px', 
                                        marginBottom: '20px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '10px'
                                    }}>
                                        <CheckCircle size={20} />
                                        <div>Solicitud completada con éxito. Redirigiendo a mis papeletas...</div>
                                    </div>
                                )}

                                <div className="form-group-solicitud-cirio">
                                    <label htmlFor="puesto">Puesto a solicitar</label>
                                    <select 
                                        id="puesto"
                                        className="form-input-solicitud-cirio"
                                        value={selectedPuestoId}
                                        onChange={(e) => setSelectedPuestoId(e.target.value)}
                                        required
                                        disabled={submitting || success || puestosCirio.length === 0}
                                    >
                                        <option value="" disabled>-- Seleccione un puesto --</option>
                                        {puestosCirio.map((puesto) => (
                                            <option key={puesto.id} value={puesto.id}>
                                                {puesto.nombre}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="form-group-solicitud-cirio">
                                    <label htmlFor="numeroVinculado">Vincular con Hermano (Nº Registro)</label>
                                    <input 
                                        type="number" 
                                        id="numeroVinculado"
                                        className="form-input-solicitud-cirio"
                                        value={numeroVinculado}
                                        onChange={(e) => setNumeroVinculado(e.target.value)}
                                        placeholder="Ej: 1234"
                                        disabled={submitting || success}
                                    />
                                    <small className="form-help-text-solicitud-cirio">
                                        Opcional. Introduzca el número de registro del hermano con el que desea procesionar. Tenga en cuenta que se adoptará la antigüedad del hermano más reciente.
                                    </small>
                                </div>

                                <div className="form-actions-solicitud-cirio">
                                    <button 
                                        type="button" 
                                        className="btn-cancel-solicitud-cirio" 
                                        onClick={() => navigate("/mis-papeletas")}
                                    >
                                        Cancelar
                                    </button>
                                    
                                    <button 
                                        type="submit" 
                                        className="btn-save-solicitud-cirio" 
                                        disabled={submitting || !selectedPuestoId || success}
                                    >
                                        <Save size={18} />
                                        {submitting ? "Procesando..." : "Solicitar Papeleta"}
                                    </button>
                                </div>

                            </form>
                        </div>
                    </div>
            </section>
        </div>
    );
}

export default HermanoCrearSolicitudCirio;