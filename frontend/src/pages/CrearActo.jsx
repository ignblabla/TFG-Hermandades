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
                } else {
                    console.log("Token caducado o inválido");
                    localStorage.removeItem("access"); 
                    setUser(null);
                }
            })
            .catch(error => console.error("Error:", error))
            .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

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
                        <p className="page-subtitle-acto">Complete los detalles para programar un nuevo evento en el calendario de la Hermandad.</p>
                    </header>

                    <section className="form-card-acto">
                        <form className="event-form-acto" onSubmit={(e) => e.preventDefault()}>
                            <div className="form-group-acto full-width">
                                <label htmlFor="nombre">NOMBRE DEL ACTO</label>
                                <div className="input-with-icon-acto">
                                    <span className="icon-acto">📅</span>
                                    <input 
                                        type="text" 
                                        id="nombre" 
                                        placeholder="Ej: Solemne Quinario en honor a Nuestro Padre Jesús en Su Soberano Poder ante Caifás" 
                                    />
                                </div>
                            </div>

                            <div className="form-row-acto">
                                <div className="form-group-acto">
                                    <label htmlFor="tipo">TIPO DE ACTO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">▲</span>
                                        <select id="tipo" defaultValue="">
                                            <option value="" disabled>Seleccione categoría</option>
                                            <option value="culto">Culto</option>
                                            <option value="salida">Salida Procesional</option>
                                            <option value="formacion">Formación</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group-acto">
                                    <label htmlFor="fecha">FECHA Y HORA</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">🕒</span>
                                        <input type="datetime-local" id="fecha" />
                                    </div>
                                </div>
                            </div>

                            <div className="form-group-acto full-width">
                                <label htmlFor="descripcion">DESCRIPCIÓN DEL ACTO</label>
                                <textarea 
                                    id="descripcion" 
                                    rows="5" 
                                    placeholder="Detalle la información relevante del acto para los hermanos..."
                                ></textarea>
                            </div>

                            <div className="form-actions-acto">
                                <button type="button" className="btn-cancel-acto">Cancelar</button>
                                <button type="submit" className="btn-save-acto">
                                    <span className="icon-save-acto">💾</span> Guardar Acto
                                </button>
                            </div>
                        </form>
                    </section>

                    <footer className="admin-footer-acto">
                        <div className="footer-content-acto">
                            <span className="footer-logo-acto">📦</span>
                            <span className="footer-text-acto">PANEL ADMINISTRATIVO • SAN GONZALO</span>
                        </div>
                    </footer>
                </main>
            </div>
        </div>
    );
}

export default CrearActo;