import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api"; // Asumo que tienes tu instancia de axios aquí
import "../styles/HazteHermano.css"; // CSS específico que crearemos abajo
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, User, MapPin, Church, CreditCard, Lock, Mail, Phone, Calendar } from "lucide-react";

function HazteHermano() {
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [generalError, setGeneralError] = useState("");
    const [fieldErrors, setFieldErrors] = useState({}); // Para errores específicos por campo
    const [success, setSuccess] = useState(false);

    const [formData, setFormData] = useState({
        dni: "",
        email: "",
        password: "",
        confirmPassword: "",
        
        nombre: "",
        primer_apellido: "",
        segundo_apellido: "",
        fecha_nacimiento: "",
        genero: "MASCULINO",
        estado_civil: "SOLTERO",
        telefono: "",

        direccion: "",
        codigo_postal: "",
        localidad: "",
        provincia: "",
        comunidad_autonoma: "",

        lugar_bautismo: "",
        fecha_bautismo: "",
        parroquia_bautismo: "",

        iban: "",
        periodicidad: "TRIMESTRAL",
        es_titular: true,

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

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setGeneralError("");
        setFieldErrors({});

        // Validación básica de contraseñas
        if (formData.password !== formData.confirmPassword) {
            setGeneralError("Las contraseñas no coinciden.");
            setSubmitting(false);
            return;
        }

        try {
            const { confirmPassword, ...payload } = formData;
            
            await api.post("api/hermanos/registro/", payload);

            setSuccess(true);
            setTimeout(() => navigate("/login"), 3000);

        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                // Si es un error de validación de campos, lo guardamos en fieldErrors
                setFieldErrors(data);
                
                if (data.detail) setGeneralError(data.detail);
                else if (data.non_field_errors) setGeneralError(data.non_field_errors[0]);
                else setGeneralError("Por favor, revise los errores marcados en el formulario.");
            } else {
                setGeneralError("Error de conexión. Inténtelo más tarde.");
            }
        } finally {
            setSubmitting(false);
        }
    };

    if (success) {
        return (
            <div className="site-wrapper success-view">
                <div className="card-container-area" style={{textAlign: 'center', padding: '50px'}}>
                    <img src={logoEscudo} alt="Escudo" style={{width: '80px', marginBottom: '20px'}}/>
                    <h2 style={{color: '#16a34a'}}>¡Solicitud Recibida!</h2>
                    <p>Su solicitud de ingreso ha sido registrada correctamente.</p>
                    <p>Recibirá una notificación cuando Secretaría apruebe su alta y se le asigne su número de hermano.</p>
                    <button className="btn-purple" onClick={() => navigate("/login")} style={{marginTop: '20px'}}>
                        Ir al Acceso de Hermanos
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="site-wrapper">
            {/* NAVBAR SIMPLIFICADA PARA REGISTRO */}
            <nav className="navbar">
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo San Gonzalo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SOLICITUD DE INGRESO</span>
                    </div>
                </div>
                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
                <div className="nav-buttons-desktop">
                    <button className="btn-outline" onClick={() => navigate("/")}>Volver al inicio</button>
                    <button className="btn-purple" onClick={() => navigate("/login")}>Ya soy hermano</button>
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area card-wide"> {/* card-wide clase nueva css */}
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Hazte Hermano</h1>
                            <button className="btn-back-area" onClick={() => navigate("/")}>
                                <ArrowLeft size={16} /> Cancelar
                            </button>
                        </div>
                        <p className="description-area">
                            Rellene el siguiente formulario para solicitar su ingreso en la nómina de la Hermandad.
                        </p>
                    </header>

                    {generalError && (
                        <div className="alert-box error">
                            {generalError}
                        </div>
                    )}

                    <form className="register-form" onSubmit={handleSubmit}>
                        
                        {/* SECCIÓN 1: ACCESO Y DATOS PERSONALES */}
                        <div className="form-section-title"><User size={18}/> Datos Personales y de Acceso</div>
                        <div className="form-grid">
                            <InputField label="DNI (Será su usuario)" name="dni" value={formData.dni} onChange={handleChange} error={fieldErrors.dni} required placeholder="12345678A" />
                            <InputField label="Correo Electrónico" name="email" type="email" value={formData.email} onChange={handleChange} error={fieldErrors.email} required />
                            
                            <InputField label="Nombre" name="nombre" value={formData.nombre} onChange={handleChange} error={fieldErrors.nombre} required />
                            <InputField label="Primer Apellido" name="primer_apellido" value={formData.primer_apellido} onChange={handleChange} error={fieldErrors.primer_apellido} required />
                            <InputField label="Segundo Apellido" name="segundo_apellido" value={formData.segundo_apellido} onChange={handleChange} error={fieldErrors.segundo_apellido} required />
                            
                            <div className="form-group-custom">
                                <label>Fecha de Nacimiento</label>
                                <input type="date" name="fecha_nacimiento" value={formData.fecha_nacimiento} onChange={handleChange} required className={fieldErrors.fecha_nacimiento ? 'input-error' : ''} />
                                {fieldErrors.fecha_nacimiento && <span className="error-text">{fieldErrors.fecha_nacimiento}</span>}
                            </div>

                            <SelectField label="Género" name="genero" value={formData.genero} onChange={handleChange} options={[{value: 'MASCULINO', label: 'Masculino'}, {value: 'FEMENINO', label: 'Femenino'}]} />
                            <SelectField label="Estado Civil" name="estado_civil" value={formData.estado_civil} onChange={handleChange} options={[{value: 'SOLTERO', label: 'Soltero'}, {value: 'CASADO', label: 'Casado'}, {value: 'SEPARADO', label: 'Separado'}, {value: 'VIUDO', label: 'Viudo'}]} />
                            
                            <InputField label="Contraseña" name="password" type="password" value={formData.password} onChange={handleChange} error={fieldErrors.password} required icon={<Lock size={14}/>}/>
                            <InputField label="Repetir Contraseña" name="confirmPassword" type="password" value={formData.confirmPassword} onChange={handleChange} required icon={<Lock size={14}/>}/>
                        </div>

                        {/* SECCIÓN 2: CONTACTO */}
                        <div className="form-section-title"><MapPin size={18}/> Dirección y Contacto</div>
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

                        {/* SECCIÓN 3: RELIGIOSOS */}
                        <div className="form-section-title"><Church size={18}/> Datos Sacramentales (Bautismo)</div>
                        <div className="form-grid">
                            <div className="form-group-custom">
                                <label>Fecha de Bautismo</label>
                                <input type="date" name="fecha_bautismo" value={formData.fecha_bautismo} onChange={handleChange} required className={fieldErrors.fecha_bautismo ? 'input-error' : ''} />
                                {fieldErrors.fecha_bautismo && <span className="error-text">{fieldErrors.fecha_bautismo}</span>}
                            </div>
                            <InputField label="Lugar (Localidad)" name="lugar_bautismo" value={formData.lugar_bautismo} onChange={handleChange} error={fieldErrors.lugar_bautismo} required />
                            <div className="full-width-col">
                                <InputField label="Parroquia" name="parroquia_bautismo" value={formData.parroquia_bautismo} onChange={handleChange} error={fieldErrors.parroquia_bautismo} required placeholder="Parroquia de..."/>
                            </div>
                        </div>

                        {/* SECCIÓN 4: BANCARIOS */}
                        <div className="form-section-title"><CreditCard size={18}/> Datos Bancarios</div>
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

                        {/* SECCIÓN 5: ÁREAS DE INTERÉS */}
                        <div className="form-section-title"><Calendar size={18}/> Áreas de Interés (Opcional)</div>
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

                        <div className="form-actions-acto" style={{marginTop: '30px'}}>
                            <button type="button" className="btn-cancel-acto" onClick={() => navigate("/")}>Cancelar</button>
                            <button type="submit" className="btn-save-acto btn-large" disabled={submitting}>
                                {submitting ? "Enviando Solicitud..." : "Enviar Solicitud de Ingreso"}
                            </button>
                        </div>

                    </form>
                </div>
            </main>
        </div>
    );
}

// Componentes auxiliares para reducir código repetitivo
const InputField = ({ label, name, value, onChange, error, type = "text", required = false, placeholder, icon, maxLength }) => (
    <div className="form-group-custom">
        <label>{label} {required && "*"}</label>
        <div className={`input-wrapper ${error ? 'has-error' : ''}`}>
            {icon && <span className="input-icon">{icon}</span>}
            <input 
                type={type} 
                name={name} 
                value={value} 
                onChange={onChange} 
                placeholder={placeholder}
                required={required}
                maxLength={maxLength}
                className={icon ? 'with-icon' : ''}
            />
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