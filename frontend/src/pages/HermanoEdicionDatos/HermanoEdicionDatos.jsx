import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../HermanoEdicionDatos/HermanoEdicionDatos.css'
import { Save, User, MapPin, AlertCircle, CheckCircle, Calendar, ShieldAlert, ListTodo,
    Users, Heart, Hammer, Church, Sun, BookOpen, Crown, Landmark, CreditCard, Bell
} from "lucide-react";


function EditarMiPerfil() {
    const navigate = useNavigate();
    const [isOpen, setIsOpen] = useState(false);
    
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");
    const [currentUser, setCurrentUser] = useState(null);
    const [areasDB, setAreasDB] = useState([]);
    
    const [readOnlyData, setReadOnlyData] = useState({});
    const [formData, setFormData] = useState({
        telefono: '', 
        estado_civil: 'SOLTERO',
        direccion: '', 
        codigo_postal: '', 
        localidad: '', 
        provincia: '', 
        comunidad_autonoma: '',
        email: '',
        password: '',
        areas_interes: [],
        datos_bancarios: {
            iban: '',
            es_titular: true,
            titular_cuenta: '',
            periodicidad: 'ANUAL'
        }
    });

    const areaInfoEstatica = {
        'TODOS_HERMANOS': { icon: <Bell size={20} />, title: 'Todos los Hermanos' },
        'COSTALEROS': { icon: <Users size={20} />, title: 'Costaleros' },
        'CARIDAD': { icon: <Heart size={20} />, title: 'Diputación de Caridad' },
        'JUVENTUD': { icon: <Sun size={20} />, title: 'Juventud' },
        'PRIOSTIA': { icon: <Hammer size={20} />, title: 'Priostía' },
        'CULTOS_FORMACION': { icon: <BookOpen size={20} />, title: 'Cultos y Formación' },
        'PATRIMONIO': { icon: <Landmark size={20} />, title: 'Patrimonio' },
        'ACOLITOS': { icon: <Church size={20} />, title: 'Acólitos' },
        'DIPUTACION_MAYOR_GOBIERNO': { icon: <Crown size={20} />, title: 'Dip. Mayor de Gobierno' },
    };

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
                const [resMe, resAreas] = await Promise.all([
                    api.get("api/me/"),
                    api.get("/api/areas-interes/")
                ]);
                
                if (isMounted) {
                    const data = resMe.data;
                    const dataAreas = resAreas.data;

                    setCurrentUser(data);
                    setAreasDB(dataAreas);

                    setReadOnlyData({
                        nombre: data.nombre || '',
                        primer_apellido: data.primer_apellido || '',
                        segundo_apellido: data.segundo_apellido || '',
                        dni: data.dni || '',
                        fecha_nacimiento: data.fecha_nacimiento || '',
                        genero: data.genero || '',
                        fecha_bautismo: data.fecha_bautismo,
                        lugar_bautismo: data.lugar_bautismo,
                        parroquia_bautismo: data.parroquia_bautismo,
                        numero_registro: data.numero_registro || 'Pendiente',
                        estado_hermano: data.estado_hermano || '',
                        fecha_ingreso: data.fecha_ingreso_corporacion,
                        fecha_baja: data.fecha_baja_corporacion
                    });

                    const areasUsuario = data.areas_interes || [];
                    if (!areasUsuario.includes('TODOS_HERMANOS')) {
                        areasUsuario.push('TODOS_HERMANOS');
                    }

                    // Campos permitidos
                    setFormData({
                        password: data.password || '',
                        telefono: data.telefono || '',
                        estado_civil: data.estado_civil || 'SOLTERO',
                        direccion: data.direccion || '',
                        codigo_postal: data.codigo_postal || '',
                        localidad: data.localidad || '',
                        provincia: data.provincia || '',
                        comunidad_autonoma: data.comunidad_autonoma || '',
                        email: data.email,
                        areas_interes: data.areas_interes || [],
                        datos_bancarios: data.datos_bancarios || {
                            iban: '',
                            es_titular: true,
                            titular_cuenta: '',
                            periodicidad: 'ANUAL'
                        }
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

    const handleBankChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            datos_bancarios: {
                ...prev.datos_bancarios,
                [name]: type === 'checkbox' ? checked : value
            }
        }));
    };

    const handleAreaToggle = (areaNombre) => {
        if (areaNombre === 'TODOS_HERMANOS') return;

        setFormData(prev => {
            const currentAreas = prev.areas_interes;
            if (currentAreas.includes(areaNombre)) {
                return { ...prev, areas_interes: currentAreas.filter(a => a !== areaNombre) };
            } else {
                return { ...prev, areas_interes: [...currentAreas, areaNombre] };
            }
        });
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

        if (payload.datos_bancarios.es_titular) {
            payload.datos_bancarios.titular_cuenta = '';
        }

        if (!payload.areas_interes.includes('TODOS_HERMANOS')) {
            payload.areas_interes.push('TODOS_HERMANOS');
        }

        try {
            await api.patch("api/me/", payload);
            setSuccessMsg("Perfil y preferencias actualizadas correctamente.");
            setFormData(prev => ({ ...prev, password: '' }));
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                const errorData = err.response.data;
                const errorMessages = Object.entries(errorData)
                    .map(([key, msg]) => {
                        if (typeof msg === 'object' && msg !== null) {
                            return Object.entries(msg).map(([subKey, subMsg]) => `${subKey.toUpperCase()}: ${subMsg}`).join(" | ");
                        }
                        return `${key.toUpperCase()}: ${msg}`;
                    })
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

    const sortedAreasDB = [...areasDB].sort((a, b) => {
        if (a.nombre_area === 'TODOS_HERMANOS') return -1;
        if (b.nombre_area === 'TODOS_HERMANOS') return 1;
        return a.nombre_area.localeCompare(b.nombre_area); 
    });

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
                            <div className="alert-banner-edicion-hermano error-edicion-hermano">
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-edicion-hermano success-edicion-hermano">
                                <CheckCircle size={20} />
                                <span>{successMsg}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            <div className="form-section-edicion-hermano">
                                <h3 className="section-title-edicion-hermano"><User size={18}/> Datos personales</h3>
                                <div className="form-grid-edicion-hermano grid-4-edicion-hermano">
                                    <div className="form-group-edicion-hermano">
                                        <label>Nombre</label>
                                        <input type="text" name="nombre" value={readOnlyData.nombre} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Primer apellido</label>
                                        <input type="text" name="primer_apellido" value={readOnlyData.primer_apellido} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Segundo apellido</label>
                                        <input type="text" name="segundo_apellido" value={readOnlyData.segundo_apellido} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>DNI</label>
                                        <input type="text" name="dni" value={readOnlyData.dni} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Fecha de nacimiento</label>
                                        <input type="date" name="fecha_nacimiento" value={readOnlyData.fecha_nacimiento || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Género</label>
                                        <input type="text" name="genero" value={readOnlyData.genero} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Estado Civil</label>
                                        <select name="estado_civil" value={formData.estado_civil} onChange={handleChange}>
                                            <option value="SOLTERO">Soltero/a</option>
                                            <option value="CASADO">Casado/a</option>
                                            <option value="SEPARADO">Separado/a</option>
                                            <option value="VIUDO">Viudo/a</option>
                                        </select>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Nueva Contraseña</label>
                                        <input 
                                            type="password" name="password" value={formData.password} 
                                            onChange={handleChange} placeholder="Opcional" autoComplete="new-password"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion-hermano">
                                <h3 className="section-title-edicion-hermano"><MapPin size={18}/> Dirección y contacto</h3>
                                <div className="form-grid-edicion-hermano grid-6-mixed-edicion-hermano">
                                    <div className="form-group-edicion-hermano span-3-edicion-hermano">
                                        <label>Dirección Postal</label>
                                        <input type="text" name="direccion" value={formData.direccion} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion-hermano span-3-edicion-hermano">
                                        <label>Localidad</label>
                                        <input type="text" name="localidad" value={formData.localidad} onChange={handleChange} />
                                    </div>

                                    <div className="form-group-edicion-hermano span-2-edicion-hermano">
                                        <label>C. Postal</label>
                                        <input type="text" name="codigo_postal" value={formData.codigo_postal} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion-hermano span-2-edicion-hermano">
                                        <label>Provincia</label>
                                        <input type="text" name="provincia" value={formData.provincia} onChange={handleChange} />
                                    </div>
                                    <div className="form-group-edicion-hermano span-2-edicion-hermano">
                                        <label>Comunidad Autónoma</label>
                                        <input type="text" name="comunidad_autonoma" value={formData.comunidad_autonoma} onChange={handleChange} />
                                    </div>

                                    <div className="form-group-edicion-hermano span-3-edicion-hermano">
                                        <label>Teléfono</label>
                                        <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} required />
                                    </div>
                                    <div className="form-group-edicion-hermano span-3-edicion-hermano">
                                        <label>Email</label>
                                        <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion-hermano">
                                <h3 className="section-title-edicion-hermano"><CreditCard size={18}/> Datos Bancarios</h3>
                                <div className="form-grid-edicion-hermano grid-4-edicion-hermano">
                                    <div className="form-group-edicion-hermano span-2-edicion-hermano">
                                        <label>IBAN de la cuenta</label>
                                        <input 
                                            type="text" 
                                            name="iban" 
                                            value={formData.datos_bancarios.iban} 
                                            onChange={handleBankChange} 
                                            placeholder="ES00..." 
                                            required 
                                        />
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Periodicidad de cobro</label>
                                        <select name="periodicidad" value={formData.datos_bancarios.periodicidad} onChange={handleBankChange}>
                                            <option value="TRIMESTRAL">Trimestral</option>
                                            <option value="SEMESTRAL">Semestral</option>
                                            <option value="ANUAL">Anual</option>
                                        </select>
                                    </div>
                                    <div className="form-group-edicion-hermano checkbox-group-edicion-hermano" style={{ justifyContent: 'center' }}>
                                        <label>
                                            <input 
                                                type="checkbox" 
                                                name="es_titular" 
                                                checked={formData.datos_bancarios.es_titular} 
                                                onChange={handleBankChange} 
                                            />
                                            <span>Soy titular de la cuenta</span>
                                        </label>
                                    </div>
                                    
                                    {/* Mostrar solo si NO es titular */}
                                    {!formData.datos_bancarios.es_titular && (
                                        <div className="form-group-edicion-hermano span-2-edicion-hermano">
                                            <label>Nombre y apellidos del titular de la cuenta</label>
                                            <input 
                                                type="text" 
                                                name="titular_cuenta" 
                                                value={formData.datos_bancarios.titular_cuenta || ''} 
                                                onChange={handleBankChange} 
                                                placeholder="Solo si no es tu cuenta"
                                                required={!formData.datos_bancarios.es_titular} 
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="form-section-edicion-hermano">
                                <h3 className="section-title-edicion-hermano"><Calendar size={18}/> Datos Eclesiásticos</h3>
                                <div className="form-grid-edicion-hermano grid-3-edicion-hermano">
                                    <div className="form-group-edicion-hermano">
                                        <label>Fecha Bautismo</label>
                                        <input type="date" name="fecha_bautismo" value={readOnlyData.fecha_bautismo || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Lugar Bautismo</label>
                                        <input type="text" name="lugar_bautismo" value={readOnlyData.lugar_bautismo || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Parroquia</label>
                                        <input type="text" name="parroquia_bautismo" value={readOnlyData.parroquia_bautismo || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion-hermano admin-section-edicion-hermano">
                                <h3 className="section-title-edicion-hermano admin-title-edicion-hermano"><ShieldAlert size={18}/> Gestión Interna (Secretaría)</h3>
                                <div className="form-grid-edicion-hermano grid-4-edicion-hermano">
                                    <div className="form-group-edicion-hermano">
                                        <label>Nº Registro Hermandad</label>
                                        <input type="number" name="numero_registro" value={readOnlyData.numero_registro} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Estado</label>
                                        <input type="text" name="estado_hermano" value={readOnlyData.estado_hermano} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Fecha Ingreso</label>
                                        <input type="date" name="fecha_ingreso_corporacion" value={readOnlyData.fecha_ingreso} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                    <div className="form-group-edicion-hermano">
                                        <label>Fecha Baja</label>
                                        <input type="date" name="fecha_baja_corporacion" value={readOnlyData.fecha_baja || ''} disabled style={{ backgroundColor: '#e9ecef' }}/>
                                    </div>
                                </div>
                            </div>

                            <div className="form-section-edicion-hermano">
                                <h3 className="section-title-edicion-hermano"><ListTodo size={18}/> Mis Áreas de interés</h3>
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                                    Selecciona los grupos de los que quieres recibir notificaciones.
                                </p>
                                
                                <div className="form-grid-edicion-hermano grid-4-edicion-hermano">
                                    {sortedAreasDB.map(area => {
                                        const visualInfo = areaInfoEstatica[area.nombre_area] || {};
                                        const isMandatory = area.nombre_area === 'TODOS_HERMANOS';
                                        const isSelected = isMandatory ? true : formData.areas_interes.includes(area.nombre_area);
                                        
                                        return (
                                            <div 
                                                key={area.id}
                                                onClick={() => handleAreaToggle(area.nombre_area)}
                                                // Asignamos la nueva clase si es la tarjeta general
                                                className={isMandatory ? 'span-full-edicion' : ''}
                                                style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '12px',
                                                    padding: '12px 16px',
                                                    borderRadius: '8px',
                                                    border: isSelected ? '2px solid var(--burgundy-primary)' : '1px solid var(--border-color)',
                                                    backgroundColor: isSelected ? 'var(--focus-ring)' : '#fff',
                                                    cursor: isMandatory ? 'not-allowed' : 'pointer',
                                                    transition: 'all 0.2s ease',
                                                    boxSizing: 'border-box',
                                                    opacity: isMandatory ? 0.9 : 1
                                                }}
                                            >
                                                <div style={{ color: isSelected ? 'var(--burgundy-primary)' : 'var(--text-muted)', display: 'flex' }}>
                                                    {visualInfo.icon}
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                        <span style={{ 
                                                            fontSize: '0.9rem', 
                                                            color: isSelected ? 'var(--burgundy-primary)' : 'var(--text-dark)',
                                                            fontWeight: isSelected ? '700' : '600'
                                                        }}>
                                                            {visualInfo.title || area.nombre_area}
                                                        </span>
                                                        {isMandatory && (
                                                            <span style={{ fontSize: '0.65rem', fontWeight: 'bold', color: '#6c757d', backgroundColor: '#e9ecef', padding: '3px 8px', borderRadius: '12px' }}>
                                                                OBLIGATORIO
                                                            </span>
                                                        )}
                                                    </div>
                                                    {isMandatory && visualInfo.desc && (
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                                                            {visualInfo.desc}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="form-actions-edicion-hermano">
                                <button type="button" className="btn-cancel-edicion-hermano" onClick={() => navigate("/hermanos/listado")}>Cancelar</button>
                                <button type="submit" className="btn-save-edicion-hermano" disabled={saving}>
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

export default EditarMiPerfil;