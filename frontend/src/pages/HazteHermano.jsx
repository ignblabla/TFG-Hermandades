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
    const totalSteps = 5;

    const [submitting, setSubmitting] = useState(false);
    const [generalError, setGeneralError] = useState("");
    const [fieldErrors, setFieldErrors] = useState({});
    const [success, setSuccess] = useState(false);

    const [formData, setFormData] = useState({
        // Paso 1
        dni: "", email: "", password: "", confirmPassword: "",
        nombre: "", primer_apellido: "", segundo_apellido: "",
        fecha_nacimiento: "", genero: "MASCULINO", estado_civil: "SOLTERO",
        // Paso 2
        telefono: "", direccion: "", codigo_postal: "", localidad: "", provincia: "", comunidad_autonoma: "",
        // Paso 3
        lugar_bautismo: "", fecha_bautismo: "", parroquia_bautismo: "",
        // Paso 4
        iban: "", periodicidad: "TRIMESTRAL", es_titular: true,
        // Paso 5
        areas_interes: [] 
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
            if (!formData[field] || formData[field].trim() === "") {
                errors[field] = `El campo ${label || field} es obligatorio.`;
                isValid = false;
            }
        };

        if (step === 1) {
            checkRequired("dni", "DNI");
            checkRequired("email", "Email");
            checkRequired("nombre", "Nombre");
            checkRequired("primer_apellido", "Primer Apellido");
            checkRequired("segundo_apellido", "Segundo Apellido");
            checkRequired("fecha_nacimiento", "Fecha Nacimiento");
            checkRequired("password", "Contraseña");
            checkRequired("confirmPassword", "Repetir Contraseña");

            if (formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword) {
                errors.confirmPassword = "Las contraseñas no coinciden";
                isValid = false;
            }
        }

        if (step === 2) {
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
            window.scrollTo(0, 0); // Subir arriba al cambiar de paso
        } else {
            setGeneralError("Por favor, complete los campos obligatorios antes de continuar.");
        }
    };

    const handlePrev = () => {
        setCurrentStep(prev => prev - 1);
        setGeneralError("");
        window.scrollTo(0, 0);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        // Validar último paso (aunque es opcional, por si acaso)
        
        setSubmitting(true);
        setGeneralError("");
        setFieldErrors({});

        try {
            const { confirmPassword, ...payload } = formData;
            await api.post("api/hermanos/registro/", payload);
            setSuccess(true);
            setTimeout(() => navigate("/login"), 5000);
        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                setFieldErrors(data);
                if (data.detail) setGeneralError(data.detail);
                else if (data.non_field_errors) setGeneralError(data.non_field_errors[0]);
                else setGeneralError("Error en la solicitud. Revise los datos.");
                
                // Si hay error en un campo de un paso anterior, podrías lógica para volver, 
                // pero por simplicidad mostramos el mensaje general.
            } else {
                setGeneralError("Error de conexión. Inténtelo más tarde.");
            }
        } finally {
            setSubmitting(false);
        }
    };

    // --- RENDERIZADO DE PASOS ---
    
    const stepsConfig = [
        { id: 1, title: "Personales", icon: <User size={18}/> },
        { id: 2, title: "Contacto", icon: <MapPin size={18}/> },
        { id: 3, title: "Sacramentales", icon: <Church size={18}/> },
        { id: 4, title: "Bancarios", icon: <CreditCard size={18}/> },
        { id: 5, title: "Intereses", icon: <Calendar size={18}/> },
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
                    <img src={logoEscudo} alt="Escudo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SOLICITUD DE INGRESO</span>
                    </div>
                </div>
                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
                <div className="nav-buttons-desktop">
                    <button className="btn-outline" onClick={() => navigate("/")}>Cancelar</button>
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area card-wide">
                    
                    {/* --- HEADER DEL WIZARD (PROGRESO) --- */}
                    <div className="wizard-progress">
                        {stepsConfig.map((step, index) => (
                            <div key={step.id} className={`step-item ${currentStep === step.id ? 'active' : ''} ${currentStep > step.id ? 'completed' : ''}`}>
                                <div className="step-circle">
                                    {currentStep > step.id ? <Check size={16}/> : step.icon}
                                </div>
                                <span className="step-title">{step.title}</span>
                                {index < stepsConfig.length - 1 && <div className="step-line"></div>}
                            </div>
                        ))}
                    </div>

                    <div className="wizard-content">
                        {generalError && (
                            <div className="alert-box error" style={{marginBottom: '20px'}}>
                                {generalError}
                            </div>
                        )}

                        <form className="register-form" onSubmit={handleSubmit}>
                            
                            {/* PASO 1: DATOS PERSONALES */}
                            {currentStep === 1 && (
                                <div className="step-anim">
                                    <div className="form-section-title">Datos Personales y Acceso</div>
                                    <div className="form-grid">
                                        
                                        {/* Fila 1: DNI y Email */}
                                        <InputField label="DNI (Usuario)" name="dni" value={formData.dni} onChange={handleChange} error={fieldErrors.dni} required placeholder="12345678A" />
                                        <InputField label="Email" name="email" type="email" value={formData.email} onChange={handleChange} error={fieldErrors.email} required />
                                        
                                        {/* Fila 2: Nombre y Apellidos (3 columnas) */}
                                        <div className="full-width-col three-cols-row">
                                            <InputField label="Nombre" name="nombre" value={formData.nombre} onChange={handleChange} error={fieldErrors.nombre} required />
                                            <InputField label="Primer Apellido" name="primer_apellido" value={formData.primer_apellido} onChange={handleChange} error={fieldErrors.primer_apellido} required />
                                            <InputField label="Segundo Apellido" name="segundo_apellido" value={formData.segundo_apellido} onChange={handleChange} error={fieldErrors.segundo_apellido} required />
                                        </div>
                                        
                                        {/* Fila 3: Fecha nacimiento, Género y Estado Civil (AHORA EN 3 COLUMNAS) */}
                                        <div className="full-width-col three-cols-row">
                                            <div className="form-group-custom">
                                                <label>Fecha de Nacimiento *</label>
                                                <input type="date" name="fecha_nacimiento" value={formData.fecha_nacimiento} onChange={handleChange} className={fieldErrors.fecha_nacimiento ? 'input-error' : ''} />
                                                {fieldErrors.fecha_nacimiento && <span className="error-text">{fieldErrors.fecha_nacimiento}</span>}
                                            </div>

                                            <SelectField label="Género" name="genero" value={formData.genero} onChange={handleChange} options={[{value: 'MASCULINO', label: 'Masculino'}, {value: 'FEMENINO', label: 'Femenino'}]} />
                                            
                                            <SelectField label="Estado Civil" name="estado_civil" value={formData.estado_civil} onChange={handleChange} options={[{value: 'SOLTERO', label: 'Soltero'}, {value: 'CASADO', label: 'Casado'}, {value: 'SEPARADO', label: 'Separado'}, {value: 'VIUDO', label: 'Viudo'}]} />
                                        </div>
                                        
                                        {/* Fila 4: Contraseñas */}
                                        <InputField label="Contraseña" name="password" type="password" value={formData.password} onChange={handleChange} error={fieldErrors.password} required icon={<Lock size={14}/>}/>
                                        <InputField label="Repetir Contraseña" name="confirmPassword" type="password" value={formData.confirmPassword} onChange={handleChange} error={fieldErrors.confirmPassword} required icon={<Lock size={14}/>}/>
                                    </div>
                                </div>
                            )}

                            {/* PASO 2: CONTACTO */}
                            {currentStep === 2 && (
                                <div className="step-anim">
                                    <div className="form-section-title">Dirección y Contacto</div>
                                    <div className="form-grid">
                                        <InputField label="Teléfono Móvil" name="telefono" value={formData.telefono} onChange={handleChange} error={fieldErrors.telefono} required icon={<Phone size={14}/>} placeholder="600000000"/>
                                        <div className="full-width-col">
                                            <InputField label="Dirección Postal" name="direccion" value={formData.direccion} onChange={handleChange} error={fieldErrors.direccion} required placeholder="C/ Ejemplo, 1, 1ºA"/>
                                        </div>
                                        <InputField label="Código Postal" name="codigo_postal" value={formData.codigo_postal} onChange={handleChange} error={fieldErrors.codigo_postal} required maxLength={5}/>
                                        <InputField label="Localidad" name="localidad" value={formData.localidad} onChange={handleChange} error={fieldErrors.localidad} required />
                                        <InputField label="Provincia" name="provincia" value={formData.provincia} onChange={handleChange} error={fieldErrors.provincia} required />
                                        <InputField label="Comunidad Autónoma" name="comunidad_autonoma" value={formData.comunidad_autonoma} onChange={handleChange} error={fieldErrors.comunidad_autonoma} required />
                                    </div>
                                </div>
                            )}

                            {/* PASO 3: RELIGIOSOS */}
                            {currentStep === 3 && (
                                <div className="step-anim">
                                    <div className="form-section-title">Datos Sacramentales</div>
                                    <div className="form-grid">
                                        <div className="form-group-custom">
                                            <label>Fecha de Bautismo *</label>
                                            <input type="date" name="fecha_bautismo" value={formData.fecha_bautismo} onChange={handleChange} className={fieldErrors.fecha_bautismo ? 'input-error' : ''} />
                                            {fieldErrors.fecha_bautismo && <span className="error-text">{fieldErrors.fecha_bautismo}</span>}
                                        </div>
                                        <InputField label="Lugar (Localidad)" name="lugar_bautismo" value={formData.lugar_bautismo} onChange={handleChange} error={fieldErrors.lugar_bautismo} required />
                                        <div className="full-width-col">
                                            <InputField label="Parroquia" name="parroquia_bautismo" value={formData.parroquia_bautismo} onChange={handleChange} error={fieldErrors.parroquia_bautismo} required placeholder="Parroquia de..."/>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* PASO 4: BANCARIOS */}
                            {currentStep === 4 && (
                                <div className="step-anim">
                                    <div className="form-section-title">Datos Bancarios</div>
                                    <div className="form-grid">
                                        <div className="full-width-col">
                                            <InputField label="IBAN" name="iban" value={formData.iban} onChange={handleChange} error={fieldErrors.iban} required placeholder="ES00 0000 0000 0000 0000 0000" />
                                        </div>
                                        <SelectField label="Periodicidad Cuota" name="periodicidad" value={formData.periodicidad} onChange={handleChange} options={[{value: 'TRIMESTRAL', label: 'Trimestral'}, {value: 'SEMESTRAL', label: 'Semestral'}, {value: 'ANUAL', label: 'Anual'}]} />
                                        
                                        <div className="form-group-custom checkbox-group">
                                            <label style={{display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer'}}>
                                                <input type="checkbox" name="es_titular" checked={formData.es_titular} onChange={handleChange} />
                                                <span>Confirmo que soy el titular de la cuenta bancaria.</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* PASO 5: AREAS */}
                            {currentStep === 5 && (
                                <div className="step-anim">
                                    <div className="form-section-title">Áreas de Interés (Opcional)</div>
                                    <p className="small-desc">Marque las áreas en las que le gustaría colaborar con la Hermandad.</p>
                                    <div className="areas-grid">
                                        {areasOptions.map(option => (
                                            <label key={option.value} className={`area-card ${formData.areas_interes.includes(option.value) ? 'selected' : ''}`}>
                                                <input 
                                                    type="checkbox" 
                                                    value={option.value}
                                                    checked={formData.areas_interes.includes(option.value)}
                                                    onChange={() => handleAreaChange(option.value)}
                                                    style={{display: 'none'}}
                                                />
                                                {option.label}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* --- BOTONERA DE NAVEGACIÓN --- */}
                            <div className="wizard-actions">
                                {currentStep > 1 && (
                                    <button type="button" className="btn-outline-acto" onClick={handlePrev}>
                                        <ChevronLeft size={16}/> Anterior
                                    </button>
                                )}
                                
                                {currentStep < totalSteps ? (
                                    <button type="button" className="btn-purple btn-next" onClick={handleNext}>
                                        Siguiente <ChevronRight size={16}/>
                                    </button>
                                ) : (
                                    <button type="submit" className="btn-save-acto btn-next" disabled={submitting}>
                                        {submitting ? "Enviando..." : "Finalizar Solicitud"}
                                    </button>
                                )}
                            </div>

                        </form>
                    </div>
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