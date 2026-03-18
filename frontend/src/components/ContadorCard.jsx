import React, { useState, useEffect } from 'react';
import { useCountdown } from '../hooks/useCountdown';
import api from '../api';
import '../styles/ContadorCard.css';

const ContadorCard = () => {
    const [acto, setActo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;

        const fetchProximaEstacion = async () => {
            try {
                const response = await api.get('/api/actos/proxima-estacion/');
                
                if (isMounted) {
                    setActo(response.data);
                }
            } catch (error) {
                if (isMounted) {
                    if (error.response?.status === 404) {
                        setActo(null);
                    } else {
                        console.error("Error al obtener la próxima estación:", error);
                    }
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        fetchProximaEstacion();
        
        return () => { isMounted = false; };
    }, []);

    const { meses, dias, horas, minutos, segundos } = useCountdown(acto?.fecha);

    const formatNumber = (num) => num.toString().padStart(2, '0');

    const timeUnits = [
        { label: 'MESES', value: formatNumber(meses) },
        { label: 'DÍAS', value: formatNumber(dias) },
        { label: 'HORAS', value: formatNumber(horas) },
        { label: 'MINUTOS', value: formatNumber(minutos) },
        { label: 'SEGUNDOS', value: formatNumber(segundos) }
    ];

    if (loading) {
        return (
            <div className="countdown-container card-wrapper">
                <div className="countdown-board">
                    <h2 className="countdown-title">Cargando...</h2>
                </div>
            </div>
        );
    }

    if (!acto) {
        return (
            <div className="countdown-container card-wrapper">
                <div className="countdown-board">
                    <h2 className="countdown-title">Sin Estación Programada</h2>
                </div>
            </div>
        );
    }

    return (
        <div className="countdown-container card-wrapper">
            <div className="countdown-board">
                <h2 className="countdown-title">{acto.nombre}</h2>
                <div className="countdown-timer">
                    {timeUnits.map((unit, index) => (
                        <React.Fragment key={unit.label}>
                            <div className="time-unit">
                                <div className="time-value-box">
                                    {unit.value}
                                </div>
                                <span className="time-label">{unit.label}</span>
                            </div>
                            {index < timeUnits.length - 1 && (
                                <span className="separator">:</span>
                            )}
                        </React.Fragment>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ContadorCard;