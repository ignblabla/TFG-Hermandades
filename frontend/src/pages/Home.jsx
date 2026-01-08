import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import api from "../api";
import Note from "../components/Note"
import "../styles/Home.css"
import logoEscudo from '../assets/escudo.png';

function Home() {
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [activeSection, setActiveSection] = useState(null);
    const [formData, setFormData] = useState({
        telefono: "",
        direccion: "",
        codigo_postal: "",
        localidad: "",
        provincia: "",
        comunidad_autonoma: "",
        estado_civil: "",
        lugar_bautismo: "",
        fecha_bautismo: "",
        parroquia_bautismo: ""
    });

    const [mensaje, setMensaje] = useState({ texto: "", tipo: "" });

    const navigate = useNavigate();

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            const parsedUser = JSON.parse(usuarioGuardado);
            setUser(parsedUser);
            inicializarFormulario(parsedUser);
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
                    inicializarFormulario(data);
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

    const inicializarFormulario = (datosUsuario) => {
        setFormData({
            telefono: datosUsuario.telefono || "",
            direccion: datosUsuario.direccion || "",
            codigo_postal: datosUsuario.codigo_postal || "",
            localidad: datosUsuario.localidad || "",
            provincia: datosUsuario.provincia || "",
            comunidad_autonoma: datosUsuario.comunidad_autonoma || "",
            estado_civil: datosUsuario.estado_civil || "",
            lugar_bautismo: datosUsuario.lugar_bautismo || "",
            fecha_bautismo: datosUsuario.fecha_bautismo || "",
            parroquia_bautismo: datosUsuario.parroquia_bautismo || ""
        });
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/"; 
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSave = () => {
        const token = localStorage.getItem("access");
        setMensaje({ texto: "Guardando...", tipo: "info" });

        fetch("http://127.0.0.1:8000/api/me/", {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        })
        .then(async response => {
            if (response.ok) {
                const data = await response.json();
                
                const usuarioActualizado = { ...user, ...data };

                setUser(usuarioActualizado); 
                setActiveSection(null);
                setMensaje({ texto: "Datos actualizados correctamente.", tipo: "success" });
                
                localStorage.setItem("user_data", JSON.stringify(usuarioActualizado));
                
                setTimeout(() => setMensaje({ texto: "", tipo: "" }), 3000);
            } else {
                const errorData = await response.json();
                console.error("Errores:", errorData);
                setMensaje({ texto: "Error al actualizar. Revise los campos.", tipo: "error" });
            }
        })
        .catch(error => {
            console.error("Error de red:", error);
            setMensaje({ texto: "Error de conexión.", tipo: "error" });
        });
    };

    const handleCancel = () => {
        setActiveSection(null);
        if (user) inicializarFormulario(user);
        setMensaje({ texto: "", tipo: "" });
    };

    if (loading) return <div className="site-wrapper">Cargando...</div>;
    if (!user) return <div className="site-wrapper">No has iniciado sesión.</div>;

    return (
        <div className="site-wrapper">
            HOLA
        </div>
    );
}

export default Home;