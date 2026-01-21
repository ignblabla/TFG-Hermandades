import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api';
import '../styles/AdminEdicionHermano.css'; // Crearemos este CSS abajo
import { Save, User, MapPin, Calendar, ShieldAlert, CheckCircle } from "lucide-react";

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

    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => {
                setSuccessMsg("");
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

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
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i 
                        className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} 
                        id="btn" 
                        onClick={toggleSidebar}
                    ></i>
                </div>
                <ul className="nav-list-dashboard">
                    <li>
                        <i className="bx bx-search" onClick={toggleSidebar}></i>
                        <input type="text" placeholder="Search..." />
                        <span className="tooltip-dashboard">Search</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-grid-alt"></i>
                            <span className="link_name-dashboard">Dashboard</span>
                        </a>
                        <span className="tooltip-dashboard">Dashboard</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-user"></i>
                            <span className="link_name-dashboard">User</span>
                        </a>
                        <span className="tooltip-dashboard">User</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-chat"></i>
                            <span className="link_name-dashboard">Message</span>
                        </a>
                        <span className="tooltip-dashboard">Message</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-pie-chart-alt-2"></i>
                            <span className="link_name-dashboard">Analytics</span>
                        </a>
                        <span className="tooltip-dashboard">Analytics</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-folder"></i>
                            <span className="link_name-dashboard">File Manager</span>
                        </a>
                        <span className="tooltip-dashboard">File Manager</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-cart-alt"></i>
                            <span className="link_name-dashboard">Order</span>
                        </a>
                        <span className="tooltip-dashboard">Order</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-cog"></i>
                            <span className="link_name-dashboard">Settings</span>
                        </a>
                        <span className="tooltip-dashboard">Settings</span>
                    </li>
                    
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            <img src="profile.jpeg" alt="profile image" />
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{currentUser ? `${currentUser.nombre} ${currentUser.primer_apellido}` : "Usuario"}</div>
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

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Edición de Hermano</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        {error && (
                            <div className="alert-banner-edicion error-edicion">
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-edicion success-edicion">
                                <CheckCircle size={20} />
                                <span>{successMsg}</span>
                            </div>
                        )}
                        <form onSubmit={handleSubmit}>
                            <div className="form-section-edicion">
                                <h3 className="section-title-edicion"><User size={18}/> Datos personales</h3>
                                <div className="form-grid-edicion grid-4-edicion">
                                    <div className="form-group-edicion">
                                        <label>Nombre</label>
                                        <input type="text" name="nombre" value={formData.nombre} onChange={handleChange} required />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Primer apellido</label>
                                        <input type="text" name="primer_apellido" value={formData.primer_apellido} onChange={handleChange} required />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Segundo apellido</label>
                                        <input type="text" name="segundo_apellido" value={formData.segundo_apellido} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>DNI</label>
                                        <input type="text" name="dni" value={formData.dni} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Fecha de nacimiento</label>
                                        <input type="date" name="fecha_nacimiento" value={formData.fecha_nacimiento || ''} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Género</label>
                                        <select name="genero" value={formData.genero} onChange={handleChange}>
                                            <option value="MASCULINO">Masculino</option>
                                            <option value="FEMENINO">Femenino</option>
                                        </select>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Estado Civil</label>
                                        <select name="estado_civil" value={formData.estado_civil} onChange={handleChange}>
                                            <option value="SOLTERO">Soltero/a</option>
                                            <option value="CASADO">Casado/a</option>
                                            <option value="SEPARADO">Separado/a</option>
                                            <option value="VIUDO">Viudo/a</option>
                                        </select>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Nueva Contraseña</label>
                                        <input 
                                            type="password" name="password" value={formData.password} 
                                            onChange={handleChange} placeholder="Opcional" autoComplete="new-password"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion">
                                <h3 className="section-title-edicion"><MapPin size={18}/> Dirección y contacto</h3>
                                <div className="form-grid-edicion grid-6-mixed-edicion">
                                    <div className="form-group-edicion span-3-edicion">
                                        <label>Dirección Postal</label>
                                        <input type="text" name="direccion" value={formData.direccion} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion span-3-edicion">
                                        <label>Localidad</label>
                                        <input type="text" name="localidad" value={formData.localidad} onChange={handleChange} />
                                    </div>

                                    <div className="form-group-edicion span-2-edicion">
                                        <label>C. Postal</label>
                                        <input type="text" name="codigo_postal" value={formData.codigo_postal} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Provincia</label>
                                        <input type="text" name="provincia" value={formData.provincia} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Comunidad Autónoma</label>
                                        <input type="text" name="comunidad_autonoma" value={formData.comunidad_autonoma} onChange={handleChange} />
                                    </div>

                                    <div className="form-group-edicion span-3-edicion">
                                        <label>Teléfono</label>
                                        <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} required />
                                    </div>
                                    <div className="form-group-edicion span-3-edicion">
                                        <label>Email</label>
                                        <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion">
                                <h3 className="section-title-edicion"><Calendar size={18}/> Datos Eclesiásticos</h3>
                                <div className="form-grid-edicion grid-3-edicion">
                                    <div className="form-group-edicion">
                                        <label>Fecha Bautismo</label>
                                        <input type="date" name="fecha_bautismo" value={formData.fecha_bautismo || ''} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Lugar Bautismo</label>
                                        <input type="text" name="lugar_bautismo" value={formData.lugar_bautismo} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Parroquia</label>
                                        <input type="text" name="parroquia_bautismo" value={formData.parroquia_bautismo} onChange={handleChange} />
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion admin-section-edicion">
                                <h3 className="section-title-edicion admin-title-edicion"><ShieldAlert size={18}/> Gestión Interna (Secretaría)</h3>
                                <div className="form-grid-edicion">
                                    <div className="form-group-edicion">
                                        <label>Nº Registro Hermandad</label>
                                        <input type="number" name="numero_registro" value={formData.numero_registro} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Estado</label>
                                        <select name="estado_hermano" value={formData.estado_hermano} onChange={handleChange} 
                                            style={{borderColor: formData.estado_hermano === 'ALTA' ? 'green' : 'red'}}>
                                            <option value="ALTA">Alta</option>
                                            <option value="BAJA">Baja</option>
                                            <option value="PENDIENTE_INGRESO">Pendiente de Ingreso</option>
                                        </select>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Fecha Ingreso</label>
                                        <input type="date" name="fecha_ingreso_corporacion" value={formData.fecha_ingreso_corporacion || ''} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Fecha Baja</label>
                                        <input type="date" name="fecha_baja_corporacion" value={formData.fecha_baja_corporacion || ''} onChange={handleChange} />
                                    </div>
                                    
                                    <div className="form-group-edicion checkbox-group">
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

                            <div className="form-actions-edicion">
                                <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/hermanos/listado")}>Cancelar</button>
                                <button type="submit" className="btn-save-edicion" disabled={saving}>
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