import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../api';
import '../../styles/Admin/Dashboard.css';
import { DashboardStats } from '../../components/AdminDashboard/DashboardCard';

import SideBarMenu from '../../components/SideBarMenu';

function AdminDashboard() {
    const [isOpen, setIsOpen] = useState(false);
    
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const navigate = useNavigate();

    useEffect(() => {
        api.get("api/me/")
            .then((res) => {
                const userData = res.data;
                
                if (!userData.esAdmin) {
                    alert("No tienes permisos de administrador para acceder a este panel.");
                    navigate("/");
                } else {
                    setUser(userData);
                }
            })
            .catch((error) => {
                console.error("Error cargando datos de usuario:", error);
                if (error.response && error.response.status === 401) {
                    navigate("/login");
                } else {
                    alert("Error de conexión verificando credenciales.");
                }
            })
            .finally(() => setLoading(false));
    }, [navigate]);

    const toggleSidebar = () => {
        setIsOpen(!isOpen);
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando panel de administración...</div>;
    if (!user) return null;

    return (
        <div>
            <SideBarMenu 
                isOpen={isOpen} 
                toggleSidebar={toggleSidebar} 
                user={user} 
                handleLogout={handleLogout}
            />
            <section className="home-section-dashboard">
                <div className="text-dashboard">Panel de administración</div>
                <div style={{padding: '0 18px'}}>
                    <p>Bienvenido al panel de control, {user.nombre || "Administrador"}.</p>
                    
                    <DashboardStats/>
                </div>
            </section>
        </div>
    );
}

export default AdminDashboard;