import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../AdminCreacionPuesto/AdminCreacionPuesto.css";
import api from '../../api';
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
                
                if (!userData.esAdmin) {
                    alert("No tienes permisos de administrador para gestionar puestos.");
                    navigate("/");
                    return;
                }

                if (isMounted) setUser(userData);

                const [actosRes, tiposRes] = await Promise.all([
                    api.get("/api/actos/"),
                    api.get("/api/tipos-puesto/")
                ]);

                if (isMounted) {
                    const actosArray = Array.isArray(actosRes.data) 
                        ? actosRes.data 
                        : (actosRes.data.results || []);
                        
                    const tiposArray = Array.isArray(tiposRes.data) 
                        ? tiposRes.data 
                        : (tiposRes.data.results || []);

                    const hoy = new Date();
                    hoy.setHours(0, 0, 0, 0);

                    const actosFiltrados = actosArray.filter(acto => {
                        if (!acto.requiere_papeleta) return false;
                        if (!acto.inicio_solicitud) return false;

                        const fechaInicio = new Date(acto.inicio_solicitud);
                        fechaInicio.setHours(0, 0, 0, 0);

                        return fechaInicio >= hoy;
                    });

                    setListaActos(actosFiltrados);
                    setListaTiposPuesto(tiposArray);
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
            setTimeout(() => navigate("/new-home"), 2000);

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

            <section className={`home-section-dashboard-solicitud ${isOpen ? 'sidebar-open' : ''}`}>
                <div className="dashboard-split-layout-solicitud">
                    <div className="dashboard-panel-crear-puesto">
                        <div className="historical-header-container-crear-puesto">
                            <h1 className="historical-header-title-crear-puesto">CREAR PUESTO</h1>
                        </div>

                        <div className="plazos-separator-asignacion">
                            <div className="plazos-line"></div>
                                <span className="plazos-text">Datos generales del puesto</span>
                            <div className="plazos-line"></div>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-container-crear-puesto">

                                <div className="form-grid-4-crear-puesto">
                                    <div className="form-group-crear-puesto span-3-crear-puesto">
                                        <label htmlFor="nombre_puesto" className="form-label-crear-puesto">
                                            Nombre del puesto *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input 
                                                type="text" 
                                                id="nombre_puesto"
                                                name="nombre_puesto" 
                                                value={formData.nombre_puesto} 
                                                onChange={handleChange} 
                                                placeholder="Ej: Diputado Mayor de Gobierno"
                                                required 
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto">
                                        <label htmlFor="cantidad" className="form-label-crear-puesto">
                                            Cantidad *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input 
                                                type="number" 
                                                id="cantidad"
                                                name="cantidad" 
                                                value={formData.cantidad} 
                                                onChange={handleChange}
                                                placeholder="Ej: 1"
                                                min="1"
                                                required
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <div className="checkbox-container-crear-puesto">
                                            <label className="checkbox-label-crear-puesto">
                                                <input 
                                                    type="checkbox" 
                                                    name="disponible" 
                                                    checked={formData.disponible} 
                                                    onChange={handleChange}
                                                    className="checkbox-input-crear-puesto"
                                                />
                                                <div className="checkbox-text-crear-puesto">
                                                    <span className="checkbox-title-crear-puesto">Disponible para asignación</span>
                                                    <span className="checkbox-desc-crear-puesto">Marcar como Disponible para asignación inmediata.</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <div className="checkbox-container-crear-puesto">
                                            <label className="checkbox-label-crear-puesto">
                                                <input 
                                                    type="checkbox" 
                                                    name="cortejo_cristo" 
                                                    checked={formData.cortejo_cristo} 
                                                    onChange={handleChange}
                                                    className="checkbox-input-crear-puesto"
                                                />
                                                <div className="checkbox-text-crear-puesto">
                                                    <span className="checkbox-title-crear-puesto">Sección del Cortejo</span>
                                                    <span className="checkbox-desc-crear-puesto">Márquela si pertenece al cortejo de Cristo. Si pertenece al de Virgen, déjela en blanco.</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text">Detalles del acto y del puesto</span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="form-grid-4-crear-puesto">
                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="acto" className="form-label-crear-puesto">
                                            Acto asociado *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <select
                                                id="acto"
                                                name="acto"
                                                value={formData.acto}
                                                onChange={handleChange}
                                                required
                                                className="form-control-crear-puesto"
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
                                        </div>
                                        <small style={{color: '#666', fontSize: '0.8rem', marginTop: '4px'}}>
                                            Solo actos que requieran papeleta.
                                        </small>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="tipo_puesto" className="form-label-crear-puesto">
                                            Tipo de puesto *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <select
                                                id="tipo_puesto"
                                                name="tipo_puesto"
                                                value={formData.tipo_puesto}
                                                onChange={handleChange}
                                                required
                                                className="form-control-crear-puesto"
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

                                <div className="plazos-separator-asignacion">
                                    <div className="plazos-line"></div>
                                        <span className="plazos-text" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <MapPin size={18} /> Datos de citación
                                        </span>
                                    <div className="plazos-line"></div>
                                </div>

                                <div className="form-grid-4-crear-puesto">
                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="lugar_citacion" className="form-label-crear-puesto">
                                            Lugar de citación *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input
                                                type="text"
                                                id="lugar_citacion"
                                                name="lugar_citacion"
                                                value={formData.lugar_citacion}
                                                onChange={handleChange}
                                                placeholder="Ej: Parroquia de San Gonzalo"
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group-crear-puesto span-2-crear-puesto">
                                        <label htmlFor="hora_citacion" className="form-label-crear-puesto">
                                            Hora de citación *
                                        </label>
                                        <div className="input-wrapper-crear-puesto">
                                            <input
                                                type="time"
                                                id="hora_citacion"
                                                name="hora_citacion"
                                                value={formData.hora_citacion}
                                                onChange={handleChange}
                                                className="form-control-crear-puesto"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="form-actions-crear-puesto">
                                    <button 
                                        type="button" 
                                        className="btn-cancel-crear-puesto" 
                                        onClick={() => navigate("/home")}
                                    >
                                        Cancelar
                                    </button>
                                    
                                    <button 
                                        type="submit" 
                                        className="btn-save-crear-puesto" 
                                        disabled={saving}
                                    >
                                        <Save size={18} />
                                        {saving ? "Guardando..." : "Guardar Puesto"}
                                    </button>
                                </div>
                                
                            </div>
                        </form>
                    </div>
                </div>
            </section>

            {/* <section className="home-section-dashboard">
                <div className="text-dashboard">Crear nuevo puesto</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
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
            </section> */}
        </div>
    )
}

export default AdminCrearPuesto;