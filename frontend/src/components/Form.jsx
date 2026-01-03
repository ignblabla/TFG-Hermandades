import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import "../styles/Form.css";
import LoadingIndicator from "./LoadingIndicator";
import { FaUser, FaLock, FaIdCard } from "react-icons/fa";
import logoEscudo from "../assets/escudo.png"; 

function Form({ route, method }) {
    const [dni, setDni] = useState("");
    const [password, setPassword] = useState("");
    const [nombre, setNombre] = useState("");
    const [primerApellido, setPrimerApellido] = useState("");
    const [segundoApellido, setSegundoApellido] = useState("");
    
    const [loading, setLoading] = useState(false);
    const [menuOpen, setMenuOpen] = useState(false);
    
    const navigate = useNavigate();

    const isLogin = method === "login";
    const title = isLogin ? "Acceso de Hermanos" : "Registro de Hermano";

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const data = isLogin 
            ? { dni, password } 
            : { 
                dni, 
                password, 
                nombre, 
                primer_apellido: primerApellido, 
                segundo_apellido: segundoApellido 
            };

        try {
            const res = await api.post(route, data);
            if (isLogin) {
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
                navigate("/");
            } else {
                navigate("/login");
            }
        } catch (error) {
            const errorMsg = error.response?.data?.dni 
                ? "Este DNI ya está registrado." 
                : (error.response?.data?.detail || "Error en los datos introducidos");
            alert("Error: " + errorMsg);
        } finally {
            setLoading(false);
        }
    };

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

                {/* Botón para móviles */}
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
                        <button className="btn-outline">Acceso Hermano</button>
                        <button className="btn-purple">Hazte Hermano</button>
                    </div>
                </ul>

                <div className="nav-buttons-desktop">
                    <button className="btn-outline">Acceso Hermano</button>
                    <button className="btn-purple">Hazte Hermano</button>
                </div>
            </nav>

            <main className="content-wrapper">
                <div className="login-card">
                    <div className="card-header-icon">
                        <FaUser />
                    </div>

                    <h2 className="card-title">{title}</h2>
                    <p className="card-subtitle">
                        {isLogin 
                            ? "Bienvenido al portal del hermano. Por favor, identifícate." 
                            : "Completa los datos para darte de alta en la Hermandad."}
                    </p>

                    <form onSubmit={handleSubmit}>
                        {/* Campo DNI - Siempre visible */}
                        <div className="input-group">
                            <label htmlFor="dni">DNI / NIE</label>
                            <div className="input-wrapper">
                                <FaIdCard className="input-icon" />
                                <input
                                    id="dni"
                                    type="text"
                                    value={dni}
                                    onChange={(e) => setDni(e.target.value.toUpperCase())}
                                    placeholder="12345678X"
                                    required
                                />
                            </div>
                        </div>

                        {/* Campos adicionales solo para Registro */}
                        {!isLogin && (
                            <>
                                <div className="input-group">
                                    <label>Nombre</label>
                                    <input
                                        type="text"
                                        value={nombre}
                                        onChange={(e) => setNombre(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="input-group">
                                    <label>Primer Apellido</label>
                                    <input
                                        type="text"
                                        value={primerApellido}
                                        onChange={(e) => setPrimerApellido(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="input-group">
                                    <label>Segundo Apellido</label>
                                    <input
                                        type="text"
                                        value={segundoApellido}
                                        onChange={(e) => setSegundoApellido(e.target.value)}
                                        required
                                    />
                                </div>
                            </>
                        )}

                        <div className="input-group">
                            <label htmlFor="password">Contraseña</label>
                            <div className="input-wrapper">
                                <FaLock className="input-icon" />
                                <input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="********"
                                    required
                                />
                            </div>
                        </div>

                        {isLogin && (
                            <div className="forgot-password">
                                <a href="#">¿Olvidaste tu contraseña?</a>
                            </div>
                        )}

                        {loading && <LoadingIndicator />}
                        
                        <button type="submit" className="btn-login" disabled={loading}>
                            {isLogin ? "Iniciar Sesión" : "Registrarse"}
                        </button>
                    </form>

                    <div className="card-footer">
                        <p>
                            {isLogin ? (
                                <>¿Aún no tienes cuenta? <a href="/register">Solicitar alta</a></>
                            ) : (
                                <>¿Ya tienes cuenta? <a href="/login">Inicia sesión aquí</a></>
                            )}
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Form;