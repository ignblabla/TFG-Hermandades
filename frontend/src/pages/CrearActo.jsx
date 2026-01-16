import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import api from "../api";
import "../styles/CrearActo.css"
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft } from "lucide-react";

function CrearActo() {
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [tiposActo, setTiposActo] = useState([]);

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [formData, setFormData] = useState({
        nombre: "",
        tipo_acto: "",
        fecha: "",
        descripcion: "",
        inicio_solicitud: "",
        fin_solicitud: "",
        inicio_solicitud_cirios: "",
        fin_solicitud_cirios: ""
    });

    const navigate = useNavigate();

    const now = new Date();
    const minDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    const maxDate = `${now.getFullYear()}-12-31T23:59`;

    useEffect(() => {
        // Carga de Usuario
        const fetchUser = api.get("api/me/");
        // Carga de Tipos de Acto (Nueva llamada)
        const fetchTipos = api.get("api/tipos-acto/");

        Promise.all([fetchUser, fetchTipos])
            .then(([resUser, resTipos]) => {
                const userData = resUser.data;
                setUser(userData);
                if (!userData.esAdmin) {
                    alert("No tienes permisos de administrador.");
                    navigate("/");
                }

                setTiposActo(resTipos.data);
            })
            .catch(error => {
                console.error("Error cargando datos:", error);
                if (error.response && error.response.status === 401) {
                    if (!localStorage.getItem("access")) {
                        navigate("/login");
                    }
                } else {
                    setError("No se pudieron cargar los tipos de actos. Recargue la página.");
                }
            })
            .finally(() => setLoading(false));
    }, [navigate]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const requierePapeleta = () => {
        if (!formData.tipo_acto) return false;
        
        const tipoSeleccionado = tiposActo.find(t => t.tipo === formData.tipo_acto);
        return tipoSeleccionado ? tipoSeleccionado.requiere_papeleta : false;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError("");
        setSuccess(false);

        const payload = {
            ...formData,
            inicio_solicitud: formData.inicio_solicitud || null,
            fin_solicitud: formData.fin_solicitud || null,
            inicio_solicitud_cirios: formData.inicio_solicitud_cirios || null,
            fin_solicitud_cirios: formData.fin_solicitud_cirios || null
        };

        if (requierePapeleta()) {
            if (!payload.inicio_solicitud || !payload.fin_solicitud) {
                setError("Debe indicar las fechas para solicitud de Insignias.");
                setSubmitting(false);
                return;
            }
            
            if (!payload.inicio_solicitud_cirios || !payload.fin_solicitud_cirios) {
                setError("Debe indicar las fechas para solicitud de Cirios.");
                setSubmitting(false);
                return;
            }
            
        }

        try {
            await api.post("api/actos/", payload);

            setSuccess(true);
            setFormData({ 
                nombre: "", tipo_acto: "", fecha: "", descripcion: "", 
                inicio_solicitud: "", fin_solicitud: "" 
            });
            setTimeout(() => navigate("/home"), 2000);

        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                if (data.fecha) setError(`Fecha Acto: ${data.fecha[0]}`);

                else if (data.inicio_solicitud) setError(`Inicio Solicitud: ${data.inicio_solicitud[0]}`);
                else if (data.fin_solicitud) setError(`Fin Solicitud: ${data.fin_solicitud[0]}`);

                else if (data.inicio_solicitud_cirios) setError(`Inicio Cirios: ${data.inicio_solicitud_cirios[0]}`);
                else if (data.fin_solicitud_cirios) setError(`Fin Cirios: ${data.fin_solicitud_cirios[0]}`);

                else if (data.non_field_errors) setError(data.non_field_errors[0]);
                else if (data.detail) setError(data.detail);
                else setError("Error al crear el acto. Revise los datos.");
            } else {
                setError("Error de conexión con el servidor.");
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/"; 
    };

    if (loading) return <div className="site-wrapper">Cargando...</div>;
    if (!user) return <div className="site-wrapper">No has iniciado sesión.</div>;

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

                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
                    ☰
                </button>

                <ul className={`nav-links ${menuOpen ? "active" : ""}`}>
                    <li><a href="#hermandad">Hermandad</a></li>
                    <li><a href="#titulares">Titulares</a></li>
                    <li><a href="#agenda">Agenda</a></li>
                    <li><a href="#lunes-santo">Lunes Santo</a></li>
                    <li><a href="#multimedia">Multimedia</a></li>
                    
                    <div className="nav-buttons-mobile">
                        {user ? (
                            <>
                                <button className="btn-outline">
                                    Hermano: {user.dni}
                                </button>
                                <button className="btn-purple" onClick={handleLogout}>
                                    Cerrar Sesión
                                </button>
                            </>
                        ) : (
                            <>
                                <button className="btn-outline" onClick={() => navigate("/login")}>Acceso Hermano</button>
                                <button className="btn-purple">Hazte Hermano</button>
                            </>
                        )}
                    </div>
                </ul>

                <div className="nav-buttons-desktop">
                    {user ? (
                            <>
                            <button className="btn-outline" onClick={() => navigate("/editar-perfil")} style={{cursor: 'pointer'}}>
                                Hermano: {user.dni}
                            </button>
                            <button className="btn-purple" onClick={handleLogout}>
                                Cerrar Sesión
                            </button>
                            </>
                    ) : (
                        <>
                            <button className="btn-outline" onClick={() => navigate("/login")}>Acceso Hermano</button>
                            <button className="btn-purple">Hazte Hermano</button>
                        </>
                    )}
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area">
                    <header className="content-header-area">
                        <div className="title-row-area">
                        <h1>Creación nuevo acto</h1>
                        <button className="btn-back-area" onClick={() => navigate(-1)}>
                            <ArrowLeft size={16} /> Volver
                        </button>
                    </div>
                    <p className="description-area">
                        Complete los detalles para programar un nuevo evento. Recuerde que debe ser para el año en curso.
                    </p>
                    </header>

                    {error && <div style={{padding: '10px', backgroundColor: '#fee2e2', color: '#dc2626', marginBottom: '1rem', borderRadius: '4px'}}>{error}</div>}
                    {success && <div style={{padding: '10px', backgroundColor: '#dcfce7', color: '#16a34a', marginBottom: '1rem', borderRadius: '4px'}}>¡Acto creado correctamente! Redirigiendo...</div>}

                    <section className="form-card-acto">
                        <form className="event-form-acto" onSubmit={handleSubmit}>
                            
                            {/* CAMPO NOMBRE */}
                            <div className="form-group-acto full-width">
                                <label htmlFor="nombre">NOMBRE DEL ACTO</label>
                                <div className="input-with-icon-acto">
                                    <span className="icon-acto">📅</span>
                                    <input 
                                        type="text" 
                                        id="nombre"
                                        name="nombre" 
                                        required
                                        value={formData.nombre}
                                        onChange={handleChange}
                                        placeholder="Ej: Solemne Quinario..." 
                                    />
                                </div>
                            </div>

                            <div className="form-row-acto">
                                {/* CAMPO TIPO ACTO - AHORA DINÁMICO */}
                                <div className="form-group-acto">
                                    <label htmlFor="tipo_acto">TIPO DE ACTO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">▲</span>
                                        <select 
                                            id="tipo_acto" 
                                            name="tipo_acto"
                                            required
                                            value={formData.tipo_acto}
                                            onChange={handleChange}
                                        >
                                            <option value="" disabled>Seleccione categoría</option>
                                            
                                            {/* MAPEO DINÁMICO DESDE LA BASE DE DATOS */}
                                            {tiposActo.map((tipo) => (
                                                <option key={tipo.id} value={tipo.tipo}>
                                                    {tipo.nombre_mostrar || tipo.tipo}
                                                </option>
                                            ))}
                                            
                                        </select>
                                    </div>
                                </div>

                                {/* CAMPO FECHA */}
                                <div className="form-group-acto">
                                    <label htmlFor="fecha">FECHA Y HORA</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">🕒</span>
                                        <input 
                                            type="datetime-local" 
                                            id="fecha"
                                            name="fecha"
                                            required
                                            min={minDate}
                                            max={maxDate}
                                            value={formData.fecha}
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN CONDICIONAL DINÁMICA */}
                            {requierePapeleta() && (
                                <>
                                    {/* BLOQUE INSIGNIAS */}
                                    <div className="form-row-acto" style={{backgroundColor: '#f9fafb', padding: '15px', borderRadius: '8px', border: '1px solid #e5e7eb', marginBottom: '10px'}}>
                                        <div className="full-width" style={{marginBottom: '10px'}}>
                                            <label style={{fontWeight: 'bold', color: '#4f46e5'}}>1. SOLICITUD DE INSIGNIAS</label>
                                            <p style={{fontSize: '0.85rem', color: '#6b7280', margin: '0'}}>Fechas para solicitud de Varas, Insignias y puestos asignados.</p>
                                        </div>
                                        
                                        <div className="form-group-acto">
                                            <label htmlFor="inicio_solicitud">INICIO (INSIGNIAS)</label>
                                            <div className="input-with-icon-acto">
                                                <span className="icon-acto">🔓</span>
                                                <input 
                                                    type="datetime-local" 
                                                    id="inicio_solicitud"
                                                    name="inicio_solicitud"
                                                    required // Asumo requerido si hay papeleta
                                                    value={formData.inicio_solicitud}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="fin_solicitud">FIN (INSIGNIAS)</label>
                                            <div className="input-with-icon-acto">
                                                <span className="icon-acto">🔒</span>
                                                <input 
                                                    type="datetime-local" 
                                                    id="fin_solicitud"
                                                    name="fin_solicitud"
                                                    required
                                                    value={formData.fin_solicitud}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* BLOQUE CIRIOS / GENERAL */}
                                    <div className="form-row-acto" style={{backgroundColor: '#f3f4f6', padding: '15px', borderRadius: '8px', border: '1px solid #d1d5db', marginBottom: '20px'}}>
                                        <div className="full-width" style={{marginBottom: '10px'}}>
                                            <label style={{fontWeight: 'bold', color: '#059669'}}>2. SOLICITUD DE CIRIOS</label>
                                            <p style={{fontSize: '0.85rem', color: '#6b7280', margin: '0'}}>Fechas para solicitud de papeletas de sitio generales (Cirios).</p>
                                        </div>
                                        
                                        <div className="form-group-acto">
                                            <label htmlFor="inicio_solicitud_cirios">INICIO (CIRIOS)</label>
                                            <div className="input-with-icon-acto">
                                                <span className="icon-acto">🕯️</span>
                                                <input 
                                                    type="datetime-local" 
                                                    id="inicio_solicitud_cirios"
                                                    name="inicio_solicitud_cirios"
                                                    // No pongo 'required' estricto en HTML por si quieres dejarlo vacío, 
                                                    // pero lo lógico sería validarlo.
                                                    value={formData.inicio_solicitud_cirios}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="fin_solicitud_cirios">FIN (CIRIOS)</label>
                                            <div className="input-with-icon-acto">
                                                <span className="icon-acto">🔒</span>
                                                <input 
                                                    type="datetime-local" 
                                                    id="fin_solicitud_cirios"
                                                    name="fin_solicitud_cirios"
                                                    value={formData.fin_solicitud_cirios}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </>
                            )}

                            {/* CAMPO DESCRIPCION */}
                            <div className="form-group-acto full-width">
                                <label htmlFor="descripcion">DESCRIPCIÓN DEL ACTO</label>
                                <textarea 
                                    id="descripcion" 
                                    name="descripcion"
                                    rows="5" 
                                    value={formData.descripcion}
                                    onChange={handleChange}
                                    placeholder="Detalle la información relevante..."
                                ></textarea>
                            </div>

                            <div className="form-actions-acto">
                                <button type="button" className="btn-cancel-acto" onClick={() => navigate("/agenda")}>Cancelar</button>
                                <button type="submit" className="btn-save-acto" disabled={submitting}>
                                    <span className="icon-save-acto">💾</span> {submitting ? "Guardando..." : "Guardar Acto"}
                                </button>
                            </div>
                        </form>
                    </section>
                </div>
            </main>
        </div>
    );
}

export default CrearActo;