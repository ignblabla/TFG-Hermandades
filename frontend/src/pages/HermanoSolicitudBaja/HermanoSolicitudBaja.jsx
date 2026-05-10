import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from '../../api';
import '../HermanoSolicitudBaja/HermanoSolicitudBaja.css'
import { Save, AlertCircle, CheckCircle, FileText, Timer, ClipboardList, CreditCard } from "lucide-react";

function HermanoSolicitudBaja() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isOpen, setIsOpen] = useState(false);

    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);
    const [successMsg, setSuccessMsg] = useState("");
    const [cuotasPendientes, setCuotasPendientes] = useState(0);

    const [formData, setFormData] = useState({
        motivo: ""
    });

    const navigate = useNavigate();

    const toggleSidebar = () => setIsOpen(!isOpen);

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("access");

        if (!token) {
            if (isMounted) setLoading(false);
            navigate("/login");
            return;
        }

        const fetchData = async () => {
            try {
                const userRes = await api.get("/api/me/");
                const userData = userRes.data;

                if (userData.estado_hermano !== 'ALTA') {
                    alert("Solo los hermanos en estado de ALTA pueden solicitar la baja de la Hermandad.");
                    navigate("/");
                    return;
                }

                const cuotasTotalRes = await api.get("/api/mis-cuotas-pendientes/total/");

                if (isMounted) {
                    setUser(userData);
                    setCuotasPendientes(cuotasTotalRes.data.total_pendientes ?? 0);
                }

            } catch (err) {
                console.error("Error cargando datos:", err);

                if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                    localStorage.removeItem("access"); 
                    navigate("/login");
                } else {
                    if (isMounted) setError("Error de conexión al cargar los datos iniciales. Inténtelo de nuevo más tarde.");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        
        return () => { isMounted = false; };
    }, [navigate]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        try {
            const payload = {
                motivo: formData.motivo
            };

            await api.post("/api/solicitudes-baja/", payload);

            setSuccessMsg("Solicitud de baja enviada con éxito. La Secretaría revisará su petición.");
            setTimeout(() => navigate("/new-home"), 3000);

        } catch (err) {
            console.error(err);

            if (err.response && err.response.data) {
                const data = err.response.data;

                if (data.error) {
                    const msg = Array.isArray(data.error) ? data.error[0] : data.error;
                    setError(`⚠️ ${msg}`);
                } 
                else if (data.detail) {
                    setError(data.detail);
                }
                else if (data.non_field_errors) {
                    setError(data.non_field_errors[0]);
                }
                else {
                    const firstKey = Object.keys(data)[0];
                    const firstMsg = data[firstKey];
                    const msgTexto = Array.isArray(firstMsg) ? firstMsg[0] : firstMsg;
                    setError(`Error: ${msgTexto}`);
                }
            } else {
                setError("Error de conexión con el servidor. Inténtelo más tarde.");
            }

            setTimeout(() => setError(""), 3000);

        } finally {
            setSaving(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/";
    };

    const handleVincularTelegram = (e) => {
        e.preventDefault();

        if (user && user.enlace_vinculacion_telegram) {
            window.open(user.enlace_vinculacion_telegram, '_blank');
        } else {
            console.error("El enlace de Telegram no está disponible.");
            alert("Hubo un problema al cargar tu enlace personal de Telegram.");
        }
    };

    if (loading) return <div className="site-wrapper">Cargando...</div>;
    if (!user) return null;

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
                            onClick={!user?.telegram_chat_id ? handleVincularTelegram : (e) => e.preventDefault()}
                            style={{ 
                                cursor: user?.telegram_chat_id ? 'default' : 'pointer',
                                opacity: user?.telegram_chat_id ? 0.6 : 1
                            }}
                        >
                            <i className="bx bxl-telegram"></i>
                            <span className="link_name-dashboard">
                                {user?.telegram_chat_id ? "Telegram Vinculado ✅" : "Vincular Telegram"}
                            </span>
                        </a>
                        <span className="tooltip-dashboard">
                            {user?.telegram_chat_id ? "Ya vinculado" : "Vincular Telegram"}
                        </span>
                    </li>
                    {user?.esAdmin && (
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
                    <div className="dashboard-panel-baja">
                        <div className="historical-header-container-baja">
                            <h1 className="historical-header-title-baja">SOLICITUD DE BAJA DE HERMANO</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Datos generales del Hermano</span>
                            <div className="plazos-line"></div>
                        </div>

                        <div className="baja-cards-container">
                            <div className="baja-card-wrapper">
                                <div className="baja-card-content">
                                    <div className="baja-card-icon">
                                        <Timer size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="baja-card-title">AÑOS DE ANTIGÜEDAD</h3>
                                    <p className="baja-card-description">
                                        Número total de años transcurridos desde tu fecha de ingreso oficial en la corporación.
                                    </p>
                                    <div className="baja-card-date">
                                        {user?.antiguedad_anios ?? "-"}
                                    </div>
                                </div>
                            </div>

                            <div className="baja-card-wrapper">
                                <div className="baja-card-content">
                                    <div className="baja-card-icon">
                                        <ClipboardList size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="baja-card-title">NÚMERO DE REGISTRO</h3>
                                    <p className="baja-card-description">
                                        Identificador numérico único asignado a tu ficha personal en el censo oficial de la Hermandad.
                                    </p>
                                    <div className="baja-card-date">
                                        {user?.numero_registro ?? "-"}
                                    </div>
                                </div>
                            </div>

                            <div className="baja-card-wrapper">
                                <div className="baja-card-content">
                                    <div className="baja-card-icon">
                                        <CreditCard size={32} strokeWidth={2.5} />
                                    </div>
                                    <h3 className="baja-card-title">CUOTAS PENDIENTES</h3>
                                    <p className="baja-card-description">
                                        Número total de cuotas pendientes que constan actualmente en tu historial.
                                    </p>
                                    <div className="baja-card-date">
                                        {cuotasPendientes ?? "-"}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Formulario para solicitar la baja de Hermano</span>
                            <div className="plazos-line"></div>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="solicitud-form-container">
                                <div className="form-group-crear-baja span-full-crear-baja">
                                    <label htmlFor="motivo" className="form-label-crear-baja">
                                        Motivo de la baja (Opcional)
                                    </label>
                                    <div className="input-wrapper-crear-baja">
                                        <textarea 
                                            id="motivo"
                                            name="motivo" 
                                            value={formData.motivo} 
                                            onChange={handleChange} 
                                            placeholder="Si lo desea, puede indicarnos el motivo por el cual solicita la baja."
                                            rows="5"
                                            className="form-control-crear-baja"
                                        />
                                    </div>
                                </div>

                                <div className="toast-container-crear-comunicado">
                                    {successMsg && (
                                        <div className="toast-message-crear-comunicado toast-success-crear-comunicado">
                                            <CheckCircle size={24} />
                                            <span>{successMsg}</span>
                                        </div>
                                    )}
                                    {error && (
                                        <div className="toast-message-crear-comunicado toast-error-crear-comunicado">
                                            <AlertCircle size={24} />
                                            <span>{error}</span>
                                        </div>
                                    )}
                                </div>

                                <div className="form-actions-crear-baja">
                                    <button 
                                        type="button" 
                                        className="btn-cancel-crear-baja" 
                                        onClick={() => navigate("/editar-mi-perfil")}
                                    >
                                        Cancelar
                                    </button>
                                    
                                    <button 
                                        type="submit" 
                                        className="btn-save-crear-baja" 
                                        disabled={saving}
                                    >
                                        <Save size={18} />
                                        {saving ? "Creando..." : "Crear solicitud de baja"}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default HermanoSolicitudBaja;