import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import api from "../api";
import "../styles/CrearActo.css"
import logoEscudo from '../assets/escudo.png';

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

    useEffect(() => {
        const token = localStorage.getItem("access");

        if (token) {
            fetch("http://127.0.0.1:8000/api/me/", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                }
            })
            .then(async response => {
                if (response.ok) {
                    const data = await response.json();
                    setUser(data);
                    // Opcional: Redirigir si no es admin en el frontend (aunque el backend protege igual)
                    if (!data.esAdmin) {
                        alert("No tienes permisos de administrador.");
                        navigate("/");
                    }
                } else {
                    localStorage.removeItem("access"); 
                    setUser(null);
                    navigate("/login");
                }
            })
            .catch(error => console.error("Error:", error))
            .finally(() => setLoading(false));
        } else {
            setLoading(false);
            navigate("/login");
        }
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

        const token = localStorage.getItem("access");

        try {
            const response = await fetch("http://127.0.0.1:8000/api/actos/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess(true);
                // Limpiar formulario o redirigir
                setFormData({ nombre: "", tipo_acto: "", fecha: "", descripcion: "" });
                setTimeout(() => navigate("/home"), 2000); // Redirigir a agenda tras 2s
            } else {
                // Manejo de errores de validación (ej: año incorrecto)
                // Django suele devolver errores como { "fecha": ["Error..."] }
                if (data.fecha) setError(data.fecha[0]);
                else if (data.detail) setError(data.detail); // Error de permisos o genérico
                else setError("Error al crear el acto. Revise los datos.");
            }
        } catch (err) {
            setError("Error de conexión con el servidor.");
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

            <div className="admin-layout-acto">
                <main className="main-content-acto">
                    
                    <header className="page-header-acto">
                        <h1 className="page-title-acto">Creación nuevo acto</h1>
                        <p className="page-subtitle-acto">Complete los detalles para programar un nuevo evento. Recuerde que debe ser para el año en curso.</p>
                    </header>

                    {/* Feedback visual de errores o éxito */}
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
                </main>
            </div>
        </div>
    );
}

export default CrearActo;