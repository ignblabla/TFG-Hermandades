import { useState, useEffect } from 'react';

export const useCountdown = (targetDate) => {
    const [timeLeft, setTimeLeft] = useState({
        meses: 0,
        dias: 0,
        horas: 0,
        minutos: 0,
        segundos: 0,
    });

    useEffect(() => {
        if (!targetDate) return;

        const calculateTimeLeft = () => {
            const now = new Date();
            const target = new Date(targetDate);
            const difference = target - now;

            if (difference <= 0) {
                return { meses: 0, dias: 0, horas: 0, minutos: 0, segundos: 0 };
            }

            let meses = (target.getFullYear() - now.getFullYear()) * 12 + (target.getMonth() - now.getMonth());
            let tempDate = new Date(now);
            tempDate.setMonth(tempDate.getMonth() + meses);

            if (target < tempDate) {
                meses--;
                tempDate = new Date(now);
                tempDate.setMonth(tempDate.getMonth() + meses);
            }

            const diffAfterMonths = target - tempDate;

            return {
                meses,
                dias: Math.floor(diffAfterMonths / (1000 * 60 * 60 * 24)),
                horas: Math.floor((diffAfterMonths / (1000 * 60 * 60)) % 24),
                minutos: Math.floor((diffAfterMonths / 1000 / 60) % 60),
                segundos: Math.floor((diffAfterMonths / 1000) % 60)
            };
        };

        setTimeLeft(calculateTimeLeft());

        const timer = setInterval(() => {
            setTimeLeft(calculateTimeLeft());
        }, 1000);

        return () => clearInterval(timer);
    }, [targetDate]);

    return timeLeft;
};