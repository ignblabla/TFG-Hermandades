import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/SideBarMenu.css';

function SideBarMenu({ isOpen, toggleSidebar, user, handleLogout }) {
    return (
        <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
            <div className="logo_details-dashboard">
                <i className="bx bxl-audible icon-dashboard"></i>
                <div className="logo_name-dashboard">San Gonzalo</div>
                <i 
                    className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} 
                    id="btn" 
                    onClick={toggleSidebar}
                    style={{cursor: 'pointer'}}
                ></i>
            </div>
            <ul className="nav-list-dashboard">
                <li>
                    <i className="bx bx-search" onClick={toggleSidebar}></i>
                    <input type="text" placeholder="Buscar..." />
                    <span className="tooltip-dashboard">Buscar</span>
                </li>
                
                {/* --- ENLACES DE NAVEGACIÓN --- */}
                
                <li>
                    <Link to="/panel-administracion">
                        <i className="bx bx-grid-alt"></i>
                        <span className="link_name-dashboard">Dashboard</span>
                    </Link>
                    <span className="tooltip-dashboard">Dashboard</span>
                </li>

                <li>
                    <Link to="/admin/censo">
                        <i className="bx bx-user"></i>
                        <span className="link_name-dashboard">Usuarios</span>
                    </Link>
                    <span className="tooltip-dashboard">Usuarios</span>
                </li>

                <li>
                    <a href="#">
                        <i className="bx bx-chat"></i>
                        <span className="link_name-dashboard">Mensajes</span>
                    </a>
                    <span className="tooltip-dashboard">Mensajes</span>
                </li>
                <li>
                    <a href="#">
                        <i className="bx bx-pie-chart-alt-2"></i>
                        <span className="link_name-dashboard">Analíticas</span>
                    </a>
                    <span className="tooltip-dashboard">Analíticas</span>
                </li>
                <li>
                    <a href="#">
                        <i className="bx bx-folder"></i>
                        <span className="link_name-dashboard">Archivos</span>
                    </a>
                    <span className="tooltip-dashboard">Archivos</span>
                </li>
                <li>
                    <a href="#">
                        <i className="bx bx-cart-alt"></i>
                        <span className="link_name-dashboard">Pedidos</span>
                    </a>
                    <span className="tooltip-dashboard">Pedidos</span>
                </li>
                <li>
                    <a href="#">
                        <i className="bx bx-cog"></i>
                        <span className="link_name-dashboard">Configuración</span>
                    </a>
                    <span className="tooltip-dashboard">Configuración</span>
                </li>
                
                {/* --- PERFIL DE USUARIO --- */}
                <li className="profile-dashboard">
                    <div className="profile_details-dashboard">
                        <img src="/profile.jpeg" alt="profile" onError={(e) => e.target.style.display = 'none'} /> 
                        <div className="profile_content-dashboard">
                            <div className="name-dashboard">
                                {user ? `${user.nombre} ${user.primer_apellido}` : "Usuario"}
                            </div>
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
    );
}

export default SideBarMenu;