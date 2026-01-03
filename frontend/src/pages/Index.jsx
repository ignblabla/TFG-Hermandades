import { useState } from "react";
import "../styles/Index.css";
import logoEscudo from '../assets/escudo.png';

function Index() {
    const [menuOpen, setMenuOpen] = useState(false);

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
        </div>
    );
}
export default Index;