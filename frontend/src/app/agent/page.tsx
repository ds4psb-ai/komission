"use client";

import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
    Send, Sparkles, MessageSquare, Lightbulb,
    Camera, TrendingUp, BookOpen, Loader2,
    Bot, User, Trash2, RefreshCcw, Zap, ChevronRight
} from 'lucide-react';
import { AppHeader } from '@/components/AppHeader';
import { api } from '@/lib/api';

// ====================
// TYPES
// ====================

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    actions?: ActionButton[];
}

interface ActionButton {
    id: string;
    label: string;
    icon?: string;
    action_type: string;
}

interface Suggestion {
    id: string;
    text: string;
    category: string;
}

// ====================
// CONSTANTS
// ====================

const STORAGE_KEY = 'komission_agent_chat';
const MAX_RETRY_ATTEMPTS = 2;

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
    '분석': <TrendingUp className="w-3.5 h-3.5" />,
    '창작': <Lightbulb className="w-3.5 h-3.5" />,
    '코칭': <Camera className="w-3.5 h-3.5" />,
    '학습': <BookOpen className="w-3.5 h-3.5" />,
    '추천': <Zap className="w-3.5 h-3.5" />,
    '비즈니스': <Sparkles className="w-3.5 h-3.5" />,
};

const DEFAULT_SUGGESTIONS: Suggestion[] = [
    { id: 'analyze_trend', text: '지난주 뷰티 트렌드 분석해줘', category: '분석' },
    { id: 'hook_ideas', text: '3초 훅 아이디어 3개 만들어줘', category: '창작' },
    { id: 'coaching_tips', text: '촬영할 때 주의할 점 알려줘', category: '코칭' },
    { id: 'pattern_explain', text: '핵심 규칙 3가지가 뭐야?', category: '학습' },
];

// ====================
// UTILITIES
// ====================

function generateMessageId(): string {
    return `msg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
}

function generateSessionId(): string {
    return `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

// Simple markdown-like formatting
function formatMessage(content: string): React.ReactNode {
    const lines = content.split('\n');
    return lines.map((line, i) => {
        // Bold: **text**
        let formatted: React.ReactNode = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Code: `text`
        formatted = String(formatted).replace(/`(.+?)`/g, '<code class="px-1.5 py-0.5 bg-white/10 rounded text-purple-300 text-xs">$1</code>');
        // Lists: - item or • item
        if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
            return (
                <div key={i} className="flex items-start gap-2 ml-2">
                    <span className="text-purple-400 mt-0.5">•</span>
                    <span dangerouslySetInnerHTML={{ __html: String(formatted).slice(2) }} />
                </div>
            );
        }
        // Numbered lists
        const numMatch = line.match(/^(\d+)\.\s/);
        if (numMatch) {
            return (
                <div key={i} className="flex items-start gap-2 ml-2">
                    <span className="text-purple-400 font-medium min-w-[1.2rem]">{numMatch[1]}.</span>
                    <span dangerouslySetInnerHTML={{ __html: String(formatted).slice(numMatch[0].length) }} />
                </div>
            );
        }
        // Headers: ## text
        if (line.startsWith('## ')) {
            return <div key={i} className="font-semibold text-white mt-3 mb-1">{line.slice(3)}</div>;
        }
        if (line.startsWith('### ')) {
            return <div key={i} className="font-medium text-purple-300 mt-2 mb-1">{line.slice(4)}</div>;
        }
        // Empty lines
        if (!line.trim()) {
            return <div key={i} className="h-2" />;
        }
        return <div key={i} dangerouslySetInnerHTML={{ __html: String(formatted) }} />;
    });
}

// ====================
// COMPONENTS
// ====================

function TypingIndicator() {
    return (
        <div className="flex justify-start mb-4 animate-fade-in">
            <div className="flex items-start gap-3 max-w-[85%]">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 
                               flex items-center justify-center flex-shrink-0 shadow-lg shadow-purple-500/20">
                    <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl rounded-tl-md px-4 py-3">
                    <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                </div>
            </div>
        </div>
    );
}

function SuggestionChip({
    suggestion,
    onClick,
    compact = false
}: {
    suggestion: Suggestion;
    onClick: () => void;
    compact?: boolean;
}) {
    return (
        <button
            onClick={onClick}
            className={`group flex items-center gap-2 rounded-xl 
                       bg-white/5 backdrop-blur-sm border border-white/10 
                       hover:bg-purple-500/10 hover:border-purple-500/40
                       transition-all duration-300 ease-out
                       hover:shadow-lg hover:shadow-purple-500/10
                       ${compact ? 'px-3 py-1.5 text-xs' : 'px-4 py-2.5 text-sm'}
                       text-white/70 hover:text-white`}
        >
            <span className="text-purple-400 group-hover:text-purple-300 transition-colors">
                {CATEGORY_ICONS[suggestion.category] || <MessageSquare className="w-3.5 h-3.5" />}
            </span>
            <span>{suggestion.text}</span>
            <ChevronRight className="w-3 h-3 text-white/30 group-hover:text-purple-400 
                                    group-hover:translate-x-0.5 transition-all" />
        </button>
    );
}

function ChatBubble({
    message,
    onActionClick
}: {
    message: ChatMessage;
    onActionClick?: (action: ActionButton) => void;
}) {
    const isUser = message.role === 'user';
    const formattedContent = useMemo(() =>
        isUser ? message.content : formatMessage(message.content),
        [message.content, isUser]
    );

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}>
            <div className={`flex items-start gap-3 max-w-[85%] ${isUser ? 'flex-row-reverse' : ''}`}>
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                               ${isUser
                        ? 'bg-gradient-to-br from-white/20 to-white/5 border border-white/20'
                        : 'bg-gradient-to-br from-purple-500 to-fuchsia-500 shadow-lg shadow-purple-500/20'
                    }`}>
                    {isUser
                        ? <User className="w-4 h-4 text-white/80" />
                        : <Bot className="w-4 h-4 text-white" />
                    }
                </div>

                {/* Message */}
                <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                    <div className={`rounded-2xl px-4 py-3 ${isUser
                        ? 'bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-tr-md shadow-lg shadow-purple-500/20'
                        : 'bg-white/5 backdrop-blur-xl border border-white/10 text-white/90 rounded-tl-md'
                        }`}>
                        <div className="text-sm leading-relaxed space-y-1">
                            {formattedContent}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    {message.actions && message.actions.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {message.actions.map(action => (
                                <button
                                    key={action.id}
                                    onClick={() => onActionClick?.(action)}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                                             bg-purple-500/20 border border-purple-500/30
                                             text-purple-300 text-xs font-medium
                                             hover:bg-purple-500/30 hover:text-purple-200
                                             transition-all duration-200"
                                >
                                    <Zap className="w-3 h-3" />
                                    {action.label}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Timestamp */}
                    <div className={`text-[10px] mt-1.5 ${isUser ? 'text-white/40' : 'text-white/30'}`}>
                        {message.timestamp.toLocaleTimeString('ko-KR', {
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ====================
// MAIN PAGE
// ====================

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
        const storedSession = localStorage.getItem(`${STORAGE_KEY}_session`);
        if (storedSession) {
            setSessionId(storedSession);
        } else {
            const newSession = generateSessionId();
            setSessionId(newSession);
            localStorage.setItem(`${STORAGE_KEY}_session`, newSession);
        }

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

    // Persist messages
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem(`${STORAGE_KEY}_messages`, JSON.stringify(messages));
        }
    }, [messages]);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    // Load suggestions
    useEffect(() => {
        loadSuggestions();
    }, []);

    const clearChat = () => {
        setMessages([]);
        localStorage.removeItem(`${STORAGE_KEY}_messages`);
        const newSession = generateSessionId();
        setSessionId(newSession);
        localStorage.setItem(`${STORAGE_KEY}_session`, newSession);
        setError(null);
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
        } catch {
            console.log('Using default suggestions');
        }
    };

    const sendMessage = async (text: string, retryCount = 0) => {
        if (!text.trim() || isLoading) return;

        setError(null);

        if (retryCount === 0) {
            const userMessage: ChatMessage = {
                id: generateMessageId(),
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
                id: generateMessageId(),
                role: 'assistant',
                content: data.message,
                timestamp: new Date(),
                actions: data.actions || []
            };

            setMessages(prev => [...prev, assistantMessage]);

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

            if (retryCount < MAX_RETRY_ATTEMPTS) {
                setTimeout(() => sendMessage(text, retryCount + 1), 1000);
                return;
            }

            setError('응답을 받지 못했어요. 잠시 후 다시 시도해주세요.');
            setMessages(prev => [...prev, {
                id: generateMessageId(),
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

    const handleActionClick = (action: ActionButton) => {
        console.log('Action clicked:', action);
        // TODO: Implement action execution
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950">
            <AppHeader />

            {/* Background decoration */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 -left-32 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-fuchsia-500/10 rounded-full blur-3xl" />
            </div>

            <main className="relative max-w-3xl mx-auto px-4 pt-20 pb-36">
                {/* Header */}
                <div className="text-center mb-8 pt-8">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full 
                                    bg-gradient-to-r from-purple-500/10 to-fuchsia-500/10 
                                    border border-purple-500/20 mb-4
                                    shadow-lg shadow-purple-500/5">
                        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        <span className="text-sm text-purple-300 font-medium">콘텐츠 전략 에이전트</span>
                    </div>
                    <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
                        무엇을 도와드릴까요?
                    </h1>
                    <p className="text-white/50 max-w-md mx-auto">
                        바이럴 콘텐츠 분석, 촬영 코칭, 트렌드 인사이트까지 자유롭게 물어보세요
                    </p>

                    {/* Clear chat button */}
                    {messages.length > 0 && (
                        <button
                            onClick={clearChat}
                            className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg
                                     text-white/40 hover:text-white/70 text-sm
                                     hover:bg-white/5 transition-all"
                        >
                            <Trash2 className="w-4 h-4" />
                            대화 초기화
                        </button>
                    )}
                </div>

                {/* Empty State Suggestions */}
                {messages.length === 0 && (
                    <div className="space-y-6 mb-8">
                        <p className="text-white/40 text-sm text-center flex items-center justify-center gap-2">
                            <Sparkles className="w-4 h-4" />
                            추천 질문으로 시작해보세요
                        </p>
                        <div className="flex flex-wrap justify-center gap-3">
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
                    {messages.map((message) => (
                        <ChatBubble
                            key={message.id}
                            message={message}
                            onActionClick={handleActionClick}
                        />
                    ))}

                    {/* Typing Indicator */}
                    {isLoading && <TypingIndicator />}

                    {/* Error */}
                    {error && (
                        <div className="flex justify-center mb-4">
                            <button
                                onClick={() => sendMessage(messages[messages.length - 2]?.content || '')}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg
                                         bg-red-500/10 border border-red-500/20
                                         text-red-400 text-sm hover:bg-red-500/20 transition-all"
                            >
                                <RefreshCcw className="w-4 h-4" />
                                다시 시도
                            </button>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Follow-up Suggestions */}
                {messages.length > 0 && !isLoading && (
                    <div className="flex flex-wrap justify-center gap-2 mb-4">
                        {suggestions.slice(0, 3).map(suggestion => (
                            <SuggestionChip
                                key={suggestion.id}
                                suggestion={suggestion}
                                onClick={() => handleSuggestionClick(suggestion)}
                                compact
                            />
                        ))}
                    </div>
                )}
            </main>

            {/* Fixed Input Bar */}
            <div className="fixed bottom-0 left-0 right-0 
                           bg-gradient-to-t from-zinc-950 via-zinc-950/98 to-transparent 
                           pt-8 pb-6 backdrop-blur-sm">
                <form onSubmit={handleSubmit} className="max-w-3xl mx-auto px-4">
                    <div className="relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-fuchsia-500 
                                       rounded-2xl opacity-0 group-focus-within:opacity-20 
                                       blur transition-all duration-300" />
                        <div className="relative flex items-center">
                            <input
                                ref={inputRef}
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="무엇이든 물어보세요..."
                                disabled={isLoading}
                                className="w-full px-5 py-4 pr-14 rounded-2xl
                                         bg-white/5 backdrop-blur-xl
                                         border border-white/10
                                         text-white placeholder-white/30
                                         focus:outline-none focus:border-purple-500/50
                                         disabled:opacity-50 transition-all duration-300"
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className="absolute right-2 p-3 rounded-xl
                                         bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white
                                         hover:from-purple-500 hover:to-fuchsia-500
                                         disabled:opacity-30 disabled:cursor-not-allowed
                                         transition-all duration-300 shadow-lg shadow-purple-500/20
                                         disabled:shadow-none"
                            >
                                {isLoading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5" />
                                )}
                            </button>
                        </div>
                    </div>
                    <p className="text-center text-white/25 text-xs mt-3">
                        에이전트는 실수할 수 있어요 · 중요한 정보는 직접 확인해주세요
                    </p>
                </form>
            </div>
        </div>
    );
}
