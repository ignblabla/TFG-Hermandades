import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api';
import '../styles/AdminEdicionHermano.css'; // Crearemos este CSS abajo
import { ArrowLeft, Save, User, MapPin, Calendar, ShieldAlert, Lock } from "lucide-react";

function AdminEditarHermano() {
    const { id } = useParams();
    const navigate = useNavigate();
    
    // UI States
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");
    
    // User & Data States
    const [currentUser, setCurrentUser] = useState(null);
    const [formData, setFormData] = useState({
        dni: '', nombre: '', primer_apellido: '', segundo_apellido: '',
        email: '', telefono: '', password: '',
        fecha_nacimiento: '', genero: 'MASCULINO', estado_civil: 'SOLTERO',
        direccion: '', codigo_postal: '', localidad: '', provincia: '', comunidad_autonoma: '',
        lugar_bautismo: '', fecha_bautismo: '', parroquia_bautismo: '',
        numero_registro: '', estado_hermano: 'PENDIENTE_INGRESO', 
        fecha_ingreso_corporacion: '', fecha_baja_corporacion: '',
        esAdmin: false
    });

    // --- EFECTO DE CARGA ---
    useEffect(() => {
        let isMounted = true;

        const fetchAllData = async () => {
            try {
                let user = currentUser;
                if (!user) {
                    const resUser = await api.get("api/me/");
                    user = resUser.data;
                    if (isMounted) setCurrentUser(user);
                }

                if (!user.esAdmin) {
                    alert("No tienes permisos para estar aquí.");
                    navigate("/home");
                    return;
                }

                const resHermano = await api.get(`api/hermanos/${id}/gestion/`);
                
                if (isMounted) {
                    const data = resHermano.data;
                    setFormData({
                        ...data,
                        password: '',
                        segundo_apellido: data.segundo_apellido || '',
                        email: data.email || '',
                        direccion: data.direccion || '',
                        codigo_postal: data.codigo_postal || '',
                        localidad: data.localidad || '',
                        provincia: data.provincia || '',
                        comunidad_autonoma: data.comunidad_autonoma || '',
                        lugar_bautismo: data.lugar_bautismo || '',
                        parroquia_bautismo: data.parroquia_bautismo || '',
                        fecha_baja_corporacion: data.fecha_baja_corporacion || '',
                        numero_registro: data.numero_registro || ''
                    });
                }

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar los datos del hermano.");
                if (err.response?.status === 404) navigate("/hermanos/listado");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchAllData();
        return () => { isMounted = false; };
    }, [id, navigate]);

    // --- HANDLERS ---
    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        const payload = { ...formData };

        if (!payload.password || payload.password.trim() === "") {
            delete payload.password;
        }

        const dateFields = [
            'fecha_nacimiento', 
            'fecha_bautismo', 
            'fecha_ingreso_corporacion', 
            'fecha_baja_corporacion'
        ];

        dateFields.forEach(field => {
            if (payload[field] === "") {
                payload[field] = null;
            }
        });

        try {
            await api.put(`api/hermanos/${id}/gestion/`, payload);
            setSuccessMsg("Datos actualizados correctamente.");

            setFormData(prev => ({ ...prev, password: '' }));
            
            window.scrollTo(0, 0);
            
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                const errorData = err.response.data;
                const errorMessages = Object.entries(errorData)
                    .map(([key, msg]) => `${key.toUpperCase()}: ${msg}`)
                    .join(" | ");
                setError(errorMessages);
            } else {
                setError("Error al guardar los cambios.");
            }
        } finally {
            setSaving(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando ficha...</div>;

    return (
        <div>
            {/* --- SIDEBAR (Reutilizado) --- */}
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} id="btn" onClick={toggleSidebar}></i>
                </div>
                <ul className="nav-list-dashboard">
                    <li>
                        <a href="#" onClick={() => navigate("/hermanos/listado")}>
                            <i className="bx bx-grid-alt"></i>
                            <span className="link_name-dashboard">Volver al Censo</span>
                        </a>
                        <span className="tooltip-dashboard">Censo</span>
                    </li>
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            <img src="/profile.jpeg" alt="profile" />
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{currentUser ? `${currentUser.nombre}` : "Admin"}</div>
                                <div className="designation-dashboard">Secretaría</div>
                            </div>
                        </div>
                        <i className="bx bx-log-out" id="log_out" onClick={handleLogout} style={{cursor: 'pointer'}}></i>
                    </li>
                </ul>
            </div>

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Edición de Hermano</div>

                <div className="edit-container-wrapper">
                    <div className="card-edit-form">
                        
                        {/* HEADER */}
                        <div className="form-header">
                            <div className="header-left">
                                <button className="btn-back" onClick={() => navigate("/hermanos/listado")}>
                                    <ArrowLeft size={18} />
                                </button>
                                <div>
                                    <h2>{formData.nombre} {formData.primer_apellido}</h2>
                                    <span className="header-subtitle">Nº Registro: {formData.numero_registro || "Sin asignar"}</span>
                                </div>
                            </div>
                            <div className="header-right">
                                {formData.esAdmin && <span className="badge-admin-large">ADMINISTRADOR</span>}
                            </div>
                        </div>

                        {/* MENSAJES */}
                        {error && <div className="alert alert-error">{error}</div>}
                        {successMsg && <div className="alert alert-success">{successMsg}</div>}

                        <form onSubmit={handleSubmit}>
                            
                            {/* GRUPO 1: DATOS PERSONALES */}
                            <div className="form-section">
                                <h3 className="section-title"><User size={18}/> Datos Personales</h3>
                                <div className="form-grid">
                                    <div className="form-group">
                                        <label>Nombre</label>
                                        <input type="text" name="nombre" value={formData.nombre} onChange={handleChange} required />
                                    </div>
                                    <div className="form-group">
                                        <label>Primer Apellido</label>
                                        <input type="text" name="primer_apellido" value={formData.primer_apellido} onChange={handleChange} required />
                                    </div>
                                    <div className="form-group">
                                        <label>Segundo Apellido</label>
                                        <input type="text" name="segundo_apellido" value={formData.segundo_apellido} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>DNI</label>
                                        <input type="text" name="dni" value={formData.dni} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>F. Nacimiento</label>
                                        <input type="date" name="fecha_nacimiento" value={formData.fecha_nacimiento || ''} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>Género</label>
                                        <select name="genero" value={formData.genero} onChange={handleChange}>
                                            <option value="MASCULINO">Masculino</option>
                                            <option value="FEMENINO">Femenino</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Estado Civil</label>
                                        <select name="estado_civil" value={formData.estado_civil} onChange={handleChange}>
                                            <option value="SOLTERO">Soltero/a</option>
                                            <option value="CASADO">Casado/a</option>
                                            <option value="SEPARADO">Separado/a</option>
                                            <option value="VIUDO">Viudo/a</option>
                                        </select>
                                    </div>

                                    <div className="form-group">
                                        <label>NUEVA CONTRASEÑA</label>
                                        <input 
                                            type="password" 
                                            name="password" 
                                            value={formData.password} 
                                            onChange={handleChange} 
                                            placeholder="Dejar vacío para mantener actual"
                                            autoComplete="new-password"
                                        />
                                        <small className="form-help-text">* Rellenar solo si se desea cambiar</small>
                                    </div>
                                </div>
                            </div>

                            {/* GRUPO 2: CONTACTO Y DIRECCIÓN */}
                            <div className="form-section">
                                <h3 className="section-title"><MapPin size={18}/> Contacto y Dirección</h3>
                                <div className="form-grid">
                                    <div className="form-group full-width">
                                        <label>Dirección Postal</label>
                                        <input type="text" name="direccion" value={formData.direccion} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>Localidad</label>
                                        <input type="text" name="localidad" value={formData.localidad} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>C. Postal</label>
                                        <input type="text" name="codigo_postal" value={formData.codigo_postal} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>Provincia</label>
                                        <input type="text" name="provincia" value={formData.provincia} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>Teléfono</label>
                                        <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} required />
                                    </div>
                                    <div className="form-group">
                                        <label>Email</label>
                                        <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                                    </div>
                                </div>
                            </div>

                            {/* GRUPO 3: DATOS ECLESIÁSTICOS */}
                            <div className="form-section">
                                <h3 className="section-title"><Calendar size={18}/> Datos Eclesiásticos</h3>
                                <div className="form-grid">
                                    <div className="form-group">
                                        <label>Fecha Bautismo</label>
                                        <input type="date" name="fecha_bautismo" value={formData.fecha_bautismo || ''} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>Lugar Bautismo</label>
                                        <input type="text" name="lugar_bautismo" value={formData.lugar_bautismo} onChange={handleChange} />
                                    </div>
                                    <div className="form-group full-width">
                                        <label>Parroquia</label>
                                        <input type="text" name="parroquia_bautismo" value={formData.parroquia_bautismo} onChange={handleChange} />
                                    </div>
                                </div>
                            </div>

                            {/* GRUPO 4: GESTIÓN INTERNA (SOLO ADMIN) */}
                            <div className="form-section admin-section">
                                <h3 className="section-title admin-title"><ShieldAlert size={18}/> Gestión Interna (Secretaría)</h3>
                                <div className="form-grid">
                                    <div className="form-group">
                                        <label>Nº Registro Hermandad</label>
                                        <input type="number" name="numero_registro" value={formData.numero_registro} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>Estado</label>
                                        <select name="estado_hermano" value={formData.estado_hermano} onChange={handleChange} 
                                            style={{borderColor: formData.estado_hermano === 'ALTA' ? 'green' : 'red'}}>
                                            <option value="ALTA">Alta</option>
                                            <option value="BAJA">Baja</option>
                                            <option value="PENDIENTE_INGRESO">Pendiente de Ingreso</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Fecha Ingreso</label>
                                        <input type="date" name="fecha_ingreso_corporacion" value={formData.fecha_ingreso_corporacion || ''} onChange={handleChange} />
                                    </div>
                                    <div className="form-group">
                                        <label>Fecha Baja</label>
                                        <input type="date" name="fecha_baja_corporacion" value={formData.fecha_baja_corporacion || ''} onChange={handleChange} />
                                    </div>
                                    
                                    <div className="form-group checkbox-group">
                                        <label>
                                            <input 
                                                type="checkbox" 
                                                name="esAdmin" 
                                                checked={formData.esAdmin} 
                                                onChange={handleChange}
                                            />
                                            <span>Otorgar permisos de Administrador</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <div className="form-actions">
                                <button type="button" className="btn-cancel" onClick={() => navigate("/hermanos/listado")}>Cancelar</button>
                                <button type="submit" className="btn-save" disabled={saving}>
                                    <Save size={18} />
                                    {saving ? "Guardando..." : "Guardar Cambios"}
                                </button>
                            </div>

                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminEditarHermano;