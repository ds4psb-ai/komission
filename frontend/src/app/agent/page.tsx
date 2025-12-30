"use client";

import React, { useState, useRef, useEffect } from 'react';
import {
    Send, Sparkles, MessageSquare, Lightbulb,
    Camera, TrendingUp, BookOpen, Loader2
} from 'lucide-react';
import { AppHeader } from '@/components/AppHeader';
import { api } from '@/lib/api';

// ====================
// TYPES
// ====================

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface Suggestion {
    id: string;
    text: string;
    category: string;
}

// ====================
// SUGGESTION CHIPS
// ====================

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
    '분석': <TrendingUp className="w-3.5 h-3.5" />,
    '창작': <Lightbulb className="w-3.5 h-3.5" />,
    '코칭': <Camera className="w-3.5 h-3.5" />,
    '학습': <BookOpen className="w-3.5 h-3.5" />,
    '비즈니스': <Sparkles className="w-3.5 h-3.5" />,
};

const DEFAULT_SUGGESTIONS: Suggestion[] = [
    { id: 'analyze_trend', text: '지난주 뷰티 트렌드 분석해줘', category: '분석' },
    { id: 'hook_ideas', text: '3초 훅 아이디어 3개 만들어줘', category: '창작' },
    { id: 'coaching_tips', text: '촬영할 때 주의할 점 알려줘', category: '코칭' },
    { id: 'pattern_explain', text: '핵심 규칙 3가지가 뭐야?', category: '학습' },
];

// ====================
// COMPONENTS
// ====================

function SuggestionChip({
    suggestion,
    onClick
}: {
    suggestion: Suggestion;
    onClick: () => void;
}) {
    return (
        <button
            onClick={onClick}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl 
                       bg-white/5 border border-white/10 
                       hover:bg-white/10 hover:border-purple-500/50
                       transition-all duration-200 text-sm text-white/80
                       hover:text-white group"
        >
            <span className="text-purple-400 group-hover:text-purple-300">
                {CATEGORY_ICONS[suggestion.category] || <MessageSquare className="w-3.5 h-3.5" />}
            </span>
            <span>{suggestion.text}</span>
        </button>
    );
}

function ChatBubble({ message }: { message: ChatMessage }) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${isUser
                ? 'bg-purple-600 text-white rounded-br-md'
                : 'bg-white/10 text-white/90 rounded-bl-md'
                }`}>
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                </div>
                <div className={`text-[10px] mt-1 ${isUser ? 'text-white/60' : 'text-white/40'}`}>
                    {message.timestamp.toLocaleTimeString('ko-KR', {
                        hour: '2-digit',
                        minute: '2-digit'
                    })}
                </div>
            </div>
        </div>
    );
}

// ====================
// MAIN PAGE
// ====================

const STORAGE_KEY = 'komission_agent_chat';
const MAX_RETRY_ATTEMPTS = 2;

function generateSessionId(): string {
    return `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export default function AgentPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [suggestions, setSuggestions] = useState<Suggestion[]>(DEFAULT_SUGGESTIONS);
    const [sessionId, setSessionId] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Initialize session and load persisted messages
    useEffect(() => {
        // Generate or restore session ID
        const storedSession = localStorage.getItem(`${STORAGE_KEY}_session`);
        if (storedSession) {
            setSessionId(storedSession);
        } else {
            const newSession = generateSessionId();
            setSessionId(newSession);
            localStorage.setItem(`${STORAGE_KEY}_session`, newSession);
        }

        // Load persisted messages
        const storedMessages = localStorage.getItem(`${STORAGE_KEY}_messages`);
        if (storedMessages) {
            try {
                const parsed = JSON.parse(storedMessages);
                const restored = parsed.map((m: ChatMessage) => ({
                    ...m,
                    timestamp: new Date(m.timestamp)
                }));
                setMessages(restored);
            } catch (e) {
                console.log('Could not restore messages');
            }
        }
    }, []);

    // Persist messages to localStorage
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem(`${STORAGE_KEY}_messages`, JSON.stringify(messages));
        }
    }, [messages]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Load suggestions on mount
    useEffect(() => {
        loadSuggestions();
    }, []);

    const clearChat = () => {
        setMessages([]);
        localStorage.removeItem(`${STORAGE_KEY}_messages`);
        const newSession = generateSessionId();
        setSessionId(newSession);
        localStorage.setItem(`${STORAGE_KEY}_session`, newSession);
    };

    const loadSuggestions = async () => {
        try {
            const token = api.getToken();
            const response = await fetch('/api/v1/agent/suggestions', {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (response.ok) {
                const data = await response.json();
                if (data.suggestions?.length) {
                    setSuggestions(data.suggestions);
                }
            }
        } catch (error) {
            console.log('Using default suggestions');
        }
    };

    const sendMessage = async (text: string, retryCount = 0) => {
        if (!text.trim() || isLoading) return;

        setError(null);

        // Only add user message on first attempt
        if (retryCount === 0) {
            const userMessage: ChatMessage = {
                role: 'user',
                content: text.trim(),
                timestamp: new Date()
            };
            setMessages(prev => [...prev, userMessage]);
            setInput('');
        }

        setIsLoading(true);

        try {
            const token = api.getToken();
            const response = await fetch('/api/v1/agent/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId,
                    history: messages.map(m => ({
                        role: m.role,
                        content: m.content
                    }))
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();

            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: data.message,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);

            // Update dynamic suggestions from backend
            if (data.suggestions?.length) {
                setSuggestions(prev => [
                    ...data.suggestions.map((text: string, i: number) => ({
                        id: `dynamic_${i}`,
                        text,
                        category: '추천'
                    })),
                    ...prev.slice(0, 2)
                ].slice(0, 4));
            }
        } catch (err) {
            console.error('Chat error:', err);

            // Retry logic
            if (retryCount < MAX_RETRY_ATTEMPTS) {
                console.log(`Retrying... (${retryCount + 1}/${MAX_RETRY_ATTEMPTS})`);
                setTimeout(() => sendMessage(text, retryCount + 1), 1000);
                return;
            }

            setError('응답을 받지 못했어요. 잠시 후 다시 시도해주세요.');
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '죄송해요, 지금 응답하기 어려운 상황이에요. 잠시 후 다시 시도해주세요! 🙏',
                timestamp: new Date()
            }]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        sendMessage(input);
    };

    const handleSuggestionClick = (suggestion: Suggestion) => {
        sendMessage(suggestion.text);
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950">
            <AppHeader />

            <main className="max-w-3xl mx-auto px-4 pt-20 pb-32">
                {/* Header */}
                <div className="text-center mb-8 pt-8">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full 
                                    bg-purple-500/10 border border-purple-500/20 mb-4">
                        <Sparkles className="w-4 h-4 text-purple-400" />
                        <span className="text-sm text-purple-300">콘텐츠 전략 에이전트</span>
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        무엇을 도와드릴까요?
                    </h1>
                    <p className="text-white/50">
                        바이럴 콘텐츠 분석, 촬영 코칭, 트렌드 인사이트까지
                    </p>
                </div>

                {/* Empty State / Suggestions */}
                {messages.length === 0 && (
                    <div className="space-y-4 mb-8">
                        <p className="text-white/40 text-sm text-center">추천 질문</p>
                        <div className="flex flex-wrap justify-center gap-2">
                            {suggestions.map(suggestion => (
                                <SuggestionChip
                                    key={suggestion.id}
                                    suggestion={suggestion}
                                    onClick={() => handleSuggestionClick(suggestion)}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Messages */}
                <div className="space-y-2 mb-4">
                    {messages.map((message, index) => (
                        <ChatBubble key={index} message={message} />
                    ))}

                    {/* Loading indicator */}
                    {isLoading && (
                        <div className="flex justify-start mb-4">
                            <div className="bg-white/10 rounded-2xl rounded-bl-md px-4 py-3">
                                <div className="flex items-center gap-2 text-white/50">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span className="text-sm">생각 중...</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Follow-up suggestions */}
                {messages.length > 0 && !isLoading && (
                    <div className="flex flex-wrap gap-2 mb-4">
                        {suggestions.slice(0, 3).map(suggestion => (
                            <button
                                key={suggestion.id}
                                onClick={() => handleSuggestionClick(suggestion)}
                                className="text-xs px-3 py-1.5 rounded-full 
                                         bg-white/5 border border-white/10 
                                         text-white/60 hover:text-white
                                         hover:bg-white/10 transition-all"
                            >
                                {suggestion.text}
                            </button>
                        ))}
                    </div>
                )}
            </main>

            {/* Fixed Input Bar */}
            <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-zinc-950 via-zinc-950/95 to-transparent pt-8 pb-6">
                <form
                    onSubmit={handleSubmit}
                    className="max-w-3xl mx-auto px-4"
                >
                    <div className="relative">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="무엇이든 물어보세요..."
                            disabled={isLoading}
                            className="w-full px-5 py-4 pr-14 rounded-2xl
                                     bg-white/5 border border-white/10
                                     text-white placeholder-white/30
                                     focus:outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20
                                     disabled:opacity-50 transition-all"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className="absolute right-2 top-1/2 -translate-y-1/2
                                     p-2.5 rounded-xl bg-purple-600 text-white
                                     hover:bg-purple-500 disabled:opacity-30 disabled:cursor-not-allowed
                                     transition-all"
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </button>
                    </div>
                    <p className="text-center text-white/30 text-xs mt-3">
                        에이전트는 실수할 수 있어요. 중요한 정보는 직접 확인해주세요.
                    </p>
                </form>
            </div>
        </div>
    );
}
