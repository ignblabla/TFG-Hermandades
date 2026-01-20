import React from 'react';
import '../../styles/AdminDashboard/DashboardCard.css';

const DashboardCard = ({ title, value }) => {
    return (
        <article className="dashboard-card">
            <h3 className="dashboard-card__title">{title}</h3>
            <div className="dashboard-card__content">
                <span className="dashboard-card__value">{value}</span>
            </div>
        </article>
    );
};

export const DashboardStats = () => {
    const statsData = [
        { 
            id: 1, 
            title: 'Total de Hermanos', 
            value: '2.450', 
        },
        { 
            id: 2, 
            title: 'Altas este año', 
            value: '142', 
        },
        { 
            id: 3, 
            title: 'Pendientes de Pago', 
            value: '45', 
        },
        { 
            id: 4, 
            title: 'Próximos Cumpleaños', 
            value: '28', 
        },
    ];

    return (
        <section className="dashboard-grid">
            {statsData.map((stat) => (
                <DashboardCard
                    key={stat.id}
                    title={stat.title}
                    value={stat.value}
                />
            ))}
        </section>
    );
};

export default DashboardCard;