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

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [formData, setFormData] = useState({
        nombre: "",
        tipo_acto: "",
        fecha: "",
        descripcion: ""
    });

    const navigate = useNavigate();

    const now = new Date();
    const minDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    const maxDate = `${now.getFullYear()}-12-31T23:59`;

    useEffect(() => {
        api.get("api/me/")
            .then(response => {
                const data = response.data;
                setUser(data);
                if (!data.esAdmin) {
                    alert("No tienes permisos de administrador.");
                    navigate("/");
                }
            })
            .catch(error => {
                console.error("Error cargando usuario:", error);
                if (!localStorage.getItem("access")) {
                    navigate("/login");
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

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError("");
        setSuccess(false);

        try {
            await api.post("api/actos/", formData);

            setSuccess(true);
            setFormData({ nombre: "", tipo_acto: "", fecha: "", descripcion: "" });
            setTimeout(() => navigate("/home"), 2000);

        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                if (data.fecha) setError(data.fecha[0]);
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
                                {/* CAMPO TIPO ACTO */}
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
                                            <option value="ESTACION_PENITENCIA">Estación de Penitencia</option>
                                            <option value="VIA_CRUCIS">Vía Crucis</option>
                                            <option value="QUINARIO">Quinario</option>
                                            <option value="TRIDUO">Triduo</option>
                                            <option value="ROSARIO_AURORA">Rosario de la Aurora</option>
                                            <option value="CABILDO_GENERAL">Cabildo General</option>
                                            <option value="CABILDO_EXTRAORDINARIO">Cabildo Extraordinario</option>
                                            <option value="CONVIVENCIA">Convivencia</option>
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