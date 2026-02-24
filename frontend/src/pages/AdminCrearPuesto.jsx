import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/AdminCreacionPuesto.css";
import api from '../api';
import { ArrowLeft, FileText, MapPin, FolderDot, Save, AlertCircle, CheckCircle } from "lucide-react";


function AdminCrearPuesto() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isOpen, setIsOpen] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);

    const [listaActos, setListaActos] = useState([]);
    const [listaTiposPuesto, setListaTiposPuesto] = useState([]);

    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);
    const [successMsg, setSuccessMsg] = useState("");

    // Form Data inicial
    const [formData, setFormData] = useState({
        nombre: "",
        numero_maximo_asignaciones: 1,
        acto: "",
        tipo_puesto: "",
        lugar_citacion: "",
        hora_citacion: "",
        disponible: true,
        cortejo_cristo: true
    });

    const navigate = useNavigate();

    const formatearNombre = (texto) => {
        if (!texto) return "";
        return texto
            .replace(/_/g, " ")
            .toLowerCase()
            .replace(/\b\w/g, (char) => char.toUpperCase());
    };

    const toggleSidebar = () => setIsOpen(!isOpen);

    useEffect(() => {
        const token = localStorage.getItem("access");

        if (!token) {
            setLoading(false);
            navigate("/login");
            return;
        }

        const fetchData = async () => {
            try {
                const userRes = await api.get("/api/me/");
                const userData = userRes.data;
                
                if (!userData.esAdmin) {
                    alert("No tienes permisos de administrador para gestionar puestos.");
                    navigate("/");
                    return;
                }
                setUser(userData);

                const [actosRes, tiposRes] = await Promise.all([
                    api.get("/api/actos/"),
                    api.get("/api/tipos-puesto/")
                ]);

                const actosFiltrados = actosRes.data.filter(acto => acto.requiere_papeleta === true);
                setListaActos(actosFiltrados);
                setListaTiposPuesto(tiposRes.data);

            } catch (err) {
                console.error("Error cargando datos:", err);

                localStorage.removeItem("access"); 
                navigate("/login");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate]);

    // --- MANEJADORES ---

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        try {
            const payload = {
                ...formData,
                acto: parseInt(formData.acto, 10),
                tipo_puesto: formData.tipo_puesto,
                numero_maximo_asignaciones: parseInt(formData.numero_maximo_asignaciones, 10),
                hora_citacion: formData.hora_citacion ? formData.hora_citacion : null,
                lugar_citacion: formData.lugar_citacion ? formData.lugar_citacion : null
            };
            
            const response = await api.post("/api/puestos/", payload);

            setSuccessMsg("Puesto creado con éxito");
            setTimeout(() => navigate("/home"), 2000);

        } catch (err) {
            console.error(err);

            if (err.response && err.response.data) {
                const data = err.response.data;

                if (data.acto) {
                    const msg = Array.isArray(data.acto) ? data.acto[0] : data.acto;
                    setError(`⚠️ ${msg}`); 
                } 
                else if (data.hora_citacion) {
                    const msg = Array.isArray(data.hora_citacion) ? data.hora_citacion[0] : data.hora_citacion;
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
                    setError(`Error en ${firstKey}: ${msgTexto}`);
                }
            } else {
                setError("Error de conexión con el servidor. Inténtelo más tarde.");
            }
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

            <section className="home-section-dashboard">
                <div className="text-dashboard">Crear nuevo puesto</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        {/* BANNER DE ERRORES/EXITO */}
                        {error && (
                            <div className="alert-banner-creacion-puesto error-creacion-puesto">
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-creacion-puesto success-creacion-puesto">
                                <CheckCircle size={20} />
                                <span>{successMsg}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            <div className="form-section-creacion-puesto">
                                <h3 className="section-title-creacion-puesto"><FileText size={18}/> Datos del puesto</h3>

                                <div className="form-grid-creacion-puesto">
                                    <div className="form-group-creacion-puesto span-2-main-puesto">
                                        <label>Nombre del puesto *</label>
                                        <input
                                            type="text"
                                            id="nombre"
                                            name="nombre"
                                            value={formData.nombre}
                                            onChange={handleChange}
                                            placeholder="Ej: Vara Senatus, Guión Sacramental..."
                                            required
                                        />
                                    </div>

                                    <div className="form-group-creacion-puesto span-2-main-puesto">
                                        <label>Cantidad *</label>
                                        <input
                                            type="number"
                                            id="numero_maximo_asignaciones"
                                            name="numero_maximo_asignaciones"
                                            min="1"
                                            value={formData.numero_maximo_asignaciones}
                                            onChange={handleChange}
                                            required
                                        />
                                    </div>

                                    <div className="form-group-creacion-puesto full-width">
                                        <label className="checkbox-label-puesto">
                                            <input 
                                                type="checkbox" 
                                                name="disponible" 
                                                checked={formData.disponible} 
                                                onChange={handleChange}
                                                className="checkbox-input-puesto"
                                            />
                                            <div className="checkbox-text-puesto">
                                                <span className="checkbox-title-puesto">Disponible para asignación</span>
                                                <span className="checkbox-desc-puesto">Marcar como Disponible para asignación inmediata.</span>
                                            </div>
                                        </label>
                                    </div>

                                    <div className="form-group-creacion-puesto full-width">
                                        <label className="checkbox-label-puesto">
                                            <input 
                                                type="checkbox" 
                                                name="cortejo_cristo" 
                                                checked={formData.cortejo_cristo} 
                                                onChange={handleChange}
                                                className="checkbox-input-puesto"
                                            />
                                            <div className="checkbox-text-puesto">
                                                <span className="checkbox-title-puesto">Sección del Cortejo</span>
                                                <span className="checkbox-desc-puesto">Márquela si pertenece al cortejo de Cristo. Si pertenece al de Virgen, déjela en blanco.</span>
                                            </div>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-creacion-puesto">
                                <h3 className="section-title-creacion-puesto"><FolderDot size={18}/> Detalles del acto y del puesto</h3>

                                <div className="form-grid-creacion-puesto">
                                    <div className="form-group-creacion-puesto span-2-main-puesto">
                                        <label>Acto asociado *</label>
                                        <select
                                            id="acto"
                                            name="acto"
                                            value={formData.acto}
                                            onChange={handleChange}
                                            required
                                        >
                                            <option value="" disabled>Seleccione un acto</option>
                                            {listaActos.map(acto => (
                                                <option key={acto.id} value={acto.id}>
                                                    {acto.nombre} ({new Date(acto.fecha).toLocaleDateString()})
                                                </option>
                                            ))}
                                            {listaActos.length === 0 && (
                                                <option disabled>No hay actos que requieran papeleta.</option>
                                            )}
                                        </select>
                                        <small style={{color: '#666', fontSize: '0.8rem'}}>Solo actos que requieran papeleta.</small>
                                    </div>

                                    <div className="form-group-creacion-puesto span-2-main-puesto">
                                        <label>Tipo de puesto *</label>
                                        <select
                                            id="tipo_puesto"
                                            name="tipo_puesto"
                                            value={formData.tipo_puesto}
                                            onChange={handleChange}
                                            required
                                        >
                                            <option value="" disabled>Seleccione Categoría</option>
                                            {listaTiposPuesto.map(tipo => (
                                                <option key={tipo.id} value={tipo.nombre_tipo}>
                                                    {formatearNombre(tipo.nombre_tipo)} {tipo.solo_junta_gobierno ? '(Solo Junta)' : ''}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-creacion-puesto">
                                <h3 className="section-title-creacion-puesto"><MapPin size={18}/> Datos de citación</h3>
                                <div className="form-grid-creacion-puesto">
                                    <div className="form-group-creacion-puesto span-2-main-puesto">
                                        <label>Lugar de citación *</label>
                                        <input
                                            type="text"
                                            id="lugar_citacion"
                                            name="lugar_citacion"
                                            value={formData.lugar_citacion}
                                            onChange={handleChange}
                                            placeholder="Ej: Parroquia de San Gonzalo"
                                        />
                                    </div>

                                    <div className="form-group-creacion-puesto span-2-main-puesto">
                                        <label>Hora de citación *</label>
                                        <input
                                            type="time"
                                            id="hora_citacion"
                                            name="hora_citacion"
                                            value={formData.hora_citacion}
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="form-actions-edicion">
                                <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/home")}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn-save-edicion" disabled={saving}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Save size={18} />
                                        {saving ? "Creando..." : "Crear Puesto"}
                                    </div>
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    )
}

export default AdminCrearPuesto;