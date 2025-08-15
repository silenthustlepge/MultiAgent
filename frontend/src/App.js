import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AGENT_COLORS = {
  strategist: '#3B82F6',
  creator: '#10B981', 
  analyst: '#F59E0B',
  visualizer: '#EF4444'
};

const App = () => {
  const [agents, setAgents] = useState({});
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newTopic, setNewTopic] = useState('');
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [apiStats, setApiStats] = useState(null);
  const [imagePrompt, setImagePrompt] = useState('');
  
  // New autonomous collaboration states
  const [collaborationMode, setCollaborationMode] = useState('single_turn');
  const [isCollaborating, setIsCollaborating] = useState(false);
  const [consensusStatus, setConsensusStatus] = useState(null);
  const [currentRound, setCurrentRound] = useState(0);
  const [maxRounds, setMaxRounds] = useState(8);
  
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Load agents on component mount
  useEffect(() => {
    loadAgents();
    loadApiStats();
  }, []);

  // Cleanup function
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // Add debug logging for messages
  useEffect(() => {
    console.log('Messages state updated:', messages);
  }, [messages]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`);
      setAgents(response.data);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const loadApiStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setApiStats(response.data);
    } catch (error) {
      console.error('Error loading API stats:', error);
    }
  };

  const [isPolling, setIsPolling] = React.useState(false);
  const [lastMessageCount, setLastMessageCount] = React.useState(0);
  const pollingRef = React.useRef(null);

  const setupRealTimeUpdates = (conversationId) => {
    // Close existing connections
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    // Try WebSocket first
    const setupWebSocket = () => {
      let wsUrl;
      if (BACKEND_URL.includes('emergentagent.com')) {
        wsUrl = `wss://keyvault-bulk.preview.emergentagent.com/api/ws/${conversationId}`;
      } else {
        wsUrl = `${BACKEND_URL.replace('http', 'ws')}/api/ws/${conversationId}`;
      }
      
      console.log('🔌 Attempting WebSocket connection:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        setIsPolling(false);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'connection_established') {
            console.log('✅ WebSocket connection confirmed:', data.data.message);
          } else if (data.type === 'agent_message' || data.type === 'user_message') {
            console.log('📨 WebSocket message received:', data.data);
            setMessages(prev => {
              const newMessages = [...prev, data.data];
              setLastMessageCount(newMessages.length);
              return newMessages;
            });
          } else if (data.type === 'consensus_update') {
            console.log('🎯 Consensus update received:', data.data);
            setConsensusStatus(data.data.consensus);
            setCurrentRound(data.data.round);
          } else if (data.type === 'consensus_final') {
            console.log('✅ Final consensus reached:', data.data);
            setMessages(prev => [...prev, data.data]);
            setIsCollaborating(false);
            setConsensusStatus({ reached: true, final: true });
          } else if (data.type === 'collaboration_concluded') {
            console.log('⏰ Collaboration concluded:', data.data);
            setMessages(prev => [...prev, data.data]);
            setIsCollaborating(false);
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.warn('⚠️ WebSocket error, falling back to polling:', error);
        setupPolling(conversationId);
      };

      wsRef.current.onclose = (event) => {
        if (event.code === 1006 || event.code === 1011 || event.code === 1005) {
          console.warn('⚠️ WebSocket connection failed (403/auth issue), using polling fallback');
          setupPolling(conversationId);
        } else {
          console.log('🔌 WebSocket connection closed normally:', event.code, event.reason);
        }
      };
    };

    // Polling fallback for restricted environments
    const setupPolling = (conversationId) => {
      console.log('🔄 Setting up polling fallback for real-time updates');
      setIsPolling(true);
      
      const pollMessages = async () => {
        try {
          const response = await axios.get(`${API}/conversation/${conversationId}/poll`);
          const { messages } = response.data;
          
          if (messages.length !== lastMessageCount) {
            console.log(`🔄 Polling: ${messages.length} messages (was ${lastMessageCount})`);
            setMessages(messages);
            setLastMessageCount(messages.length);
          }
        } catch (error) {
          console.error('❌ Polling error:', error);
        }
      };

      // Poll every 2 seconds
      pollingRef.current = setInterval(pollMessages, 2000);
      // Initial poll
      pollMessages();
    };

    // Start with WebSocket attempt
    setupWebSocket();
  };

  const startNewConversation = async () => {
    if (!newTopic.trim() || selectedAgents.length === 0) {
      alert('Please enter a topic and select at least one agent');
      return;
    }

    try {
      const response = await axios.post(`${API}/conversation/start`, {
        topic: newTopic,
        agents: selectedAgents,
        message_count: 5
      });

      const conversationId = response.data.conversation_id;
      setCurrentConversation(conversationId);
      setMessages([]);
      setNewTopic('');
      setSelectedAgents([]);
      
      // Setup real-time updates (WebSocket with polling fallback)
      setupRealTimeUpdates(conversationId);
      
      // Load existing messages for this conversation
      await loadConversationMessages(conversationId);
      
    } catch (error) {
      console.error('Error starting conversation:', error);
    }
  };

  const loadConversationMessages = async (conversationId) => {
    try {
      const response = await axios.get(`${API}/conversation/${conversationId}/messages`);
      console.log('Loaded existing messages:', response.data);
      setMessages(response.data);
    } catch (error) {
      console.error('Error loading conversation messages:', error);
    }
  };

  const generateConversation = async () => {
    if (!currentConversation) return;

    setIsGenerating(true);
    try {
      console.log('Starting conversation generation for:', currentConversation);
      await axios.post(`${API}/conversation/${currentConversation}/generate`);
      console.log('Conversation generation completed');
      // Messages will be received via WebSocket
    } catch (error) {
      console.error('Error generating conversation:', error);
    } finally {
      setIsGenerating(false);
      // Refresh API stats after generation
      setTimeout(loadApiStats, 1000);
    }
  };

  const sendUserMessage = async () => {
    if (!userMessage.trim() || !currentConversation) return;

    try {
      await axios.post(`${API}/conversation/${currentConversation}/message`, {
        content: userMessage
      });
      
      // Add user message to local state immediately
      const userMsg = {
        id: Date.now().toString(),
        conversation_id: currentConversation,
        content: userMessage,
        is_user: true,
        timestamp: new Date().toISOString()
      };
      
      console.log('Adding user message to state:', userMsg);
      setMessages(prev => {
        const newMessages = [...prev, userMsg];
        console.log('Updated messages with user message:', newMessages);
        return newMessages;
      });
      setUserMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const generateImage = async () => {
    if (!imagePrompt.trim() || !currentConversation) return;

    try {
      setIsGenerating(true);
      await axios.post(`${API}/image/generate`, {
        prompt: imagePrompt,
        conversation_id: currentConversation
      });
      setImagePrompt('');
    } catch (error) {
      console.error('Error generating image:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <h1 className="text-3xl font-bold text-center text-blue-400">
          🤖 Multi-Agent Chat Platform
        </h1>
        <p className="text-center text-gray-400 mt-2">
          Watch AI agents brainstorm and collaborate in real-time
        </p>
        
        {/* Connection Status Indicator */}
        {currentConversation && (
          <div className="flex justify-center mt-2">
            <div className="flex items-center text-xs px-3 py-1 rounded-full bg-gray-700">
              {isPolling ? (
                <>
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-yellow-400">Polling Mode (Fallback)</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-400">Real-time Connection</span>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-1/3 bg-gray-800 p-4 border-r border-gray-700 overflow-y-auto">
          {/* New Conversation */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4">Start New Conversation</h2>
            
            <input
              type="text"
              placeholder="Enter conversation topic..."
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none mb-4"
            />

            <div className="mb-4">
              <h3 className="text-lg font-medium mb-2">Select Agents:</h3>
              {Object.entries(agents).map(([key, agent]) => (
                <label key={key} className="flex items-center mb-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedAgents.includes(key)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedAgents(prev => [...prev, key]);
                      } else {
                        setSelectedAgents(prev => prev.filter(a => a !== key));
                      }
                    }}
                    className="mr-3"
                  />
                  <div className="flex items-center">
                    <div 
                      className="w-4 h-4 rounded-full mr-2"
                      style={{ backgroundColor: agent.color }}
                    ></div>
                    <span className="font-medium">{agent.name}</span>
                    <span className="text-sm text-gray-400 ml-2">({agent.role})</span>
                  </div>
                </label>
              ))}
            </div>

            <button
              onClick={startNewConversation}
              className="w-full bg-blue-600 hover:bg-blue-700 p-3 rounded-lg font-semibold transition-colors"
            >
              Start Conversation
            </button>
          </div>

          {/* API Stats */}
          {apiStats && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">API Key Usage</h3>
              <div className="space-y-2">
                {apiStats.api_keys.map((key, index) => (
                  <div key={index} className="bg-gray-700 p-2 rounded">
                    <div className="flex justify-between text-sm">
                      <span className="truncate">{key.keyId}</span>
                      <span>{key.requestCount}/{key.rateLimit}</span>
                    </div>
                    <div className="w-full bg-gray-600 rounded-full h-2 mt-1">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${Math.min(key.utilizationPercent, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Controls */}
          {currentConversation && (
            <div className="space-y-4">
              <button
                onClick={generateConversation}
                disabled={isGenerating}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 p-3 rounded-lg font-semibold transition-colors"
              >
                {isGenerating ? 'Generating...' : '🚀 Generate Agent Discussion'}
              </button>

              <div>
                <input
                  type="text"
                  placeholder="Generate an image..."
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  className="w-full p-2 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none mb-2"
                />
                <button
                  onClick={generateImage}
                  disabled={isGenerating || !imagePrompt.trim()}
                  className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 p-2 rounded-lg font-semibold transition-colors"
                >
                  🎨 Generate Image
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {currentConversation ? (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className="flex items-start space-x-3">
                    {!message.is_user && (
                      <div 
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                        style={{ backgroundColor: message.agent_config?.color || AGENT_COLORS[message.agent_type] || '#6B7280' }}
                      >
                        {message.agent_config?.name?.[0] || message.agent_type?.[0]?.toUpperCase() || 'A'}
                      </div>
                    )}
                    
                    <div className={`flex-1 ${message.is_user ? 'text-right' : ''}`}>
                      <div className={`inline-block max-w-3xl p-3 rounded-lg ${
                        message.is_user 
                          ? 'bg-blue-600 text-white ml-auto' 
                          : 'bg-gray-700 text-white'
                      }`}>
                        {!message.is_user && (
                          <div className="font-semibold text-sm mb-1" style={{ color: message.agent_config?.color || AGENT_COLORS[message.agent_type] || '#6B7280' }}>
                            {message.agent_config?.name || message.agent_type || 'Agent'}
                          </div>
                        )}
                        
                        <div className="text-sm">{message.content}</div>
                        
                        {message.image_url && (
                          <img 
                            src={message.image_url} 
                            alt="Generated" 
                            className="mt-2 rounded-lg max-w-full h-auto"
                          />
                        )}
                        
                        <div className="text-xs text-gray-400 mt-1">
                          {formatTimestamp(message.timestamp)}
                        </div>
                      </div>
                    </div>
                    
                    {message.is_user && (
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                        U
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* User Input */}
              <div className="p-4 border-t border-gray-700">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Type your message..."
                    value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendUserMessage()}
                    className="flex-1 p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    onClick={sendUserMessage}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
                  >
                    Send
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">🤖</div>
                <h2 className="text-2xl font-semibold mb-2">Welcome to Multi-Agent Chat</h2>
                <p className="text-gray-400">Start a new conversation to see AI agents collaborate!</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;