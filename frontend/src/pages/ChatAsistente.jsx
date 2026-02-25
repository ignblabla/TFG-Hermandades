import React, { useState, useRef, useEffect } from 'react';
import api from '../api'; // Ajusta esta ruta si api.js está en otra carpeta

const ChatAsistente = () => {
  // Estado para guardar el historial de la conversación
  const [mensajes, setMensajes] = useState([
    {
      id: 1,
      emisor: 'ia',
      texto: '¡Hola, Hermano! Soy el asistente virtual de la Hermandad. ¿En qué puedo ayudarte con los comunicados y noticias oficiales?'
    }
  ]);
  
  const [pregunta, setPregunta] = useState('');
  const [cargando, setCargando] = useState(false);
  
  // Referencia para hacer auto-scroll al último mensaje
  const finalDelChatRef = useRef(null);

  // Auto-scroll cada vez que cambia el array de mensajes
  useEffect(() => {
    finalDelChatRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  const enviarPregunta = async (e) => {
    e.preventDefault();
    if (!pregunta.trim()) return;

    // 1. Añadimos la pregunta del usuario al chat
    const nuevoMensajeUsuario = { id: Date.now(), emisor: 'usuario', texto: pregunta };
    setMensajes((prev) => [...prev, nuevoMensajeUsuario]);
    setPregunta('');
    setCargando(true);

    try {
      // 2. Usamos tu instancia api.js (Axios)
      // La URL base (VITE_API_URL) y el Token ya se añaden automáticamente
      const response = await api.post("api/comunicados/chat/", { 
        pregunta: nuevoMensajeUsuario.texto 
      });

      // 3. Axios guarda la respuesta en response.data
      setMensajes((prev) => [
        ...prev,
        { id: Date.now(), emisor: 'ia', texto: response.data.respuesta }
      ]);

    } catch (error) {
      console.error("Error en el chat:", error);
      
      // Extraemos el mensaje de error de Axios de forma segura
      let mensajeError = "Error al comunicar con la IA.";
      if (error.response && error.response.data && error.response.data.detail) {
        mensajeError = error.response.data.detail;
      } else if (error.message) {
        mensajeError = error.message;
      }

      setMensajes((prev) => [
        ...prev,
        { id: Date.now(), emisor: 'ia', texto: `❌ Vaya, ha ocurrido un error: ${mensajeError}` }
      ]);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] max-w-2xl mx-auto bg-gray-50 border border-gray-200 rounded-xl shadow-lg overflow-hidden">
      
      {/* CABECERA */}
      <div className="bg-purple-800 text-white px-6 py-4 shadow-md z-10">
        <h2 className="text-xl font-bold flex items-center gap-2">
          🤖 Asistente Virtual
        </h2>
        <p className="text-sm text-purple-200">Consultas sobre comunicados oficiales</p>
      </div>

      {/* ÁREA DE MENSAJES */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {mensajes.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.emisor === 'usuario' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                msg.emisor === 'usuario'
                  ? 'bg-purple-600 text-white rounded-tr-none'
                  : 'bg-white text-gray-800 border border-gray-200 shadow-sm rounded-tl-none'
              }`}
              style={{ whiteSpace: 'pre-wrap' }} // Mantiene los saltos de línea de la IA
            >
              {msg.texto}
            </div>
          </div>
        ))}

        {/* Indicador de carga */}
        {cargando && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-500 rounded-2xl rounded-tl-none px-5 py-3 flex items-center gap-2 animate-pulse">
              <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
              <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-75"></span>
              <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-150"></span>
            </div>
          </div>
        )}
        <div ref={finalDelChatRef} />
      </div>

      {/* ZONA DE INPUT */}
      <div className="bg-white p-4 border-t border-gray-200">
        <form onSubmit={enviarPregunta} className="flex gap-2">
          <input
            type="text"
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            placeholder="Escribe aquí tu duda..."
            disabled={cargando}
            className="flex-1 border border-gray-300 rounded-full px-5 py-3 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={cargando || !pregunta.trim()}
            className="bg-purple-600 text-white rounded-full px-6 py-3 font-semibold hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Enviar
          </button>
        </form>
      </div>

    </div>
  );
};

export default ChatAsistente;