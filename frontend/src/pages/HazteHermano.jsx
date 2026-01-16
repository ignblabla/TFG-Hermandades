import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/HazteHermano.css"; 
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, User, MapPin, Church, CreditCard, Calendar, Lock, Phone, ChevronRight, ChevronLeft, Check } from "lucide-react";

function HazteHermano() {
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);
    
    // --- ESTADO DEL WIZARD ---
    const [currentStep, setCurrentStep] = useState(1);
    const totalSteps = 4;

    const [user, setUser] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [generalError, setGeneralError] = useState("");
    const [fieldErrors, setFieldErrors] = useState({});
    const [success, setSuccess] = useState(false);

    const [formData, setFormData] = useState({
        // Paso 1
        nombre: "", primer_apellido: "", segundo_apellido: "",
        fecha_nacimiento: "", genero: "MASCULINO", estado_civil: "SOLTERO",
        dni: "", password: "", confirmPassword: "",
        // Paso 2
        email: "", telefono: "", direccion: "", codigo_postal: "", localidad: "", provincia: "", comunidad_autonoma: "",
        // Paso 3
        lugar_bautismo: "", fecha_bautismo: "", parroquia_bautismo: "",
        // Paso 4
        iban: "", periodicidad: "TRIMESTRAL", es_titular: true,
    });

    const areasOptions = [
        { value: 'CARIDAD', label: 'Caridad' },
        { value: 'CULTOS_FORMACION', label: 'Cultos y Formación' },
        { value: 'JUVENTUD', label: 'Juventud' },
        { value: 'PATRIMONIO', label: 'Patrimonio' },
        { value: 'PRIOSTIA', label: 'Priostía' },
        { value: 'DIPUTACION_MAYOR_GOBIERNO', label: 'Diputación Mayor de Gobierno' },
        { value: 'COSTALEROS', label: 'Costaleros' },
        { value: 'ACÓLITOS', label: 'Acólitos' }
    ];

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
        
        // Limpiar error del campo al escribir
        if (fieldErrors[name]) {
            setFieldErrors(prev => ({ ...prev, [name]: null }));
        }
    };

    const handleAreaChange = (valorArea) => {
        setFormData(prev => {
            const currentAreas = prev.areas_interes;
            if (currentAreas.includes(valorArea)) {
                return { ...prev, areas_interes: currentAreas.filter(a => a !== valorArea) };
            } else {
                return { ...prev, areas_interes: [...currentAreas, valorArea] };
            }
        });
    };

    // --- LÓGICA DE NAVEGACIÓN Y VALIDACIÓN DEL WIZARD ---

    const validateStep = (step) => {
        const errors = {};
        let isValid = true;

        const checkRequired = (field, label) => {
            if (!formData[field] || formData[field].toString().trim() === "") {
                errors[field] = `El campo ${label || field} es obligatorio.`;
                isValid = false;
            }
        };

        if (step === 1) {
            checkRequired("nombre", "Nombre");
            checkRequired("primer_apellido", "Primer Apellido");
            checkRequired("segundo_apellido", "Segundo Apellido");
            checkRequired("fecha_nacimiento", "Fecha Nacimiento");
            checkRequired("dni", "DNI");
            checkRequired("password", "Contraseña");
            checkRequired("confirmPassword", "Repetir Contraseña");

            if (formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword) {
                errors.confirmPassword = "Las contraseñas no coinciden";
                isValid = false;
            }
        }

        if (step === 2) {
            checkRequired("email", "Email");
            checkRequired("telefono", "Teléfono");
            checkRequired("direccion", "Dirección");
            checkRequired("codigo_postal", "C.P.");
            checkRequired("localidad", "Localidad");
            checkRequired("provincia", "Provincia");
            checkRequired("comunidad_autonoma", "Comunidad");
        }

        if (step === 3) {
            checkRequired("fecha_bautismo", "Fecha Bautismo");
            checkRequired("lugar_bautismo", "Lugar Bautismo");
            checkRequired("parroquia_bautismo", "Parroquia");
        }

        if (step === 4) {
            checkRequired("iban", "IBAN");
        }

        setFieldErrors(errors);
        return isValid;
    };

    const handleNext = () => {
        if (validateStep(currentStep)) {
            setGeneralError("");
            setCurrentStep(prev => prev + 1);
            window.scrollTo(0, 0); 
        } else {
            setGeneralError("Por favor, complete los campos obligatorios antes de continuar.");
        }
    };

    const handlePrev = () => {
        setCurrentStep(prev => prev - 1);
        setGeneralError("");
        window.scrollTo(0, 0);
    };

    // --- AQUÍ ESTÁ EL CAMBIO IMPORTANTE ---
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        setSubmitting(true);
        setGeneralError("");
        setFieldErrors({});

        try {
            // 1. Desestructuramos el estado plano para separar datos personales de bancarios
            const { 
                iban, 
                periodicidad, 
                es_titular, 
                confirmPassword, // Lo eliminamos para no enviarlo
                ...datosPersonales // Aquí queda dni, nombre, areas_interes, etc.
            } = formData;

            // 2. Construimos el JSON anidado que espera el Backend
            const payload = {
                ...datosPersonales,
                datos_bancarios: {
                    iban: iban,
                    periodicidad: periodicidad,
                    es_titular: es_titular
                }
            };

            await api.post("api/hermanos/registro/", payload);
            setSuccess(true);
            setTimeout(() => navigate("/login"), 5000);

        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                
                // 3. Aplanamos los errores para la UI
                // Si el backend devuelve { datos_bancarios: { iban: ["Error"] } }
                // Nosotros queremos que fieldErrors tenga { iban: ["Error"] } para que el InputField lo pinte rojo.
                let erroresParaUI = { ...data };

                if (data.datos_bancarios) {
                    erroresParaUI = { ...erroresParaUI, ...data.datos_bancarios };
                }

                setFieldErrors(erroresParaUI);

                if (data.detail) setGeneralError(data.detail);
                else if (data.non_field_errors) setGeneralError(data.non_field_errors[0]);
                else setGeneralError("Error en la solicitud. Revise los datos marcados en rojo.");
                
            } else {
                setGeneralError("Error de conexión. Inténtelo más tarde.");
            }
        } finally {
            setSubmitting(false);
        }
    };

    // --- RENDERIZADO DE PASOS (Igual que antes) ---
    
    const stepsConfig = [
        { id: 1, title: "Personales", icon: <User size={18}/> },
        { id: 2, title: "Contacto", icon: <MapPin size={18}/> },
        { id: 3, title: "Sacramentales", icon: <Church size={18}/> },
        { id: 4, title: "Bancarios", icon: <CreditCard size={18}/> },
    ];

    if (success) {
        return (
            <div className="site-wrapper success-view">
                <div className="card-container-area" style={{textAlign: 'center', padding: '50px'}}>
                    <img src={logoEscudo} alt="Escudo" style={{width: '80px', marginBottom: '20px'}}/>
                    <h2 style={{color: '#16a34a'}}>¡Solicitud Recibida!</h2>
                    <p>Su solicitud de ingreso ha sido registrada correctamente.</p>
                    <p>Recibirá una notificación cuando Secretaría apruebe su alta.</p>
                    <button className="btn-purple" onClick={() => navigate("/login")} style={{marginTop: '20px'}}>
                        Ir al Acceso de Hermanos
                    </button>
                </div>
            </div>
        );
    }

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
                            <button className="btn-outline" onClick={() => navigate("/editar-perfil")} style={{cursor: 'pointer'}}>
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

            <main className="main-container-area">
                <div className="card-container-area">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Solicitud de nuevo ingreso</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Complete los detalles para solicitar su ingreso como hermano.
                        </p>
                    </header>

                    <div className="wizard-progress" style={{marginBottom: '20px'}}>
                        {stepsConfig.map((step, index) => (
                            <div key={step.id} className={`step-item ${currentStep === step.id ? 'active' : ''} ${currentStep > step.id ? 'completed' : ''}`}>
                                <div className="step-circle">
                                    {currentStep > step.id ? <Check size={16}/> : step.id}
                                </div>
                                <span className="step-title" style={{fontSize:'0.8rem'}}>{step.title}</span>
                                {index < stepsConfig.length - 1 && <div className="step-line"></div>}
                            </div>
                        ))}
                    </div>

                    {success && <div style={{padding: '10px', backgroundColor: '#dcfce7', color: '#16a34a', marginBottom: '1rem', borderRadius: '4px'}}>¡Solicitud de insignia creada correctamente! Redirigiendo...</div>}
                    
                    <section className="form-card-acto">
                        <form className="event-form-acto" onSubmit={handleSubmit}>
                            {currentStep === 1 && (
                                <>
                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="nombre">NOMBRE</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="nombre"
                                                    name="nombre"
                                                    required
                                                    placeholder="Nombre"
                                                    value={formData.nombre}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.nombre && <small className="error-message" style={{color: 'red'}}>{fieldErrors.nombre}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="primer_apellido">PRIMER APELLIDO</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="primer_apellido"
                                                    name="primer_apellido"
                                                    required
                                                    placeholder="Primer Apellido"
                                                    value={formData.primer_apellido}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.primer_apellido && <small className="error-message" style={{color: 'red'}}>{fieldErrors.primer_apellido}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="segundo_apellido">SEGUNDO APELLIDO</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="segundo_apellido"
                                                    name="segundo_apellido"
                                                    required
                                                    placeholder="Segundo Apellido"
                                                    value={formData.segundo_apellido}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.segundo_apellido && <small className="error-message" style={{color: 'red'}}>{fieldErrors.segundo_apellido}</small>}
                                        </div>
                                    </div>

                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="fecha_nacimiento">FECHA DE NACIMIENTO</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="date" 
                                                    id="fecha_nacimiento"
                                                    name="fecha_nacimiento"
                                                    required
                                                    value={formData.fecha_nacimiento}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.fecha_nacimiento && <small className="error-message" style={{color: 'red'}}>{fieldErrors.fecha_nacimiento}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="genero">GÉNERO</label>
                                            <div className="input-with-icon-acto">

                                                <select
                                                    id="genero"
                                                    name="genero"
                                                    required
                                                    value={formData.genero}
                                                    onChange={handleChange}
                                                >
                                                    <option value="" disabled>Seleccione una opción</option>
                                                    <option value="MASCULINO">Masculino</option>
                                                    <option value="FEMENINO">Femenino</option>
                                                </select>
                                            </div>
                                            {fieldErrors.genero && <small className="error-message" style={{color: 'red'}}>{fieldErrors.genero}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="estado_civil">ESTADO CIVIL</label>
                                            <div className="input-with-icon-acto">
                                                <select
                                                    id="estado_civil"
                                                    name="estado_civil"
                                                    required
                                                    value={formData.estado_civil}
                                                    onChange={handleChange}
                                                >
                                                    <option value="" disabled>Seleccione una opción</option>
                                                    <option value="SOLTERO">Soltero</option>
                                                    <option value="CASADO">Casado</option>
                                                    <option value="SEPARADO">Separado</option>
                                                    <option value="VIUDO">Viudo</option>
                                                </select>
                                            </div>
                                            {fieldErrors.estado_civil && <small className="error-message" style={{color: 'red'}}>{fieldErrors.estado_civil}</small>}
                                        </div>
                                    </div>

                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="dni">DNI (USUARIO)</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="dni"
                                                    name="dni"
                                                    required
                                                    placeholder="12345678A"
                                                    value={formData.dni}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.dni && <small className="error-message" style={{color: 'red'}}>{fieldErrors.dni}</small>}
                                        </div>
                                        <div className="form-group-acto">
                                            <label htmlFor="password">CONTRASEÑA</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="password" 
                                                    id="password"
                                                    name="password"
                                                    required
                                                    placeholder="********"
                                                    value={formData.password}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.password && <small className="error-message" style={{color: 'red'}}>{fieldErrors.password}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="confirmPassword">REPETIR CONTRASEÑA</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="password" 
                                                    id="confirmPassword"
                                                    name="confirmPassword"
                                                    required
                                                    placeholder="********"
                                                    value={formData.confirmPassword}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.confirmPassword && <small className="error-message" style={{color: 'red'}}>{fieldErrors.confirmPassword}</small>}
                                        </div>
                                    </div>
                                </>
                            )}

                            {currentStep === 2 && (
                                <>
                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="email">EMAIL</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="email" 
                                                    id="email"
                                                    name="email"
                                                    required
                                                    placeholder="ejemplo@correo.com"
                                                    value={formData.email}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.email && <small className="error-message" style={{color: 'red'}}>{fieldErrors.email}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="telefono">TELÉFONO MÓVIL</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="tel" 
                                                    id="telefono"
                                                    name="telefono"
                                                    required
                                                    placeholder="600000000"
                                                    maxLength={9}
                                                    value={formData.telefono}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.telefono && <small className="error-message" style={{color: 'red'}}>{fieldErrors.telefono}</small>}
                                        </div>
                                    </div>

                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="direccion">DIRECCIÓN POSTAL</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="direccion"
                                                    name="direccion"
                                                    required
                                                    placeholder="C/ Ejemplo, 1, 1ºA"
                                                    value={formData.direccion}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.direccion && <small className="error-message" style={{color: 'red'}}>{fieldErrors.direccion}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="localidad">LOCALIDAD</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="localidad"
                                                    name="localidad"
                                                    required
                                                    placeholder="Localidad"
                                                    value={formData.localidad}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.localidad && <small className="error-message" style={{color: 'red'}}>{fieldErrors.localidad}</small>}
                                        </div>
                                    </div>

                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="codigo_postal">CÓDIGO POSTAL</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="codigo_postal"
                                                    name="codigo_postal"
                                                    required
                                                    maxLength={5}
                                                    placeholder="00000"
                                                    value={formData.codigo_postal}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.codigo_postal && <small className="error-message" style={{color: 'red'}}>{fieldErrors.codigo_postal}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="provincia">PROVINCIA</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="provincia"
                                                    name="provincia"
                                                    required
                                                    placeholder="Provincia"
                                                    value={formData.provincia}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.provincia && <small className="error-message" style={{color: 'red'}}>{fieldErrors.provincia}</small>}
                                        </div>

                                        <div className="form-group-acto">
                                            <label htmlFor="comunidad_autonoma">COMUNIDAD AUTÓNOMA</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="comunidad_autonoma"
                                                    name="comunidad_autonoma"
                                                    required
                                                    placeholder="Comunidad Autónoma"
                                                    value={formData.comunidad_autonoma}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.comunidad_autonoma && <small className="error-message" style={{color: 'red'}}>{fieldErrors.comunidad_autonoma}</small>}
                                        </div>
                                    </div>
                                </>
                            )}

                            {currentStep === 3 && (
                                <>
                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="fecha_bautismo">FECHA DE BAUTISMO</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="date" 
                                                    id="fecha_bautismo"
                                                    name="fecha_bautismo"
                                                    required
                                                    value={formData.fecha_bautismo}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.fecha_bautismo && <small className="error-message" style={{color: 'red'}}>{fieldErrors.fecha_bautismo}</small>}
                                        </div>

                                        {/* --- CAMPO LUGAR (LOCALIDAD) --- */}
                                        <div className="form-group-acto">
                                            <label htmlFor="lugar_bautismo">LUGAR (LOCALIDAD)</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="lugar_bautismo"
                                                    name="lugar_bautismo"
                                                    required
                                                    placeholder="Localidad"
                                                    value={formData.lugar_bautismo}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.lugar_bautismo && <small className="error-message" style={{color: 'red'}}>{fieldErrors.lugar_bautismo}</small>}
                                        </div>
                                    </div>

                                    <div className="form-group-acto full-width">
                                        <div className="form-group-acto">
                                            <label htmlFor="parroquia_bautismo">PARROQUIA</label>
                                            <div className="input-with-icon-acto">
                                                <input 
                                                    type="text" 
                                                    id="parroquia_bautismo"
                                                    name="parroquia_bautismo"
                                                    required
                                                    placeholder="Parroquia de..."
                                                    value={formData.parroquia_bautismo}
                                                    onChange={handleChange}
                                                />
                                            </div>
                                            {fieldErrors.parroquia_bautismo && <small className="error-message" style={{color: 'red'}}>{fieldErrors.parroquia_bautismo}</small>}
                                        </div>
                                    </div>
                                </>
                            )}

                            {currentStep === 4 && (
                                <>
                                    <div className="form-group-acto full-width">
                                        <label htmlFor="iban">IBAN</label>
                                        <div className="input-with-icon-acto">
                                            <input 
                                            type="text" 
                                            id="iban"
                                            name="iban"
                                            required
                                            placeholder="ESXX XXXX XXXX XXXX XXXX"
                                            value={formData.iban || ''} 
                                            onChange={handleChange}
                                            />
                                        </div>
                                    {fieldErrors.iban && (<small className="error-message" style={{color: 'red'}}>{fieldErrors.iban}</small>)}
                                    </div>

                                    <div className="form-row-acto">
                                        <div className="form-group-acto">
                                            <label htmlFor="periodicidad">PERIODICIDAD CUOTA</label>
                                            <div className="input-with-icon-acto">
                                            <select
                                                id="periodicidad"
                                                name="periodicidad"
                                                value={formData.periodicidad}
                                                onChange={handleChange}
                                            >
                                                <option value="TRIMESTRAL">Trimestral</option>
                                                <option value="SEMESTRAL">Semestral</option>
                                                <option value="ANUAL">Anual</option>
                                            </select>
                                            </div>
                                        </div>

                                        <div className="form-group-acto">
                                            <label>¿Eres el titular de la cuenta?</label>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '5px' }}>
                                            <input 
                                                type="checkbox" 
                                                id="es_titular"
                                                name="es_titular" 
                                                checked={formData.es_titular} 
                                                onChange={handleChange} 
                                                style={{ width: 'auto', margin: 0 }}
                                            />
                                            <label htmlFor="es_titular" style={{ fontSize: '0.9rem', fontWeight: 'normal', margin: 0, cursor: 'pointer' }}>
                                                Confirmo que soy el titular de la cuenta bancaria.
                                            </label>
                                            </div>
                                        </div>
                                    </div>
                                </>
                                )}


                            <div className="wizard-actions" style={{marginTop: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                
                                {currentStep > 1 ? (
                                    <button type="button" className="btn-outline-acto" onClick={handlePrev} style={{display: 'flex', alignItems: 'center', gap: '5px'}}>
                                        <ChevronLeft size={16}/> Anterior
                                    </button>
                                ) : (
                                    <div></div> /* Espaciador vacío para mantener el layout flex */
                                )}
                                
                                {currentStep < totalSteps ? (
                                    <button type="button" className="btn-purple btn-next" onClick={handleNext} style={{display: 'flex', alignItems: 'center', gap: '5px'}}>
                                        Siguiente <ChevronRight size={16}/>
                                    </button>
                                ) : (
                                    <button type="submit" className="btn-save-acto btn-next" disabled={submitting}>
                                        {submitting ? "Enviando..." : "Finalizar Solicitud"}
                                    </button>
                                )}
                            </div>
                        </form>
                    </section>
                </div>
            </main>
        </div>
    );
}

// Helper Components
const InputField = ({ label, name, value, onChange, error, type = "text", required = false, placeholder, icon, maxLength }) => (
    <div className="form-group-custom">
        <label>{label} {required && "*"}</label>
        <div className={`input-wrapper ${error ? 'has-error' : ''}`}>
            {icon && <span className="input-icon">{icon}</span>}
            <input type={type} name={name} value={value} onChange={onChange} placeholder={placeholder} maxLength={maxLength} className={icon ? 'with-icon' : ''}/>
        </div>
        {error && <span className="error-text">{Array.isArray(error) ? error[0] : error}</span>}
    </div>
);

const SelectField = ({ label, name, value, onChange, options }) => (
    <div className="form-group-custom">
        <label>{label}</label>
        <div className="input-wrapper">
            <select name={name} value={value} onChange={onChange}>
                {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
        </div>
    </div>
);

export default HazteHermano;