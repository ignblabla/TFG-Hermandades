import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import Note from "../components/Note"
import "../styles/Home.css"
import logoEscudo from '../assets/escudo.png';

function Home() {
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");

        if (usuarioGuardado) {
            setUser(JSON.parse(usuarioGuardado));
        }
    }, []);

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
            .catch(error => console.error("Error:", error));
        }
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/"; 
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
                            <button className="btn-outline" style={{cursor: 'default'}}>
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

            <main className="profile-section-home">
                <nav className="breadcrumb-home">
                    Inicio <span> &gt; </span> <span className="active-path-home">Mi Perfil</span>
                </nav>

                <div className="profile-header-home">
                    <h1>Mi Perfil de Hermano</h1>
                    <p>Gestione su información personal y su vinculación con la hermandad.</p>
                </div>

                <div className="profile-card-home">
                    <div className="profile-info-left-home">
                        <div className="avatar-container-home">
                            <img src={logoEscudo} alt="Avatar" className="profile-avatar-home" />
                            <button className="edit-avatar-btn-home">✎</button>
                        </div>

                        <div className="user-data-home">
                            <h2>{user ? `${user.nombre} ${user.primer_apellido}` : "Francisco Javier Pérez"}</h2>
                            <div className="badge-container-home">
                                <span className="badge-home">Hermano Nº {user?.numero_hermano || "1402"}</span>
                                <span className="badge-home">Antigüedad: 15 años</span>
                                <span className="status-badge-home">
                                    <span className="dot-home">●</span> Cuotas al día
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="profile-info-right-home">
                        <button className="btn-digital-card-home">
                            <span className="icon-card-home">🪪</span> Tarjeta Digital
                        </button>
                    </div>
                </div>

                <div className="profile-details-grid-home">
                    <div className="details-card-home">
                        <div className="details-card-header-home">
                            <div className="header-title-home">
                                <span className="header-icon-home purple-bg">🪪</span>
                                <h3>Información Personal</h3>
                            </div>
                            <button className="edit-link-home">Editar</button>
                        </div>

                        <div className="details-form-home">
                            <div className="form-group-home full-width">
                                <label>NOMBRE COMPLETO</label>
                                <input type="text" readOnly value={user ? `${user.nombre} ${user.primer_apellido}` : "Francisco Javier Pérez González"} />
                            </div>

                            <div className="form-row-home">
                                <div className="form-group-home">
                                    <label>DNI / NIF</label>
                                    <input type="text" readOnly value={user?.dni || "12345678X"} />
                                </div>
                                <div className="form-group-home">
                                    <label>FECHA DE NACIMIENTO</label>
                                    <input type="text" readOnly value="04/12/1985" />
                                </div>
                            </div>

                            <div className="form-row-home">
                                <div className="form-group-home">
                                    <label>GÉNERO</label>
                                    <div className="select-container-home">
                                        <select disabled>
                                            <option>Masculino</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="form-group-home">
                                    <label>ESTADO CIVIL</label>
                                    <div className="select-container-home">
                                        <select disabled>
                                            <option>Casado/a</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="details-card-home">
                        <div className="details-card-header-home">
                            <div className="header-title-home">
                                <span className="header-icon-home purple-bg">📍</span>
                                <h3>Datos de Contacto</h3>
                            </div>
                            <button className="edit-link-home">Editar</button>
                        </div>

                        <div className="details-form-home">
                            <div className="form-group-home full-width">
                                <label>DIRECCIÓN POSTAL</label>
                                <input type="text" readOnly value="C/ Pureza, 14, 2ºA" />
                            </div>
                            <div className="form-row-home">
                                <div className="form-group-home">
                                    <label>CÓDIGO POSTAL</label>
                                    <input type="text" readOnly value="41010" />
                                </div>
                                <div className="form-group-home">
                                    <label>LOCALIDAD</label>
                                    <input type="text" readOnly value="Sevilla" />
                                </div>
                            </div>

                            <div className="form-group-home full-width">
                                <label>TELÉFONO</label>
                                <div className="input-with-icon-home">
                                    <span className="input-icon-home">📞</span>
                                    <input type="text" readOnly value="600 123 456" />
                                </div>
                            </div>

                            <div className="form-group-home full-width">
                                <label>CORREO ELECTRÓNICO</label>
                                <div className="input-with-icon-home">
                                    <span className="input-icon-home">📧</span>
                                    <input type="text" readOnly value={user?.email || "fran.perez@email.com"} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Home;