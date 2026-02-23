import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import '../styles/AdminEdicionHermano.css';
import { Save, User, MapPin, AlertCircle, CheckCircle, Info, Calendar, ShieldAlert } from "lucide-react";

function EditarMiPerfil() {
    const navigate = useNavigate();
    const [isOpen, setIsOpen] = useState(false);
    
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");
    const [currentUser, setCurrentUser] = useState(null);
    
    // Estados separados: Datos de solo lectura (informativos) y Datos editables
    const [readOnlyData, setReadOnlyData] = useState({});
    const [formData, setFormData] = useState({
        telefono: '', 
        estado_civil: 'SOLTERO',
        direccion: '', 
        codigo_postal: '', 
        localidad: '', 
        provincia: '', 
        comunidad_autonoma: '',
        email: ''
        // Nota: áreas_interes y datos_bancarios requieren un manejo un poco más complejo 
        // (selects múltiples y objetos anidados). Se omiten aquí para mantener la simplicidad, 
        // pero tu backend ya los soporta.
    });

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    // --- EFECTO DE CARGA ---
    useEffect(() => {
        let isMounted = true;
        const fetchMyData = async () => {
            try {
                const response = await api.get("api/me/");
                
                if (isMounted) {
                    const data = response.data;

                    setReadOnlyData({
                        nombre: data.nombre,
                        primer_apellido: data.primer_apellido,
                        segundo_apellido: data.segundo_apellido || '',
                        dni: data.dni,
                        fecha_nacimiento: data.fecha_nacimiento,
                        genero: data.genero,
                        fecha_bautismo: data.fecha_bautismo,
                        lugar_bautismo: data.lugar_bautismo,
                        parroquia_bautismo: data.parroquia_bautismo,
                        numero_registro: data.numero_registro || 'Pendiente',
                        estado_hermano: data.estado_hermano,
                        fecha_ingreso: data.fecha_ingreso_corporacion,
                        fecha_baja: data.fecha_baja_corporacion
                    });

                    // Campos permitidos
                    setFormData({
                        password: data.password,
                        telefono: data.telefono || '',
                        estado_civil: data.estado_civil || 'SOLTERO',
                        direccion: data.direccion || '',
                        codigo_postal: data.codigo_postal || '',
                        localidad: data.localidad || '',
                        provincia: data.provincia || '',
                        comunidad_autonoma: data.comunidad_autonoma || '',
                        email: data.email
                    });
                }
            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar tu perfil. Comprueba tu conexión.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchMyData();
        return () => { isMounted = false; };
    }, []);

    // --- TEMPORIZADOR PARA MENSAJE DE ÉXITO ---
    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    // --- HANDLERS ---
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        try {
            // Usamos PATCH hacia api/me/ para que actúe el UserUpdateSerializer
            await api.patch("api/me/", formData);
            setSuccessMsg("Tus datos se han actualizado correctamente.");
            window.scrollTo(0, 0);
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                // Manejo de errores de validación de Django/DRF
                const errorData = err.response.data;
                const errorMessages = Object.entries(errorData)
                    .map(([key, msg]) => `${key.toUpperCase()}: ${msg}`)
                    .join(" | ");
                setError(errorMessages);
            } else {
                setError("Error al guardar los cambios. Inténtalo de nuevo más tarde.");
            }
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="loading-screen">Cargando tu perfil...</div>;

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

            <section className="home-section-dashboard">
                <div className="text-dashboard">Edición de datos personales</div>
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
                                        <input type="text" name="nombre" value={readOnlyData.nombre} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Primer apellido</label>
                                        <input type="text" name="primer_apellido" value={readOnlyData.primer_apellido} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Segundo apellido</label>
                                        <input type="text" name="segundo_apellido" value={readOnlyData.segundo_apellido} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>DNI</label>
                                        <input type="text" name="dni" value={readOnlyData.dni} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Fecha de nacimiento</label>
                                        <input type="date" name="fecha_nacimiento" value={readOnlyData.fecha_nacimiento || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Género</label>
                                        <input type="text" name="genero" value={readOnlyData.genero} disabled style={{ backgroundColor: '#e9ecef' }}/>
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
                                        <input type="date" name="fecha_bautismo" value={readOnlyData.fecha_bautismo || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Lugar Bautismo</label>
                                        <input type="text" name="lugar_bautismo" value={readOnlyData.lugar_bautismo || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Parroquia</label>
                                        <input type="text" name="parroquia_bautismo" value={readOnlyData.parroquia_bautismo || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion admin-section-edicion">
                                <h3 className="section-title-edicion admin-title-edicion"><ShieldAlert size={18}/> Gestión Interna (Secretaría)</h3>
                                <div className="form-grid-edicion grid-4-edicion">
                                    <div className="form-group-edicion">
                                        <label>Nº Registro Hermandad</label>
                                        <input type="number" name="numero_registro" value={readOnlyData.numero_registro} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Estado</label>
                                        <input type="text" name="estado_hermano" value={readOnlyData.estado_hermano} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Fecha Ingreso</label>
                                        <input type="date" name="fecha_ingreso_corporacion" value={readOnlyData.fecha_ingreso} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion">
                                        <label>Fecha Baja</label>
                                        <input type="date" name="fecha_baja_corporacion" value={readOnlyData.fecha_baja || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
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

            {/* <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
            <h2 className="text-dashboard" style={{ marginBottom: '20px' }}>Mi Perfil de Hermano</h2>
            
            <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}> */}
                
                {/* --- MENSAJES DE ALERTA --- */}
                {/* {error && (
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
                )} */}

                {/* --- SECCIÓN DE SOLO LECTURA (Informativa) --- */}
                {/* <div className="form-section-edicion" style={{ backgroundColor: '#f8f9fa', borderLeft: '4px solid #0056b3' }}>
                    <h3 className="section-title-edicion"><Info size={18}/> Datos Identificativos (Solo Lectura)</h3>
                    <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '15px' }}>
                        Para modificar tu nombre, DNI o correo electrónico, contacta con Secretaría.
                    </p>
                    <div className="form-grid-edicion grid-4-edicion">
                        <div className="form-group-edicion">
                            <label>Nombre Completo</label>
                            <input type="text" value={readOnlyData.nombreCompleto} disabled style={{ backgroundColor: '#e9ecef' }} />
                        </div>
                        <div className="form-group-edicion">
                            <label>DNI</label>
                            <input type="text" value={readOnlyData.dni} disabled style={{ backgroundColor: '#e9ecef' }} />
                        </div>
                        <div className="form-group-edicion">
                            <label>Nº de Registro</label>
                            <input type="text" value={readOnlyData.numero_registro} disabled style={{ backgroundColor: '#e9ecef' }} />
                        </div>
                        <div className="form-group-edicion">
                            <label>Correo Electrónico</label>
                            <input type="email" value={readOnlyData.email} disabled style={{ backgroundColor: '#e9ecef' }} />
                        </div>
                    </div>
                </div> */}

                {/* --- FORMULARIO EDITABLE --- */}
                {/* <form onSubmit={handleSubmit}> */}
                    
                    {/* Datos de Contacto y Dirección */}
                    {/* <div className="form-section-edicion">
                        <h3 className="section-title-edicion"><MapPin size={18}/> Datos de Contacto y Dirección</h3>
                        <div className="form-grid-edicion grid-6-mixed-edicion">
                            <div className="form-group-edicion span-3-edicion">
                                <label>Dirección Postal</label>
                                <input type="text" name="direccion" value={formData.direccion} onChange={handleChange} required />
                            </div>
                            <div className="form-group-edicion span-3-edicion">
                                <label>Localidad</label>
                                <input type="text" name="localidad" value={formData.localidad} onChange={handleChange} required />
                            </div>

                            <div className="form-group-edicion span-2-edicion">
                                <label>C. Postal</label>
                                <input type="text" name="codigo_postal" value={formData.codigo_postal} onChange={handleChange} required />
                            </div>
                            <div className="form-group-edicion span-2-edicion">
                                <label>Provincia</label>
                                <input type="text" name="provincia" value={formData.provincia} onChange={handleChange} required />
                            </div>
                            <div className="form-group-edicion span-2-edicion">
                                <label>Comunidad Autónoma</label>
                                <input type="text" name="comunidad_autonoma" value={formData.comunidad_autonoma} onChange={handleChange} required />
                            </div>
                        </div>
                    </div> */}

                    {/* Otros Datos Personales */}
                    {/* <div className="form-section-edicion">
                        <h3 className="section-title-edicion"><User size={18}/> Otros Datos</h3>
                        <div className="form-grid-edicion grid-4-edicion">
                            <div className="form-group-edicion">
                                <label>Teléfono (9 dígitos)</label>
                                <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} required />
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
                        </div>
                    </div> */}

                    {/* Acciones */}
                    {/* <div className="form-actions-edicion">
                        <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/dashboard")}>
                            Volver
                        </button>
                        <button type="submit" className="btn-save-edicion" disabled={saving}>
                            <Save size={18} />
                            {saving ? "Guardando..." : "Actualizar Mis Datos"}
                        </button>
                    </div> */}
                {/* </form> */}

            {/* </div> */}
        {/* </div> */}

        </div>
    );
}

export default EditarMiPerfil;