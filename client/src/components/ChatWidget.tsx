import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Send,
  X,
  ChevronLeft,
  ChevronRight,
  Globe,
  Settings,
  Info,
  User,
  MessageCircle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import Logo from "@/components/Logo";

interface Message {
  role: "user" | "assistant";
  content: string;
  products?: Product[];
  context?: ContextInfo;
}

interface Product {
  id: number;
  name: string;
  description?: string;
  category?: string;
  subcategory?: string;
  price?: number;
  brand?: string;
  image_url?: string;
  rating?: number;
}

interface TripSegment {
  destination: string;
  start_date: string;
  end_date: string;
}

interface SegmentContext {
  destination: string;
  start_date: string;
  end_date: string;
  weather?: {
    temperature?: number;
    description?: string;
  };
}

interface ContextInfo {
  intent?: {
    category?: string;
    occasion?: string;
    style?: string;
    budget_max?: number;
    location?: string;
    trip_segments?: TripSegment[];
  };
  environmental?: {
    weather?: {
      temperature?: number;
      description?: string;
    };
    trends?: string[];
    segments?: SegmentContext[];
  };
}

interface ChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatWidget({ isOpen, onClose }: ChatWidgetProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [currentContext, setCurrentContext] = useState<ContextInfo | null>(null);
  const [currentIntent, setCurrentIntent] = useState<Record<string, unknown>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [customerName, setCustomerName] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const storedCustomerId = localStorage.getItem("customer_id");
    const storedCustomerName = localStorage.getItem("customer_name");
    setCustomerId(storedCustomerId);
    setCustomerName(storedCustomerName);
  }, [isOpen]);

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const conversationHistory = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          user_id: customerId || "guest",
          conversation_history: conversationHistory,
          existing_intent: currentIntent,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      return response.json();
    },
    onSuccess: (data) => {
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        products: data.products,
        context: data.context,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (data.context) {
        setCurrentContext(data.context);
      }

      if (data.updated_intent) {
        setCurrentIntent(data.updated_intent);
      }

      if (data.products && data.products.length > 0) {
        setCurrentStep(10);
      } else if (data.clarification_needed) {
        setCurrentStep((prev) => Math.min(prev + 1, 9));
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    chatMutation.mutate(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setCurrentContext(null);
    setCurrentIntent({});
    setCurrentStep(1);
  };

  const formatPrice = (price?: number) => {
    if (!price) return "";
    return `$${(price / 100).toFixed(2)}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" data-testid="chat-overlay">
      <div className="bg-white w-full max-w-4xl h-[600px] rounded-lg shadow-2xl flex flex-col overflow-hidden" data-testid="chat-modal">
        <div className="bg-[#1565C0] text-white px-4 py-3 flex items-center justify-between" data-testid="chat-header">
          <div className="flex items-center gap-3">
            <Logo className="h-10" />
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>Online</span>
            </div>
            <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-user">
              <User className="w-5 h-5" />
            </button>
            <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-globe">
              <Globe className="w-5 h-5" />
            </button>
            <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-settings">
              <Settings className="w-5 h-5" />
            </button>
            <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-info">
              <Info className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-1 text-sm">
              <span>{currentStep}/10</span>
              <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-prev">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-next">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <button onClick={onClose} className="hover:bg-white/10 p-1 rounded" data-testid="btn-close-chat">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-48 bg-gray-100 p-4 border-r" data-testid="chat-sidebar">
            <h3 className="text-xs font-semibold text-gray-600 mb-4">CONVERSATION PROGRESS</h3>
            <div className="space-y-3">
              <div className={`flex items-center gap-2 ${currentStep >= 1 ? 'text-purple-600' : 'text-gray-400'}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${currentStep >= 1 ? 'bg-purple-600 text-white' : 'bg-gray-300'}`}>
                  1
                </div>
                <span className="text-sm">Welcome</span>
              </div>
              {currentStep > 1 && (
                <div className="ml-3 border-l-2 border-purple-200 h-4"></div>
              )}
            </div>
          </div>

          <div className="flex-1 flex flex-col">
            <ScrollArea className="flex-1 p-4" data-testid="chat-messages">
              {messages.length === 0 && (
                <div className="bg-gray-100 rounded-lg p-4 mb-4" data-testid="welcome-message">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <MessageCircle className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <p className="text-gray-800">
                        Hi {customerName || "there"}, how may I help you today?
                      </p>
                      <span className="text-xs text-gray-500 mt-1 block">
                        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`mb-4 ${message.role === "user" ? "flex justify-end" : ""}`}
                  data-testid={`message-${message.role}-${index}`}
                >
                  {message.role === "assistant" ? (
                    <div className="bg-gray-100 rounded-lg p-4 max-w-[80%]">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-full flex items-center justify-center flex-shrink-0">
                          <MessageCircle className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex-1">
                          <div className="prose prose-sm max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {message.content}
                            </ReactMarkdown>
                          </div>

                          {message.products && message.products.length > 0 && (
                            <div className="mt-4 grid grid-cols-2 gap-3">
                              {message.products.slice(0, 4).map((product) => (
                                <div
                                  key={product.id}
                                  className="bg-white rounded-lg p-3 border shadow-sm"
                                  data-testid={`product-card-${product.id}`}
                                >
                                  <div className="w-full h-24 bg-gray-100 rounded mb-2 flex items-center justify-center text-gray-400 text-xs">
                                    {product.category || "Product"}
                                  </div>
                                  <h4 className="font-medium text-sm text-gray-800 truncate">{product.name}</h4>
                                  <p className="text-xs text-gray-500">{product.brand}</p>
                                  <p className="text-sm font-semibold text-gray-900 mt-1">
                                    {formatPrice(product.price)}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-purple-600 text-white rounded-lg p-3 max-w-[70%]">
                      <p>{message.content}</p>
                    </div>
                  )}
                </div>
              ))}

              {chatMutation.isPending && (
                <div className="flex items-center gap-2 text-gray-500" data-testid="typing-indicator">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                  </div>
                  <span className="text-sm">Thinking...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </ScrollArea>

            <div className="border-t p-4" data-testid="chat-input-area">
              <form onSubmit={handleSubmit} className="flex items-end gap-2">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask me anything about style or travel..."
                  className="flex-1 min-h-[44px] max-h-32 resize-none"
                  disabled={chatMutation.isPending}
                  data-testid="chat-input"
                />
                <Button
                  type="submit"
                  disabled={chatMutation.isPending || !input.trim()}
                  className="bg-purple-600 hover:bg-purple-700 h-11 w-11 p-0"
                  data-testid="btn-send"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
