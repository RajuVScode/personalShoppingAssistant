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
  Sparkles,
  Cloud,
  TrendingUp,
  Calendar,
  RefreshCw,
  ShoppingBag,
  LogIn,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
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
  const [isAnimating, setIsAnimating] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginCustomerId, setLoginCustomerId] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setIsAnimating(true);
        });
      });
    } else {
      setIsAnimating(false);
      const timer = setTimeout(() => {
        setShouldRender(false);
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  useEffect(() => {
    const storedCustomerId = localStorage.getItem("customer_id");
    const storedCustomerName = localStorage.getItem("customer_name");
    setCustomerId(storedCustomerId);
    setCustomerName(storedCustomerName);

    if (isOpen && storedCustomerId && messages.length === 0) {
      loadConversation(storedCustomerId);
    }
  }, [isOpen]);

  const loadConversation = async (storedCustomerId: string) => {
    const userId = parseInt(storedCustomerId.replace("CUST-", "")) || 1;
    
    const greetingRes = await fetch(`/api/greeting/${storedCustomerId}`);
    const greetingData = await greetingRes.json();
    const greetingMessage: Message = { 
      role: "assistant", 
      content: greetingData.greeting || "How may I assist you?" 
    };
    
    const convRes = await fetch(`/api/conversation/${userId}`);
    const convData = await convRes.json();
    
    if (convData.messages && convData.messages.length > 0) {
      const restoredMessages: Message[] = convData.messages.map((msg: { role: string; content: string }) => ({
        role: msg.role as "user" | "assistant",
        content: msg.content,
      }));
      setMessages([greetingMessage, ...restoredMessages]);
      if (convData.context) {
        setCurrentContext(convData.context);
      }
    } else {
      setMessages([greetingMessage]);
    }
  };

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const storedId = localStorage.getItem("customer_id");
      const userId = storedId ? parseInt(storedId.replace("CUST-", "")) : 1;
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          user_id: userId,
        }),
      });
      if (!response.ok) throw new Error("Failed to send message");
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

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    chatMutation.mutate(input);
    setInput("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const resetConversation = async () => {
    const storedId = localStorage.getItem("customer_id");
    const userId = storedId ? parseInt(storedId.replace("CUST-", "")) : 1;
    await fetch(`/api/reset?user_id=${userId}`, { method: "POST" });
    setCurrentContext(null);
    setCurrentIntent({});
    setCurrentStep(1);

    if (storedId) {
      const res = await fetch(`/api/greeting/${storedId}`);
      const data = await res.json();
      setMessages(
        data.greeting ? [{ role: "assistant", content: data.greeting }] : [],
      );
    } else {
      setMessages([]);
    }
  };

  const handleClose = () => {
    onClose();
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!loginCustomerId.trim() || !loginPassword.trim()) {
      toast({
        title: "Error",
        description: "Please enter both Customer ID and Password",
        variant: "destructive",
      });
      return;
    }

    setIsLoggingIn(true);
    
    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          customer_id: loginCustomerId.toUpperCase().trim(), 
          password: loginPassword 
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        localStorage.setItem("customer_id", data.customer.customer_id);
        localStorage.setItem("customer_name", `${data.customer.first_name} ${data.customer.last_name}`);
        setCustomerId(data.customer.customer_id);
        setCustomerName(`${data.customer.first_name} ${data.customer.last_name}`);
        toast({
          title: "Welcome!",
          description: `Logged in as ${data.customer.first_name} ${data.customer.last_name}`,
        });
        setShowLoginModal(false);
        setLoginCustomerId("");
        setLoginPassword("");
        loadConversation(data.customer.customer_id);
      } else {
        toast({
          title: "Login Failed",
          description: data.message || "Invalid Customer ID or Password",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Unable to connect to the server. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("customer_id");
    localStorage.removeItem("customer_name");
    setCustomerId(null);
    setCustomerName(null);
    setMessages([]);
    setCurrentContext(null);
    setCurrentIntent({});
    setCurrentStep(1);
    toast({
      title: "Logged out",
      description: "You have been logged out successfully",
    });
  };

  if (!shouldRender) return null;

  return (
    <div 
      className={`fixed inset-0 z-50 flex items-center justify-end pr-[3%] bg-black/50 transition-opacity duration-500 ${isAnimating ? 'opacity-100' : 'opacity-0'}`} 
      data-testid="chat-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div 
        className={`bg-white w-[90vw] h-[95vh] rounded-[5px] shadow-2xl flex flex-col overflow-hidden transition-transform duration-500 ease-in-out ${isAnimating ? 'translate-x-0' : 'translate-x-[105%]'}`} 
        data-testid="chat-modal"
      >
        <div className="bg-[#1565C0] text-white px-4 py-1.5 flex items-center justify-between" data-testid="chat-header">
          <div className="flex items-center gap-3">
            <Logo className="h-10" />
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>Online</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetConversation}
              className="text-white hover:bg-white/10"
              data-testid="button-reset"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              New Chat
            </Button>
            <button 
              className="hover:bg-white/10 p-1 rounded flex items-center gap-1" 
              data-testid="btn-user"
              onClick={() => customerName ? handleLogout() : setShowLoginModal(true)}
              title={customerName ? `Logout (${customerName})` : "Login"}
            >
              {customerName ? (
                <>
                  <User className="w-5 h-5" />
                  <span className="text-xs max-w-[80px] truncate">{customerName.split(' ')[0]}</span>
                </>
              ) : (
                <LogIn className="w-5 h-5" />
              )}
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
            <button onClick={handleClose} className="hover:bg-white/10 p-1 rounded" data-testid="btn-close-chat">
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
              {currentStep >= 2 && (
                <>
                  <div className={`flex items-center gap-2 ${currentStep >= 2 ? 'text-purple-600' : 'text-gray-400'}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${currentStep >= 2 ? 'bg-purple-600 text-white' : 'bg-gray-300'}`}>
                      2
                    </div>
                    <span className="text-sm">Destination</span>
                  </div>
                  {currentStep > 2 && (
                    <div className="ml-3 border-l-2 border-purple-200 h-4"></div>
                  )}
                </>
              )}
              {currentStep >= 3 && (
                <>
                  <div className={`flex items-center gap-2 ${currentStep >= 3 ? 'text-purple-600' : 'text-gray-400'}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${currentStep >= 3 ? 'bg-purple-600 text-white' : 'bg-gray-300'}`}>
                      3
                    </div>
                    <span className="text-sm">Dates</span>
                  </div>
                  {currentStep > 3 && (
                    <div className="ml-3 border-l-2 border-purple-200 h-4"></div>
                  )}
                </>
              )}
              {currentStep >= 4 && (
                <>
                  <div className={`flex items-center gap-2 ${currentStep >= 4 ? 'text-purple-600' : 'text-gray-400'}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${currentStep >= 4 ? 'bg-purple-600 text-white' : 'bg-gray-300'}`}>
                      4
                    </div>
                    <span className="text-sm">Activities</span>
                  </div>
                  {currentStep > 4 && (
                    <div className="ml-3 border-l-2 border-purple-200 h-4"></div>
                  )}
                </>
              )}
              {currentStep === 10 && (
                <>
                  <div className="flex items-center gap-2 text-green-600">
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium bg-green-600 text-white">
                      <ShoppingBag className="w-3 h-3" />
                    </div>
                    <span className="text-sm">Recommendations</span>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="flex-1 flex flex-col">
            <ScrollArea className="flex-1 p-6" data-testid="chat-messages">
              <div className="space-y-6">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${message.role === "user" ? "justify-end" : ""}`}
                  >
                    {message.role === "assistant" && (
                      <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
                        <Sparkles className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] ${message.role === "user" ? "order-first" : ""}`}
                    >
                      <div
                        className={`rounded-2xl px-4 py-3 ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground ml-auto"
                            : "bg-muted"
                        }`}
                        data-testid={`message-${message.role}-${index}`}
                      >
                        {message.role === "assistant" ? (
                          <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:mt-2 prose-headings:mb-1 prose-p:my-1 prose-ul:my-1 prose-li:my-0 prose-hr:my-2">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <p className="whitespace-pre-wrap">
                            {message.content}
                          </p>
                        )}
                      </div>

                      {message.products && message.products.length > 0 && (
                        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                          {message.products.slice(0, 6).map((product) => (
                            <Card
                              key={product.id}
                              className="overflow-hidden hover:shadow-lg transition-shadow"
                              data-testid={`card-product-${product.id}`}
                            >
                              {product.image_url && (
                                <div className="aspect-[4/3] bg-muted overflow-hidden max-h-32">
                                  <img
                                    src={product.image_url}
                                    alt={product.name}
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                      (e.target as HTMLImageElement).src =
                                        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400";
                                    }}
                                  />
                                </div>
                              )}
                              <CardContent className="p-3">
                                <p className="font-medium text-sm line-clamp-1">
                                  {product.name}
                                </p>
                                <div className="flex items-center justify-between mt-1">
                                  <span className="text-xs text-muted-foreground">
                                    {product.brand}
                                  </span>
                                  {product.price && (
                                    <span className="font-semibold text-sm">
                                      ${product.price}
                                    </span>
                                  )}
                                </div>
                                {product.rating && (
                                  <div className="flex items-center gap-1 mt-1">
                                    <span className="text-yellow-500 text-xs">
                                      ★
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                      {product.rating}
                                    </span>
                                  </div>
                                )}
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}
                    </div>
                    {message.role === "user" && (
                      <div className="h-8 w-8 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                        <User className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                ))}

                {chatMutation.isPending && (
                  <div className="flex gap-3">
                    <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
                      <Sparkles className="h-4 w-4 text-primary-foreground" />
                    </div>
                    <div className="bg-muted rounded-2xl px-4 py-3">
                      <div className="flex gap-1">
                        <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" />
                        <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0.1s" }} />
                        <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0.2s" }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="border-t px-6 py-4">
              <div className="relative flex items-end gap-3 bg-muted/30 border border-muted-foreground/10 p-3 pl-[5px] pr-[5px] pt-[5px] pb-[5px]" style={{ borderRadius: '12px' }}>
                <div className="flex-1">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="What are you looking for today?"
                    className="min-h-[40px] max-h-[120px] resize-none border-none bg-transparent p-[10px] shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 focus:outline-none text-sm"
                    style={{ border: 'none', outline: 'none' }}
                    disabled={chatMutation.isPending}
                    data-testid="input-message"
                    rows={1}
                  />
                </div>
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || chatMutation.isPending}
                  size="icon"
                  className="rounded-full h-9 w-9 shrink-0 disabled:opacity-100 disabled:pointer-events-auto"
                  style={{ 
                    backgroundColor: '#0d6efd',
                    cursor: (!input.trim() || chatMutation.isPending) ? 'not-allowed' : 'pointer'
                  }}
                  data-testid="button-send"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {currentContext && (
            <div className="w-72 border-l p-4 hidden lg:block">
              <h3 className="font-medium text-sm mb-4 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                Context Insights
              </h3>

              {currentContext.intent && (
                <div className="mb-4">
                  <p className="text-xs text-muted-foreground mb-2">
                    Understood Intent
                  </p>
                  <div className="space-y-1">
                    {currentContext.intent.category && (
                      <Badge variant="secondary" className="mr-1">
                        {currentContext.intent.category}
                      </Badge>
                    )}
                    {currentContext.intent.occasion &&
                      !currentContext.intent.trip_segments?.length && (
                        <Badge variant="outline" className="mr-1">
                          {currentContext.intent.occasion}
                        </Badge>
                      )}
                    {currentContext.intent.style && (
                      <Badge variant="outline">
                        {currentContext.intent.style}
                      </Badge>
                    )}
                  </div>
                </div>
              )}

              {currentContext.intent?.trip_segments &&
                currentContext.intent.trip_segments.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                      <Calendar className="h-3 w-3" /> Trip Destinations
                    </p>
                    <div className="space-y-2">
                      {currentContext.intent.trip_segments.map((segment, i) => (
                        <div key={i} className="bg-muted/50 rounded-lg p-2">
                          <p className="text-sm font-medium">
                            {segment.destination}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {segment.start_date} to {segment.end_date}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              <Separator className="my-4" />

              {currentContext.environmental?.segments &&
              currentContext.environmental.segments.length > 0 ? (
                <div className="mb-4">
                  <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                    <Cloud className="h-3 w-3" /> Weather by Destination
                  </p>
                  <div className="space-y-2">
                    {currentContext.environmental.segments.map((seg, i) => (
                      <div key={i} className="bg-muted/50 rounded-lg p-2">
                        <p className="text-sm font-medium">{seg.destination}</p>
                        {seg.weather && (
                          <p className="text-xs text-muted-foreground">
                            {seg.weather.temperature}°C -{" "}
                            {seg.weather.description}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                currentContext.environmental?.weather && (
                  <div className="mb-4">
                    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                      <Cloud className="h-3 w-3" /> Weather
                    </p>
                    <p className="text-sm">
                      {currentContext.environmental.weather.temperature}°C -{" "}
                      {currentContext.environmental.weather.description}
                    </p>
                  </div>
                )
              )}

              {currentContext.environmental?.trends &&
                currentContext.environmental.trends.length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" /> Trending
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {currentContext.environmental.trends
                        .slice(0, 3)
                        .map((trend, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {trend}
                          </Badge>
                        ))}
                    </div>
                  </div>
                )}
            </div>
          )}
        </div>
      </div>

      {showLoginModal && (
        <div 
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowLoginModal(false);
          }}
        >
          <Card className="w-full max-w-md mx-4 shadow-2xl">
            <CardHeader className="text-center pb-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <CardTitle className="text-xl font-bold text-gray-800">
                    Welcome back
                  </CardTitle>
                  <CardDescription>
                    Sign in with your Customer ID to get personalized recommendations
                  </CardDescription>
                </div>
                <button 
                  onClick={() => setShowLoginModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="loginCustomerId">Customer ID / User Name</Label>
                  <Input
                    id="loginCustomerId"
                    type="text"
                    placeholder="e.g., CUST-0000001"
                    value={loginCustomerId}
                    onChange={(e) => setLoginCustomerId(e.target.value)}
                    data-testid="input-login-customer-id"
                    disabled={isLoggingIn}
                    className="h-11"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="loginPassword">Password</Label>
                  <Input
                    id="loginPassword"
                    type="password"
                    placeholder="Enter your password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    data-testid="input-login-password"
                    disabled={isLoggingIn}
                    className="h-11"
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full h-11 bg-[#1565C0] hover:bg-[#0D47A1]"
                  disabled={isLoggingIn}
                  data-testid="button-login-submit"
                >
                  {isLoggingIn ? "Signing in..." : "Sign In"}
                </Button>
              </form>
              <p className="text-sm text-gray-500 text-center mt-4">
                Default password: password123
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
