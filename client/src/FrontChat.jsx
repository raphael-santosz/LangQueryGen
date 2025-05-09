import React, { useState, useEffect, useRef } from "react";
import { Menu, PenSquare, ChevronUp, LogOut, User, LogOutIcon } from 'lucide-react';

import { useNavigate, useLocation } from 'react-router-dom';
import { auth, db } from './Services/FirebaseConfig.js';
import { signOut } from 'firebase/auth';

const IconButton = ({ icon: Icon, onClick, className }) => (
  <button onClick={onClick} className={`p-2 hover:bg-gray-700 rounded ${className}`}>
    <Icon size={20} />
  </button>
);

export default function ChatInterface() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  const [token, setToken] = useState("");
  const location = useLocation();
  const [userEmail, setUserEmail] = useState('');
  const [selectedFile, setSelectedFile] = useState(null); // Estado para armazenar o nome do arquivo selecionado

  const handleRefresh = () => {
    if (messages.length > 0) {
      const newConversation = {
        id: conversations.length,
        title: messages[0].text.substring(0, 30),
        messages: messages,
      };
      setConversations([newConversation, ...conversations]);
    }
    setMessages([]);
    setActiveConversation(null);
  };

  const email = location.state?.email;
  const navigate = useNavigate();

  const sendMessage = async () => {
    if (!input.trim() && !selectedFile) return; // Não envia se não houver texto nem arquivo
  
    // Criar a nova mensagem do usuário
    let messageText = input;
    if (selectedFile) {
      messageText += `\nArquivo selecionado: ${selectedFile}`; // Adiciona o nome do arquivo à mensagem
    }
  
    const newMessages = [...messages, { sender: "user", text: messageText }];
    setMessages(newMessages);
    setInput("");
    setSelectedFile(null); // Limpa o arquivo selecionado após enviar a mensagem
    setIsTyping(true);
  
    // Verificar se um arquivo foi selecionado
    const fileInput = document.getElementById("file-upload");
    const file = fileInput.files[0];
  
    // Criar FormData para enviar a mensagem, o arquivo e o token
    const formData = new FormData();
    formData.append('question', input);
    formData.append('token', token); // Adiciona o token ao FormData
    if (file) {
      formData.append('file', file);
    }
  
    try {
      // Enviar a requisição POST para o backend com FormData
      const response = await fetch("http://localhost:5000/generate-query", {
        method: "POST",
        body: formData, // Envia o FormData com a mensagem, token e arquivo
      });
  
      // Processar a resposta do servidor
      const result = await response.json();
      const outputValue = result.output || "Sem resposta recebida";
  
      let visibleText = "";
      const fullText = outputValue;
  
      // Exibir a resposta do servidor no chat com animação de digitação
      const intervalId = setInterval(() => {
        if (visibleText.length < fullText.length) {
          visibleText += fullText[visibleText.length];
          setMessages([...newMessages, { sender: "assistant", text: visibleText }]);
        } else {
          clearInterval(intervalId);
          setIsTyping(false);
        }
      }, 50); // Intervalo de animação de 50ms para cada letra
  
    } catch (error) {
      console.error("Erro enviando a mensagem:", error);
      setIsTyping(false); // Parar a animação caso ocorra um erro
    }
  };  

  const loadConversation = (id) => {
    const conversation = conversations.find(conv => conv.id === id);
    if (conversation) {
      setMessages(conversation.messages);
      setActiveConversation(id);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      sessionStorage.removeItem('authToken');
      sessionStorage.removeItem('userRole');
      navigate('/login');
    } catch (error) {
      console.error("Erro ao fazer logout:", error);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file.name); // Armazena o nome do arquivo selecionado
    }
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes blink {
        0% { opacity: 0; }
        50% { opacity: 1; }
        100% { opacity: 0; }
      }
      .cursor::after {
        content: '|';
        animation: blink 1s infinite;
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);


  useEffect(() => {
    const emailFromState = location.state?.email;
    const tokenCryptFromState = location.state?.tokenCrypt;
    
    const params = new URLSearchParams(location.search);
    const emailFromParams = params.get('email');
  
    setUserEmail(emailFromState || emailFromParams || '');
    setToken(tokenCryptFromState || '');
  }, [location]);

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 overflow-hidden font-sans">
      <aside
        className={`flex-shrink-0 bg-gray-800 p-0 flex flex-col transition-all duration-300 ease-in-out ${
          isSidebarOpen ? 'w-64' : 'w-0'
        }`}
      >
        <div className="flex-grow overflow-y-auto pt-14">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => loadConversation(conv.id)}
              className="flex items-center w-full text-left p-2 hover:bg-gray-700 rounded mb-2"
              style={{
                maskImage: 'linear-gradient(to left, transparent, black 20px)',
                WebkitMaskImage: 'linear-gradient(to left, transparent, black 20px)',
              }}
            >
              <span className="truncate">{conv.title}</span>
            </button>
          ))}
        </div>

        <div className="p-6 mt-auto pt-8 border-t border-gray-700">
          <button onClick={handleLogout} className="flex items-center space-x-2 text-red-500 hover:text-red-600 ">
            <LogOutIcon className="h-5 w-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col w-full">
        <header className="bg-gray-800 p-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <IconButton icon={Menu} onClick={() => setIsSidebarOpen(!isSidebarOpen)} />
            <IconButton icon={PenSquare} onClick={handleRefresh} title="New chat" />
          </div>
          <div className="relative flex items-center" ref={userMenuRef}>
            <User size={20} className="mr-2 text-gray-400" />
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="text-sm text-gray-400 hover:text-gray-200"
            >
              {userEmail}
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-3xl mx-auto space-y-8">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`${message.sender === "user" ? "text-right" : "text-left"}`}
              >
                <div
                  className={`inline-block p-3 rounded-lg ${
                    message.sender === "user" ? "bg-blue-700" : "bg-gray-600"
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="text-left">
                <div className="inline-block p-3 rounded-lg bg-gray-600 cursor" />
              </div>
            )}
          </div>
        </div>
        <div className="p-4 bg-gray-800">
        <div className="max-w-3xl mx-auto flex items-center bg-gray-700 rounded-lg">
          {/* Exibir o nome do arquivo selecionado */}
          {selectedFile && (
            <span className="text-white mr-4">Arquivo selecionado: {selectedFile}</span>
          )}

          {/* Botão de anexar arquivo */}
          <label htmlFor="file-upload" className="p-2 bg-gray-600 rounded-l-lg hover:bg-gray-500 cursor-pointer">
            <span className="text-white">📎</span>
            <input
              type="file"
              id="file-upload"
              className="hidden"
              onChange={(e) => handleFileUpload(e)}  // Função para lidar com o envio do arquivo
            />
          </label>

          {/* Campo de entrada de texto */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escreva sua dúvida ..."
            className="flex-1 p-3 bg-transparent text-white focus:outline-none"
            onKeyPress={(e) => e.key === "Enter" && sendMessage()} // Enviar mensagem ao pressionar "Enter"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() && !selectedFile} // Desabilita o botão se não houver texto nem arquivo
            className="p-2 bg-white rounded-r-lg hover:bg-gray-400 cursor-pointer"
          >
            <ChevronUp size={24} className="text-gray-800" />
          </button>
        </div>
      </div>
      </main>
    </div>
  );
}
