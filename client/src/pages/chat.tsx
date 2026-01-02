import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Send,
  Sparkles,
  User,
  ShoppingBag,
  Cloud,
  TrendingUp,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { useLocation } from "wouter";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

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

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [currentContext, setCurrentContext] = useState<ContextInfo | null>(
    null,
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [customerName, setCustomerName] = useState<string | null>(null);
  const [, setLocation] = useLocation();

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

    const loadConversation = async () => {
      if (storedCustomerId) {
        const userId = parseInt(storedCustomerId.replace("CUST-", "")) || 1;
        
        // Always fetch the greeting first
        const greetingRes = await fetch(`/api/greeting/${storedCustomerId}`);
        const greetingData = await greetingRes.json();
        const greetingMessage: Message = { role: "assistant", content: greetingData.greeting || "How may I assist you?" };
        
        // Try to load existing conversation
        const convRes = await fetch(`/api/conversation/${userId}`);
        const convData = await convRes.json();
        
        if (convData.messages && convData.messages.length > 0) {
          // Restore existing conversation with greeting prepended
          const restoredMessages: Message[] = convData.messages.map((msg: { role: string; content: string }) => ({
            role: msg.role as "user" | "assistant",
            content: msg.content,
          }));
          // Prepend greeting if not already present
          setMessages([greetingMessage, ...restoredMessages]);
          if (convData.context) {
            setCurrentContext(convData.context);
          }
        } else {
          // No existing conversation, show greeting only
          setMessages([greetingMessage]);
        }
      }
    };
    loadConversation();
  }, []);

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

  return (
    <div className="min-h-screen bg-background flex">
      <div className="flex-1 flex flex-col max-w-6xl mx-auto w-full">
        <header className="border-b px-6 py-4 flex items-center justify-between glass-effect sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1
                className="text-lg font-semibold"
                data-testid="text-app-title"
              >
                AI Shopping Assistant
              </h1>
              <p className="text-sm text-muted-foreground">
                Personalized recommendations just for you
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={resetConversation}
              data-testid="button-reset"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              New Chat
            </Button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          <ScrollArea className="flex-1 p-6 scrollbar-thin">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center py-8">
                <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                  <ShoppingBag className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-2xl font-semibold mb-2">
                  Welcome to AI Shopping
                </h2>
                <p
                  className="text-muted-foreground max-w-md mb-6"
                  data-testid="text-greeting"
                >
                  Good day! {customerName || "Guest"}, How may I assist you with
                  your travel shopping? I'll find personalized recommendations
                  based on your style, the weather, and current trends.
                </p>
                <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                  {[
                    "I need shoes for a wedding",
                    "Something warm for winter",
                    "Casual weekend outfit",
                    "Professional work attire",
                  ].map((suggestion) => (
                    <Button
                      key={suggestion}
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                      onClick={() => setInput(suggestion)}
                      data-testid={`button-suggestion-${suggestion.slice(0, 10)}`}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 message-enter ${message.role === "user" ? "justify-end" : ""}`}
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
                        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {message.products.slice(0, 4).map((product) => (
                            <Card
                              key={product.id}
                              className="product-card-hover overflow-hidden"
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
                  <div className="flex gap-3 message-enter">
                    <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
                      <Sparkles className="h-4 w-4 text-primary-foreground" />
                    </div>
                    <div className="bg-muted rounded-2xl px-4 py-3">
                      <div className="typing-indicator flex gap-1">
                        <span className="h-2 w-2 rounded-full bg-muted-foreground" />
                        <span className="h-2 w-2 rounded-full bg-muted-foreground" />
                        <span className="h-2 w-2 rounded-full bg-muted-foreground" />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </ScrollArea>

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

        <div className="border-t px-6 py-4 glass-effect">
          <div className="max-w-3xl">
            <div className="relative flex items-end gap-3 bg-muted/30 border border-muted-foreground/10 p-3" style={{ borderRadius: '12px' }}>
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
                className="rounded-full h-9 w-9 shrink-0"
                style={{ backgroundColor: '#0d6efd' }}
                data-testid="button-send"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
