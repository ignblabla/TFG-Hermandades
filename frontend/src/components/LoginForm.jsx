import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import "../styles/LoginForm.css";
import LoadingIndicator from "./LoadingIndicator";
import { FaUser, FaLock, FaIdCard } from "react-icons/fa";
import logoEscudo from "../assets/escudo.png"; 

function LoginForm() {
    const [dni, setDni] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [menuOpen, setMenuOpen] = useState(false);

    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const res = await api.post("/api/token/", { dni, password });
            localStorage.setItem(ACCESS_TOKEN, res.data.access);
            localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
            navigate("/home");
        } catch (error) {
            alert("Error:" + (error.response?.data?.detail || "Error en las credenciales"));
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
                    <div className="card-header-icon"><FaUser /></div>
                    <h2 className="card-title">Acceso a Hermanos</h2>
                    <p className="card-subtitle">Bienvenido al portal del Hermano. Por favor, identifícate.</p>

                    <form onSubmit={handleSubmit}>
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

                        <div className="forgot-password"><a href="#">¿Olvidaste tu contraseña?</a></div>
                        {loading && <LoadingIndicator />}
                        <button type="submit" className="btn-login" disabled={loading}>Iniciar Sesión</button>
                    </form>

                    <div className="card-footer">
                        <p>¿Aún no tienes cuenta? <a href="/register">Solicitar alta</a></p>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default LoginForm;
