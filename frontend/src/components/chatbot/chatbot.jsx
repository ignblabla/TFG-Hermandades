import React, { useState, useRef, useEffect } from 'react';
import { Bot, X, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../../api';
import '../chatbot/chatbot.css';

const ChatBot = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [messages, setMessages] = useState([
        { text: "¡Hola, Hermano! 👋 Soy el IAmador. ¿En qué puedo ayudarte hoy?", isBot: true }
    ]);

    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    const handleSendMessage = async () => {
        if (!inputValue.trim()) return;

        const userText = inputValue.trim();

        setMessages(prev => [...prev, { text: userText, isBot: false }]);
        setInputValue("");
        setIsLoading(true);

        try {
            const response = await api.post("api/comunicados/chat/", { 
                pregunta: userText 
            });

            setMessages(prev => [...prev, { text: response.data.respuesta, isBot: true }]);
            
        } catch (error) {
            console.error("Error al consultar la IA:", error);
            setMessages(prev => [...prev, { 
                text: "Lo siento, ha ocurrido un error al conectar con el servidor. Por favor, inténtalo más tarde.", 
                isBot: true 
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    };

    return (
        <div className="aura-container">
            
            {!isOpen && (
                <div className="aura-fab" onClick={() => setIsOpen(true)}>
                    <Bot size={28} color="white" />
                </div>
            )}

            {isOpen && (
                <>
                    <div className="aura-window">
                        <div className="aura-header">
                            <div className="aura-header-left">
                                <div className="aura-avatar-main">
                                    <Bot size={24} color="white" />
                                    <div className="aura-status-dot"></div>
                                </div>
                                <div className="aura-header-info">
                                    <div className="aura-title">El IAmador</div>
                                    <div className="aura-status">En línea • Respuesta instantánea</div>
                                </div>
                            </div>

                            <div className="aura-close" onClick={() => setIsOpen(false)}>
                                <X size={20} color="white" strokeWidth={2} />
                            </div>
                        </div>

                        <div className="aura-body">
                            {messages.map((msg, index) => (
                                <div key={index} className={`aura-msg-row ${msg.isBot ? '' : 'aura-row-reverse'}`}>
                                    {msg.isBot && (
                                        <div className="aura-avatar-sm">
                                            <Bot size={18} color="#8899a6" />
                                        </div>
                                    )}
                                    <div className={`aura-bubble ${msg.isBot ? 'aura-bot' : 'aura-user'}`}>
                                        {msg.isBot ? (
                                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                                        ) : (
                                            msg.text
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="aura-msg-row">
                                    <div className="aura-avatar-sm">
                                        <Bot size={18} color="#8899a6" />
                                    </div>
                                    <div className="aura-bubble aura-bot" style={{ fontStyle: 'italic', color: '#888' }}>
                                        Escribiendo...
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>

                        <div className="aura-footer">
                            <div className="aura-input-wrapper">
                                <input 
                                    type="text" 
                                    placeholder="Escribe tu mensaje..." 
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    disabled={isLoading}
                                />
                                <button 
                                    className="aura-send-btn" 
                                    onClick={handleSendMessage}
                                    disabled={isLoading || !inputValue.trim()}
                                >
                                    <Send size={20} color={inputValue.trim() ? "#1884f7" : "#a0cfff"} />
                                </button>
                            </div>
                            <div className="aura-powered">Powered by Hermandad de San Gonzalo</div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default ChatBot;