import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
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

// Enhanced components for better UX
const TypingIndicator = ({ agentName, agentColor }) => (
  <div className="flex items-center space-x-2 p-3 bg-gray-700 rounded-lg">
    <div 
      className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm animate-pulse"
      style={{ backgroundColor: agentColor }}
    >
      {agentName?.[0] || 'A'}
    </div>
    <div className="flex space-x-1">
      <div className="text-gray-300">{agentName} is typing</div>
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  </div>
);

const StreamingMessage = ({ message, agentConfig, isStreaming }) => (
  <div className="flex items-start space-x-3">
    <div 
      className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${isStreaming ? 'animate-pulse' : ''}`}
      style={{ backgroundColor: agentConfig?.color || AGENT_COLORS[message.agent_type] || '#6B7280' }}
    >
      {agentConfig?.icon || agentConfig?.name?.[0] || message.agent_type?.[0]?.toUpperCase() || 'A'}
    </div>
    
    <div className="flex-1">
      <div className="inline-block max-w-3xl p-3 rounded-lg bg-gray-700 text-white">
        <div className="flex items-center justify-between mb-1">
          <div className="font-semibold text-sm flex items-center" style={{ color: agentConfig?.color || AGENT_COLORS[message.agent_type] || '#6B7280' }}>
            {agentConfig?.name || message.agent_type || 'Agent'}
            {isStreaming && (
              <div className="ml-2 flex space-x-1">
                <div className="w-1 h-1 bg-current rounded-full animate-ping"></div>
                <div className="w-1 h-1 bg-current rounded-full animate-ping" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-1 h-1 bg-current rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
              </div>
            )}
          </div>
          {message.response_time && (
            <div className="text-xs text-gray-400">
              {(message.response_time * 1000).toFixed(0)}ms
            </div>
          )}
        </div>
        
        <div className="text-sm">
          {message.content}
          {isStreaming && <span className="animate-pulse">▋</span>}
        </div>
        
        {message.image_url && (
          <img 
            src={message.image_url} 
            alt="Generated" 
            className="mt-2 rounded-lg max-w-full h-auto"
          />
        )}
        
        <div className="flex justify-between items-center mt-1 text-xs text-gray-400">
          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          {message.token_count && (
            <span>{message.token_count} tokens</span>
          )}
        </div>
      </div>
    </div>
  </div>
);

const PerformanceStats = ({ stats }) => {
  if (!stats) return null;
  
  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h3 className="text-lg font-semibold mb-3 text-blue-400">System Performance</h3>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-gray-400">Active Keys</div>
          <div className="text-white font-medium">{stats.summary?.active_keys || 0}/{stats.summary?.total_keys || 0}</div>
        </div>
        <div>
          <div className="text-gray-400">Avg Response</div>
          <div className="text-white font-medium">{(stats.summary?.avg_response_time * 1000 || 0).toFixed(0)}ms</div>
        </div>
        <div>
          <div className="text-gray-400">Total Requests</div>
          <div className="text-white font-medium">{stats.summary?.total_requests || 0}</div>
        </div>
        <div>
          <div className="text-gray-400">Error Rate</div>
          <div className={`font-medium ${(stats.summary?.total_errors || 0) > 0 ? 'text-red-400' : 'text-green-400'}`}>
            {((stats.summary?.total_errors || 0) / Math.max(stats.summary?.total_requests || 1, 1) * 100).toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
};

const ConversationControls = ({ 
  conversationId, 
  onExport, 
  onSummary, 
  isGenerating 
}) => (
  <div className="flex space-x-2 mb-4">
    <button
      onClick={() => onExport('json')}
      disabled={!conversationId || isGenerating}
      className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded transition-colors"
    >
      📄 Export JSON
    </button>
    <button
      onClick={() => onExport('markdown')}
      disabled={!conversationId || isGenerating}
      className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded transition-colors"
    >
      📝 Export MD
    </button>
    <button
      onClick={onSummary}
      disabled={!conversationId || isGenerating}
      className="px-3 py-1 text-xs bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded transition-colors"
    >
      🧠 Summary
    </button>
  </div>
);

const App = () => {
  // Core state
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
  
  // Enhanced state for new features
  const [collaborationMode, setCollaborationMode] = useState('autonomous');
  const [isCollaborating, setIsCollaborating] = useState(false);
  const [consensusStatus, setConsensusStatus] = useState(null);
  const [currentRound, setCurrentRound] = useState(0);
  const [maxRounds, setMaxRounds] = useState(8);
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  
  // Streaming and performance state
  const [streamingMessages, setStreamingMessages] = useState(new Map());
  const [typingAgents, setTypingAgents] = useState(new Set());
  const [systemHealth, setSystemHealth] = useState(null);
  const [conversationSummary, setConversationSummary] = useState(null);
  const [agentAnalytics, setAgentAnalytics] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Refs for optimization
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const pollingRef = useRef(null);
  const [isPolling, setIsPolling] = useState(false);
  const [lastMessageCount, setLastMessageCount] = useState(0);

  // Optimized scroll function
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Memoized agent list for performance
  const agentList = useMemo(() => Object.entries(agents), [agents]);

  // Load initial data
  useEffect(() => {
    Promise.all([
      loadAgents(),
      loadApiStats(),
      loadSystemHealth()
    ]);
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

  // Auto-scroll when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-refresh stats and health
  useEffect(() => {
    const interval = setInterval(() => {
      loadApiStats();
      loadSystemHealth();
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

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

  const loadSystemHealth = async () => {
    try {
      const response = await axios.get(`${API}/system/health`);
      setSystemHealth(response.data);
    } catch (error) {
      console.error('Error loading system health:', error);
    }
  };

  const loadAgentAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/agents`);
      setAgentAnalytics(response.data);
    } catch (error) {
      console.error('Error loading agent analytics:', error);
    }
  };

  // Enhanced real-time updates with better error handling
  const setupRealTimeUpdates = useCallback((conversationId) => {
    // Close existing connections
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    // Clear streaming state
    setStreamingMessages(new Map());
    setTypingAgents(new Set());

    const setupWebSocket = () => {
      let wsUrl;
      if (BACKEND_URL.includes('emergentagent.com')) {
        wsUrl = `wss://fast-stream-logic.preview.emergentagent.com/api/ws/${conversationId}`;
      } else {
        wsUrl = `${BACKEND_URL.replace('http', 'ws')}/api/ws/${conversationId}`;
      }
      
      console.log('🔌 Attempting enhanced WebSocket connection:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('✅ Enhanced WebSocket connected successfully');
        setConnectionStatus('connected');
        setIsPolling(false);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Enhanced WebSocket message:', data.type, data.data);
          
          switch (data.type) {
            case 'connection_established':
              console.log('✅ Enhanced connection confirmed:', data.data.message);
              break;
              
            case 'streaming_status':
              handleStreamingStatus(data.data);
              break;
              
            case 'streaming_chunk':
              handleStreamingChunk(data.data);
              break;
              
            case 'agent_message_start':
              handleAgentMessageStart(data.data);
              break;
              
            case 'agent_message_stream':
              handleAgentMessageStream(data.data);
              break;
              
            case 'agent_message_complete':
            case 'agent_message':
              handleAgentMessageComplete(data.data);
              break;
              
            case 'user_message':
              handleUserMessage(data.data);
              break;
              
            case 'consensus_update':
              setConsensusStatus(data.data.consensus);
              setCurrentRound(data.data.round);
              break;
              
            case 'consensus_final':
              setMessages(prev => [...prev, data.data]);
              setIsCollaborating(false);
              setConsensusStatus({ reached: true, final: true });
              break;
              
            case 'collaboration_concluded':
              setMessages(prev => [...prev, data.data]);
              setIsCollaborating(false);
              break;
              
            case 'round_start':
              setCurrentRound(data.data.round);
              break;
              
            case 'heartbeat':
              // Handle heartbeat for connection health
              break;
              
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('❌ Error parsing enhanced WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.warn('⚠️ Enhanced WebSocket error, falling back to polling:', error);
        setConnectionStatus('error');
        setupPolling(conversationId);
      };

      wsRef.current.onclose = (event) => {
        if (event.code === 1006 || event.code === 1011 || event.code === 1005) {
          console.warn('⚠️ Enhanced WebSocket connection failed, using polling fallback');
          setConnectionStatus('polling');
          setupPolling(conversationId);
        } else {
          console.log('🔌 Enhanced WebSocket connection closed:', event.code, event.reason);
          setConnectionStatus('disconnected');
        }
      };
    };

    // Enhanced polling fallback
    const setupPolling = (conversationId) => {
      console.log('🔄 Setting up enhanced polling fallback');
      setIsPolling(true);
      setConnectionStatus('polling');
      
      const pollMessages = async () => {
        try {
          const response = await axios.get(`${API}/conversation/${conversationId}/poll`);
          const { messages, conversation_status } = response.data;
          
          if (messages.length !== lastMessageCount) {
            console.log(`🔄 Enhanced polling: ${messages.length} messages (was ${lastMessageCount})`);
            setMessages(messages);
            setLastMessageCount(messages.length);
          }
          
          // Update collaboration status from polling
          if (conversation_status === 'completed') {
            setIsCollaborating(false);
          }
        } catch (error) {
          console.error('❌ Enhanced polling error:', error);
          setConnectionStatus('error');
        }
      };

      pollingRef.current = setInterval(pollMessages, 1500); // Faster polling
      pollMessages(); // Initial poll
    };

    // Start with WebSocket attempt
    setupWebSocket();
  }, [lastMessageCount]);

  // Enhanced streaming handlers
  const handleStreamingStatus = (data) => {
    console.log('📊 Streaming status:', data.status);
    
    if (data.status === 'started') {
      setTypingAgents(prev => new Set([...prev, data.agent_type]));
    } else if (data.status === 'completed' || data.status === 'error') {
      setTypingAgents(prev => {
        const newSet = new Set(prev);
        newSet.delete(data.agent_type);
        return newSet;
      });
    }
  };

  const handleStreamingChunk = (data) => {
    // Handle individual chunks for ultra-smooth streaming
    console.log('📝 Streaming chunk:', data.chunk_number);
  };

  const handleAgentMessageStart = (data) => {
    const agentName = data.agent_config?.name || agents[data.agent_type]?.name || data.agent_type;
    setTypingAgents(prev => new Set([...prev, agentName]));
    
    // Initialize streaming message
    setStreamingMessages(prev => new Map(prev.set(data.id, {
      ...data,
      isStreaming: true
    })));
  };

  const handleAgentMessageStream = (data) => {
    setStreamingMessages(prev => new Map(prev.set(data.id, {
      ...data,
      isStreaming: true
    })));
  };

  const handleAgentMessageComplete = (data) => {
    const agentName = data.agent_config?.name || agents[data.agent_type]?.name || data.agent_type;
    
    setTypingAgents(prev => {
      const newSet = new Set(prev);
      newSet.delete(agentName);
      return newSet;
    });
    
    setStreamingMessages(prev => {
      const newMap = new Map(prev);
      newMap.delete(data.id);
      return newMap;
    });
    
    setMessages(prev => {
      const existingIndex = prev.findIndex(msg => msg.id === data.id);
      if (existingIndex >= 0) {
        const newMessages = [...prev];
        newMessages[existingIndex] = { ...data, isStreaming: false };
        return newMessages;
      } else {
        return [...prev, { ...data, isStreaming: false }];
      }
    });
    
    setLastMessageCount(prev => prev + 1);
  };

  const handleUserMessage = (data) => {
    setMessages(prev => {
      const exists = prev.find(msg => msg.id === data.id);
      if (!exists) {
        return [...prev, data];
      }
      return prev;
    });
    setLastMessageCount(prev => prev + 1);
  };

  const startNewConversation = async () => {
    if (!newTopic.trim() || selectedAgents.length === 0) {
      alert('Please enter a topic and select at least one agent');
      return;
    }

    try {
      let response;
      
      if (collaborationMode === 'autonomous') {
        response = await axios.post(`${API}/conversation/autonomous`, {
          topic: newTopic,
          agents: selectedAgents,
          collaboration_mode: 'autonomous',
          max_rounds: maxRounds,
          consensus_threshold: 0.7,
          streaming_enabled: streamingEnabled
        });
        
        setIsCollaborating(true);
        setConsensusStatus(null);
        setCurrentRound(0);
      } else {
        response = await axios.post(`${API}/conversation/start`, {
          topic: newTopic,
          agents: selectedAgents,
          message_count: 3
        });
      }

      const conversationId = response.data.conversation_id;
      setCurrentConversation(conversationId);
      setMessages([]);
      setNewTopic('');
      setSelectedAgents([]);
      setConversationSummary(null);
      
      // Setup enhanced real-time updates
      setupRealTimeUpdates(conversationId);
      
      // Load existing messages
      await loadConversationMessages(conversationId);
      
    } catch (error) {
      console.error('Error starting enhanced conversation:', error);
      alert('Failed to start conversation');
    }
  };

  const loadConversationMessages = async (conversationId) => {
    try {
      const response = await axios.get(`${API}/conversation/${conversationId}/messages`);
      console.log('Loaded existing enhanced messages:', response.data);
      setMessages(response.data);
      setLastMessageCount(response.data.length);
    } catch (error) {
      console.error('Error loading conversation messages:', error);
    }
  };

  const generateConversation = async () => {
    if (!currentConversation) return;

    setIsGenerating(true);
    try {
      console.log('Starting enhanced conversation generation for:', currentConversation);
      await axios.post(`${API}/conversation/${currentConversation}/generate`);
      console.log('Enhanced conversation generation completed');
    } catch (error) {
      console.error('Error generating enhanced conversation:', error);
    } finally {
      setIsGenerating(false);
      setTimeout(() => {
        loadApiStats();
        loadSystemHealth();
      }, 1000);
    }
  };

  const sendUserMessage = async () => {
    if (!userMessage.trim() || !currentConversation) return;

    try {
      await axios.post(`${API}/conversation/${currentConversation}/message`, {
        content: userMessage
      });
      
      setUserMessage('');
    } catch (error) {
      console.error('Error sending enhanced message:', error);
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
      console.error('Error generating enhanced image:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  // New enhanced features
  const exportConversation = async (format) => {
    if (!currentConversation) return;

    try {
      const response = await axios.post(`${API}/conversation/${currentConversation}/export`, {
        conversation_id: currentConversation,
        format: format
      });

      if (format === 'json') {
        const blob = new Blob([JSON.stringify(response.data.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${currentConversation}.json`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'markdown') {
        const blob = new Blob([response.data.content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${currentConversation}.md`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting conversation:', error);
    }
  };

  const generateSummary = async () => {
    if (!currentConversation) return;

    try {
      const response = await axios.get(`${API}/conversation/${currentConversation}/summary`);
      setConversationSummary(response.data);
    } catch (error) {
      console.error('Error generating summary:', error);
    }
  };

  // Render combined messages with streaming
  const renderMessages = () => {
    const allMessages = [...messages];
    
    // Add streaming messages
    streamingMessages.forEach((streamingMsg, id) => {
      const existingIndex = allMessages.findIndex(msg => msg.id === id);
      if (existingIndex >= 0) {
        allMessages[existingIndex] = { ...streamingMsg, isStreaming: true };
      } else {
        allMessages.push({ ...streamingMsg, isStreaming: true });
      }
    });
    
    // Sort by timestamp
    allMessages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    return allMessages.map((message) => {
      const isStreaming = streamingMessages.has(message.id);
      
      if (message.is_user) {
        return (
          <div key={message.id} className="flex items-start space-x-3 justify-end">
            <div className="flex-1 text-right">
              <div className="inline-block max-w-3xl p-3 rounded-lg bg-blue-600 text-white">
                <div className="text-sm">{message.content}</div>
                <div className="text-xs text-blue-200 mt-1">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
              U
            </div>
          </div>
        );
      }

      const agentConfig = message.agent_config || agents[message.agent_type] || {};
      return (
        <StreamingMessage
          key={message.id}
          message={message}
          agentConfig={agentConfig}
          isStreaming={isStreaming}
        />
      );
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Enhanced Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <h1 className="text-3xl font-bold text-center text-blue-400">
          🤖 Enhanced Multi-Agent Chat Platform v2.0
        </h1>
        <p className="text-center text-gray-400 mt-2">
          Real-time streaming collaboration with AI agents
        </p>
        
        {/* Enhanced Connection Status */}
        {currentConversation && (
          <div className="flex justify-center mt-2 space-x-4">
            <div className="flex items-center text-xs px-3 py-1 rounded-full bg-gray-700">
              {connectionStatus === 'connected' ? (
                <>
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-400">WebSocket Connected</span>
                </>
              ) : connectionStatus === 'polling' ? (
                <>
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-yellow-400">Polling Mode</span>
                </>
              ) : connectionStatus === 'error' ? (
                <>
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                  <span className="text-red-400">Connection Error</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-gray-500 rounded-full mr-2"></div>
                  <span className="text-gray-400">Disconnected</span>
                </>
              )}
            </div>
            
            {streamingEnabled && (
              <div className="flex items-center text-xs px-3 py-1 rounded-full bg-purple-800">
                <div className="w-2 h-2 bg-purple-400 rounded-full mr-2"></div>
                <span className="text-purple-200">Streaming Enabled</span>
              </div>
            )}
            
            {systemHealth?.status && (
              <div className={`flex items-center text-xs px-3 py-1 rounded-full ${
                systemHealth.status === 'healthy' ? 'bg-green-800' : 'bg-red-800'
              }`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  systemHealth.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <span className={systemHealth.status === 'healthy' ? 'text-green-200' : 'text-red-200'}>
                  System {systemHealth.status}
                </span>
              </div>
            )}
          </div>
        )}
        
        {/* Enhanced Autonomous Collaboration Status */}
        {isCollaborating && currentConversation && (
          <div className="flex justify-center mt-2">
            <div className="flex items-center text-xs px-4 py-2 rounded-lg bg-purple-800 border border-purple-600">
              <div className="w-3 h-3 bg-purple-400 rounded-full mr-2 animate-ping"></div>
              <div>
                <span className="text-purple-200 font-medium">🤖 Enhanced Autonomous Collaboration</span>
                <div className="text-purple-300 mt-1">
                  Round {currentRound}/{maxRounds} • 
                  {consensusStatus?.reached ? (
                    <span className="text-green-400 ml-1">Consensus: {(consensusStatus.confidence * 100).toFixed(0)}%</span>
                  ) : (
                    <span className="text-yellow-400 ml-1">Seeking consensus...</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex h-screen">
        {/* Enhanced Sidebar */}
        <div className="w-1/3 bg-gray-800 p-4 border-r border-gray-700 overflow-y-auto">
          {/* New Conversation */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4">Start Enhanced Conversation</h2>
            
            <input
              type="text"
              placeholder="Enter conversation topic..."
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none mb-4"
            />

            <div className="mb-4">
              <h3 className="text-lg font-medium mb-2">Select Agents:</h3>
              {agentList.map(([key, agent]) => (
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
                      className="w-4 h-4 rounded-full mr-2 flex items-center justify-center text-xs"
                      style={{ backgroundColor: agent.color }}
                    >
                      {agent.icon}
                    </div>
                    <span className="font-medium">{agent.name}</span>
                    <span className="text-sm text-gray-400 ml-2">({agent.specialty})</span>
                  </div>
                </label>
              ))}
            </div>

            {/* Enhanced Collaboration Mode */}
            <div className="mb-4">
              <h3 className="text-lg font-medium mb-2">Mode & Settings:</h3>
              <div className="space-y-2">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="collaborationMode"
                    value="single_turn"
                    checked={collaborationMode === 'single_turn'}
                    onChange={(e) => setCollaborationMode(e.target.value)}
                    className="mr-3"
                  />
                  <div>
                    <span className="font-medium">Single Turn</span>
                    <p className="text-sm text-gray-400">Each agent responds once</p>
                  </div>
                </label>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="collaborationMode"
                    value="autonomous"
                    checked={collaborationMode === 'autonomous'}
                    onChange={(e) => setCollaborationMode(e.target.value)}
                    className="mr-3"
                  />
                  <div>
                    <span className="font-medium text-purple-400">🤖 Enhanced Autonomous</span>
                    <p className="text-sm text-gray-400">AI agents collaborate until consensus</p>
                  </div>
                </label>
              </div>
              
              {collaborationMode === 'autonomous' && (
                <div className="mt-3 p-3 bg-gray-700 rounded-lg space-y-3">
                  <label className="flex items-center justify-between">
                    <span className="text-sm">Max Rounds:</span>
                    <input
                      type="range"
                      min="3"
                      max="15"
                      value={maxRounds}
                      onChange={(e) => setMaxRounds(parseInt(e.target.value))}
                      className="ml-3 w-20"
                    />
                    <span className="text-sm ml-2">{maxRounds}</span>
                  </label>
                  <label className="flex items-center justify-between">
                    <span className="text-sm">Streaming:</span>
                    <input
                      type="checkbox"
                      checked={streamingEnabled}
                      onChange={(e) => setStreamingEnabled(e.target.checked)}
                      className="ml-3"
                    />
                  </label>
                </div>
              )}
            </div>

            {/* Enhanced Start Button */}
            <button
              onClick={startNewConversation}
              disabled={isCollaborating}
              className={`w-full p-3 rounded-lg font-semibold transition-all ${
                isCollaborating 
                  ? 'bg-gray-600 cursor-not-allowed' 
                  : collaborationMode === 'autonomous'
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
                    : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isCollaborating ? (
                '🤖 Agents Collaborating...'
              ) : collaborationMode === 'autonomous' ? (
                '🚀 Start Enhanced Collaboration'
              ) : (
                'Start Conversation'
              )}
            </button>
          </div>

          {/* Enhanced Performance Stats */}
          <PerformanceStats stats={apiStats} />

          {/* API Usage Details */}
          {apiStats && (
            <div className="mb-6 mt-4">
              <h3 className="text-lg font-semibold mb-3">API Key Performance</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {apiStats.api_keys.map((key, index) => (
                  <div key={index} className="bg-gray-700 p-2 rounded">
                    <div className="flex justify-between text-sm">
                      <span className="truncate">{key.keyId}</span>
                      <span className="flex items-center space-x-2">
                        <span>{key.requestCount}/{key.rateLimit}</span>
                        {key.avgResponseTime > 0 && (
                          <span className="text-gray-400">
                            {(key.avgResponseTime * 1000).toFixed(0)}ms
                          </span>
                        )}
                      </span>
                    </div>
                    <div className="w-full bg-gray-600 rounded-full h-2 mt-1">
                      <div 
                        className={`h-2 rounded-full ${
                          key.errorRate > 5 ? 'bg-red-600' : 
                          key.utilizationPercent > 80 ? 'bg-yellow-600' : 'bg-blue-600'
                        }`}
                        style={{ width: `${Math.min(key.utilizationPercent, 100)}%` }}
                      ></div>
                    </div>
                    {key.errorRate > 0 && (
                      <div className="text-xs text-red-400 mt-1">
                        Error rate: {key.errorRate.toFixed(1)}%
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Enhanced Controls */}
          {currentConversation && (
            <div className="space-y-4">
              <ConversationControls
                conversationId={currentConversation}
                onExport={exportConversation}
                onSummary={generateSummary}
                isGenerating={isGenerating}
              />
              
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

        {/* Enhanced Chat Area */}
        <div className="flex-1 flex flex-col">
          {currentConversation ? (
            <>
              {/* Enhanced Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {renderMessages()}
                
                {/* Typing Indicators */}
                {Array.from(typingAgents).map((agentName) => {
                  const agentKey = Object.keys(agents).find(key => agents[key].name === agentName);
                  const agentConfig = agentKey ? agents[agentKey] : {};
                  return (
                    <TypingIndicator 
                      key={agentName}
                      agentName={agentName} 
                      agentColor={agentConfig.color || '#6B7280'}
                    />
                  );
                })}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Enhanced User Input */}
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
                    disabled={!userMessage.trim()}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-semibold transition-colors"
                  >
                    Send
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">🤖✨</div>
                <h2 className="text-3xl font-semibold mb-2">Enhanced Multi-Agent Platform</h2>
                <p className="text-gray-400 mb-4">Experience real-time streaming AI collaboration</p>
                <div className="text-sm text-gray-500 space-y-1">
                  <div>🔄 Real-time streaming responses</div>
                  <div>📊 Performance analytics</div>
                  <div>💾 Export conversations</div>
                  <div>🧠 AI-powered summaries</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Summary Modal */}
      {conversationSummary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-blue-400">🧠 Conversation Summary</h3>
              <button
                onClick={() => setConversationSummary(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-green-400 mb-2">Summary:</h4>
                <p className="text-gray-300">{conversationSummary.summary}</p>
              </div>
              
              <div>
                <h4 className="font-medium text-yellow-400 mb-2">Key Insights:</h4>
                <ul className="list-disc list-inside text-gray-300 space-y-1">
                  {conversationSummary.key_insights?.map((insight, index) => (
                    <li key={index}>{insight}</li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-purple-400 mb-2">Agent Contributions:</h4>
                <div className="grid gap-2">
                  {Object.entries(conversationSummary.agent_contributions || {}).map(([agent, contribution]) => (
                    <div key={agent} className="text-sm">
                      <span className="font-medium" style={{ color: AGENT_COLORS[agent] || '#6B7280' }}>
                        {agent}:
                      </span>
                      <span className="text-gray-400 ml-2">{contribution}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;