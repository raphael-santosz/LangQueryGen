'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, PenSquare, ChevronUp, LogOut, User, Plus } from 'lucide-react';
import { signOut, onAuthStateChanged, User as FirebaseUser } from 'firebase/auth';
import { doc, getDoc } from 'firebase/firestore';
import { auth, db } from '@/lib/firebase';
import type { LucideProps } from 'lucide-react';

// Tipagem para as mensagens
interface Message {
  sender: 'user' | 'assistant';
  text: string;
  isWelcome?: boolean;
}

// Tipagem para as conversas
interface Conversation {
  id: number;
  title: string;
  messages: Message[];
}

// Tipagem para as props do IconButton
interface IconButtonProps {
  icon: React.ComponentType<LucideProps>;
  onClick: () => void;
  className?: string;
  ariaLabel: string;
}

// Componente IconButton
const IconButton: React.FC<IconButtonProps & { size?: number }> = ({ icon: Icon, onClick, className, ariaLabel, size = 20 }) => (
  <button
    onClick={onClick}
    className={`p-2 rounded-lg transition-colors ${className} hover:bg-gray-500 focus:outline-none`}
    aria-label={ariaLabel}
  >
    <Icon size={size} className="text-white" />
  </button>
);

export default function ChatInterface() {
  const t = useTranslations('Chat');
  const router = useRouter();
  const locale = useLocale();

  const [input, setInput] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<number | null>(null);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState<boolean>(false);
  const [isConversationsPopupOpen, setIsConversationsPopupOpen] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const conversationsPopupRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [token, setToken] = useState<string>('');
  const [userEmail, setUserEmail] = useState<string>('');
  const [userPosition, setUserPosition] = useState<string>('');

  // Carregar e-mail, position do usuário logado e token
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user: FirebaseUser | null) => {
      if (user) {
        setUserEmail(user.email || t('user', { defaultMessage: 'User' }));
        user.getIdToken().then((idToken) => setToken(idToken)).catch((error) => {
          console.error('Erro ao obter token:', error);
          setError(t('authError', { defaultMessage: 'Authentication error.' }));
        });

        // Buscar o campo position do Firestore
        const fetchUserPosition = async () => {
          try {
            const userDocRef = doc(db, 'Users', user.uid);
            const userDoc = await getDoc(userDocRef);
            if (userDoc.exists()) {
              const data = userDoc.data();
              setUserPosition(data.position || t('unknownPosition', { defaultMessage: 'Unknown' }));
            } else {
              setUserPosition(t('unknownPosition', { defaultMessage: 'Unknown' }));
            }
          } catch (error) {
            console.error('Erro ao buscar position do usuário:', error);
            setError(t('firestoreError', { defaultMessage: 'Error fetching user data.' }));
          }
        };
        fetchUserPosition();
      } else {
        // Redirecionar para login se não houver usuário autenticado
        router.push(`/${locale}/login`);
      }
    });
    return () => unsubscribe();
  }, [router, locale, t]);

  // Carregar conversas do localStorage apenas no cliente
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedConversations = localStorage.getItem('conversations');
      if (savedConversations) {
        setConversations(JSON.parse(savedConversations));
      }
    }
  }, []);

  // Salvar conversas no localStorage sempre que forem atualizadas
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }
  }, [conversations]);

  // Scroll automático para a última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Fechar o menu do usuário e o pop-up de conversas ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
      if (
        conversationsPopupRef.current &&
        !conversationsPopupRef.current.contains(event.target as Node)
      ) {
        setIsConversationsPopupOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Adicionar animação do cursor de digitação
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
        margin-left: 4px;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  const handleRefresh = () => {
    if (messages.length > 0) {
      const newConversation: Conversation = {
        id: conversations.length,
        title: messages[0].text.substring(0, 30),
        messages: messages,
      };
      setConversations([newConversation, ...conversations]);
    }
    setMessages([]);
    setActiveConversation(null);
    setSelectedFiles([]);
  };

const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/rtf',
    'text/rtf',
    'text/plain',
  ];
  const allowedExtensions = ['.pdf', '.docx', '.txt', '.md', '.rtf'];
  const files = event.target.files;
  if (files) {
    const fileArray = Array.from(files);
    const validFiles = fileArray.filter((file) => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      return allowedTypes.includes(file.type) || allowedExtensions.includes(extension);
    });

    if (validFiles.length < fileArray.length) {
      alert(t('invalidFileType', { defaultValue: 'Only PDF, DOCX, TXT, MD, and RTF files are allowed.' }));
    }

    setSelectedFiles((prev) => [...prev, ...validFiles]);
  }
};

  const sendMessage = async () => {
    console.log('Enviando mensagem - Token:', token);
    console.log('Input:', input);
    console.log('Selected Files:', selectedFiles);
    if (!input.trim() && selectedFiles.length === 0) {
      console.log('Nenhum input ou arquivo selecionado');
      return;
    }

    // Criar a mensagem do usuário
    let messageText = input.trim() || '';
    if (selectedFiles.length > 0) {
      const fileNames = selectedFiles.map((file) => file.name).join(', ');
      messageText += messageText
        ? `\n${t('uploadedFiles', { defaultMessage: 'Uploaded files: ' })}${fileNames}`
        : `${t('uploadedFiles', { defaultMessage: 'Uploaded files: ' })}${fileNames}`;
    }

    const newMessages: Message[] = [...messages, { sender: 'user', text: messageText }];
    setMessages(newMessages);
    setInput('');
    setSelectedFiles([]);
    setIsTyping(true);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';

    // Validar token
    // if (!token) {
    //   console.log('Erro: Token ausente');
    //   setError(t('authError', { defaultMessage: 'Authentication token missing.' }));
    //   setIsTyping(false);
    //   return;
    // }

    // Criar FormData para enviar mensagem, token e arquivos
    const formData = new FormData();
    formData.append('question', input || 'File upload');
    formData.append('token', token);
    selectedFiles.forEach((file) => formData.append('file', file));

    try {
      console.log('Enviando requisição para API');
      const response = await fetch(
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/generate-query',
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        console.log('Resposta da API não OK:', response.status);
        throw new Error(t('requestError', { defaultMessage: 'Failed to send message.' }));
      }

      const result = await response.json();
      console.log('Resposta da API:', result);
      const outputValue =
        result.output || t('noResponse', { defaultMessage: 'No response received' });

      // Animação de digitação
      let visibleText = '';
      const fullText = outputValue;
      const intervalId = setInterval(() => {
        if (visibleText.length < fullText.length) {
          visibleText += fullText[visibleText.length];
          setMessages([...newMessages, { sender: 'assistant', text: visibleText }]);
        } else {
          clearInterval(intervalId);
          setIsTyping(false);
        }
      }, 50);
    } catch (error) {
      console.error('Erro ao enviar a mensagem:', error);
      setError(t('errorSendingMessage', { defaultMessage: 'Error sending message. Please try again.' }));
      setIsTyping(false);
    }
  };

  const loadConversation = (id: number) => {
    const conversation = conversations.find((conv) => conv.id === id);
    if (conversation) {
      setMessages(conversation.messages);
      setActiveConversation(id);
      setIsConversationsPopupOpen(false);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      sessionStorage.removeItem('authToken');
      sessionStorage.removeItem('userRole');
      localStorage.removeItem('conversations');
      router.push(`/${locale}/login`);
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  };

  // Variantes de animação para mensagens
  const messageVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  };

  // Variantes de animação para o pop-up
  const popupVariants = {
    hidden: { opacity: 0, y: -10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  };

  return (
    <div className="flex min-h-screen bg-gray-100 text-gray-900 font-sans">
      {/* Main Content */}
      <main className="flex-1 flex flex-col w-full">
        <header className="bg-gray-900 shadow p-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <IconButton
              icon={PenSquare}
              onClick={handleRefresh}
              ariaLabel={t('newChat', { defaultMessage: 'New chat' })}
            />
            <IconButton
              icon={Menu}
              onClick={() => setIsConversationsPopupOpen(!isConversationsPopupOpen)}
              ariaLabel={t('openConversations', { defaultMessage: 'Open previous conversations' })}
            />
            {isConversationsPopupOpen && (
              <motion.div
                ref={conversationsPopupRef}
                className="absolute top-12 left-0 z-10 w-64 bg-white rounded-lg shadow-lg border border-gray-200"
                variants={popupVariants}
                initial="hidden"
                animate="visible"
              >
                <div className="p-4">
                  {conversations.length === 0 ? (
                    <p className="text-gray-500 text-sm">
                      {t('noConversations', { defaultMessage: 'No previous conversations' })}
                    </p>
                  ) : (
                    conversations.map((conv) => (
                      <button
                        key={conv.id}
                        onClick={() => loadConversation(conv.id)}
                        className="block w-full text-left p-2 hover:bg-gray-100 rounded-md text-gray-700 text-sm transition-colors"
                      >
                        {conv.title}
                      </button>
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </div>
          <div className="relative flex items-center gap-2" ref={userMenuRef}>
            <IconButton
              icon={User}
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              ariaLabel={"Default"}
              className="text-white"
              size={25}
            />
            {isUserMenuOpen && (
              <motion.div
                className="absolute top-12 right-0 z-10 w-48 bg-white rounded-lg shadow-lg border border-gray-200"
                variants={popupVariants}
                initial="hidden"
                animate="visible"
              >
                <div className="p-4">
                  <div className="flex flex-col mb-4">
                    <span className="text-sm text-gray-900">
                      {userEmail || t('user', { defaultMessage: 'User' })}
                    </span>
                    <span className="text-xs text-gray-500 text-right">
                      {userPosition || t('unknownPosition', { defaultMessage: 'Unknown' })}
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-2 text-red-500 hover:text-red-600 transition-colors w-full"
                  >
                    <LogOut size={20} />
                    <span>{t('logout', { defaultMessage: 'Logout' })}</span>
                  </button>
                </div>
              </motion.div>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 bg-gray-100">
          <div className="max-w-3xl mx-auto space-y-4">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  className={`${message.sender === 'user' ? 'text-right' : 'text-left'}`}
                  variants={messageVariants}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                >
                  <div
                    className={`inline-block p-3 rounded-lg shadow-sm ${message.isWelcome
                      ? 'text-center text-xl font-semibold text-gray-900 bg-transparent shadow-none'
                      : message.sender === 'user'
                        ? 'bg-black text-white'
                        : 'bg-white text-gray-900'
                      }`}
                  >
                    {message.text}
                  </div>
                </motion.div>
              ))}
              {isTyping && (
                <motion.div
                  className="text-left"
                  variants={messageVariants}
                  initial="hidden"
                  animate="visible"
                >
                  <div className="inline-block p-3 rounded-lg bg-white shadow-sm text-gray-900 cursor">
                    {t('typing', { defaultMessage: 'Typing...' })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            {error && (
              <motion.div
                className="text-center p-3 bg-red-100 text-red-600 rounded-lg"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {error}
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="p-3 bg-gray-900 shadow">
          <div className="max-w-2xl mx-auto flex items-center bg-gray-100 rounded-lg">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 bg-black text-white hover:bg-gray-700 focus:outline-none rounded-l-lg transition-colors"
              aria-label={t('uploadFile', { defaultMessage: 'Upload file' })}
            >
              <Plus size={24} />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              multiple
              className="hidden"
            />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t('writeQuestion', { defaultMessage: 'Write your question...' })}
              className="flex-1 p-3 bg-transparent text-gray-900 focus:outline-none"
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              aria-label={t('messageInput', { defaultMessage: 'Message input' })}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() && selectedFiles.length === 0}
              className="p-2 bg-black text-white rounded-r-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors disabled:opacity-50"
              aria-label={t('sendMessage', { defaultMessage: 'Send message' })}
            >
              <ChevronUp size={24} />
            </button>
          </div>
          {selectedFiles.length > 0 && (
            <div className="mt-2 text-sm text-gray-700">
              {t('selectedFiles', { defaultMessage: 'Selected files: ' })}
              {selectedFiles.map((file) => file.name).join(', ')}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}