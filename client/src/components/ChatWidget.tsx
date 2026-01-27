/**
 * ChatWidget Component
 * 
 * The main conversational interface for the AI shopping assistant.
 * This component handles:
 * - User chat interactions with the AI assistant
 * - Product recommendations display with interactive cards
 * - Shopping cart management (add/remove items, checkout flow)
 * - Context insights modal (weather, events, customer profile)
 * - Agent thinking log modal (shows AI reasoning process)
 * - Online/In-Store mode toggle
 * - QR code scanning for in-store product lookup
 * - Customer 360 profile viewer
 * 
 * The widget appears as a floating chat bubble that expands into
 * a full-featured shopping assistant interface.
 */

import { useState, useRef, useEffect, useCallback, useMemo, memo } from "react";
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
  ShoppingCart,
  LogIn,
  LogOut,
  Check,
  Plus,
  ChevronDown,
  Trash2,
  Package,
  Store,
  CalendarDays,
  ChevronUp,
  QrCode,
  Phone,
  Camera,
  Upload,
  MapPin,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ProductDetailPanel } from "./ProductDetailPanel";
import { ProductCard } from "./ProductCard";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";
import Logo from "@/components/Logo";
import { Html5Qrcode } from "html5-qrcode";
import { useBasket } from "@/components/Basket";
import "@/styles/chat-widget.css";

/**
 * Represents a step in the AI agent's thinking process.
 * Displayed in the Agent Thinking Log modal to show users
 * how the AI arrived at its recommendations.
 */
interface AgentThinkingStep {
  agent: string;
  action: string;
  details?: Record<string, any>;
  timestamp?: string;
}

/**
 * Represents a chat message in the conversation.
 * Can include product recommendations and context information
 * alongside the text content.
 */
interface Message {
  role: "user" | "assistant";
  content: string;
  products?: Product[];
  context?: ContextInfo;
  agentThinking?: AgentThinkingStep[];
  timestamp?: Date;
  suggestions?: string[];
}

/**
 * Product data structure for recommendations.
 */
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
  [key: string]: unknown;
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
    travel_date?: string;
    trip_duration_days?: number;
    trip_segments?: TripSegment[];
  };
  environmental?: {
    weather?: {
      temperature?: number;
      high_temp?: number;
      low_temp?: number;
      description?: string;
      precipitation?: number;
      wind?: string;
      humidity?: string;
    };
    trends?: string[];
    segments?: SegmentContext[];
  };
}

interface CartItem {
  product: Product;
  quantity: number;
}

interface Customer360Data {
  profile: {
    name: string;
    age: number;
    location: string;
    tier: string;
  };
  sizes_fit: {
    tops: string;
    bottoms: string;
    shoes: string;
    height: string;
    build: string;
    skin: string;
  };
  style_preferences: {
    preferred_colors: string[];
    style: string;
    budget: string;
  };
  favorite_brands: string[];
}

interface ChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
}

const isTravelIntent = (context: ContextInfo | null): boolean => {
  if (!context) return false;
  return !!(
    (context.intent?.trip_segments && context.intent.trip_segments.length > 0) ||
    context.intent?.location
  );
};

export default function ChatWidget({ isOpen, onClose }: ChatWidgetProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const { addToCart, isInCart, totalItems, openBasket } = useBasket();
  const [currentContext, setCurrentContext] = useState<ContextInfo | null>(null);
  const [currentIntent, setCurrentIntent] = useState<Record<string, unknown>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatModalRef = useRef<HTMLDivElement>(null);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [customerName, setCustomerName] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [isAnimating, setIsAnimating] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginCustomerId, setLoginCustomerId] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [customer360Data, setCustomer360Data] = useState<Customer360Data | null>(null);
  const [showCustomer360Modal, setShowCustomer360Modal] = useState(false);
  const [isCustomer360Animating, setIsCustomer360Animating] = useState(false);
  const [shouldRenderCustomer360, setShouldRenderCustomer360] = useState(false);
  const [showContextInsightsModal, setShowContextInsightsModal] = useState(false);
  const [isContextInsightsAnimating, setIsContextInsightsAnimating] = useState(false);
  const [shouldRenderContextInsights, setShouldRenderContextInsights] = useState(false);
  const [shoppingMode, setShoppingMode] = useState<"online" | "instore">("online");
  const [agentThinkingLogs, setAgentThinkingLogs] = useState<AgentThinkingStep[]>([]);
  const [isAgentThinkingAnimating, setIsAgentThinkingAnimating] = useState(false);
  const [shouldRenderAgentThinking, setShouldRenderAgentThinking] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isProductDetailAnimating, setIsProductDetailAnimating] = useState(false);
  const [shouldRenderProductDetail, setShouldRenderProductDetail] = useState(false);
  const [showScanProductModal, setShowScanProductModal] = useState(false);
  const [scanningState, setScanningState] = useState<"ready" | "scanning" | "loading" | "not_found">("ready");
  const [scannedProductId, setScannedProductId] = useState<number | null>(null);
  const scannerRef = useRef<any>(null);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [locationProduct, setLocationProduct] = useState<Product | null>(null);
  const [isStartingNavigation, setIsStartingNavigation] = useState(false);
  const { toast } = useToast();

  const fetchCustomer360 = async (custId: string) => {
    try {
      const response = await fetch(`/api/customer360/${custId}`);
      if (response.ok) {
        const data = await response.json();
        setCustomer360Data(data);
      }
    } catch (error) {
      console.error("Failed to fetch customer 360 data:", error);
    }
  };

  const openContextInsightsModal = () => {
    setShouldRenderContextInsights(true);
    setTimeout(() => {
      setIsContextInsightsAnimating(true);
    }, 50);
  };

  const closeContextInsightsModal = () => {
    setIsContextInsightsAnimating(false);
    setTimeout(() => {
      setShouldRenderContextInsights(false);
      setShowContextInsightsModal(false);
    }, 300);
  };

  const openCustomer360Modal = () => {
    setShouldRenderCustomer360(true);
    setTimeout(() => {
      setIsCustomer360Animating(true);
    }, 50);
  };

  const closeCustomer360Modal = () => {
    setIsCustomer360Animating(false);
    setTimeout(() => {
      setShouldRenderCustomer360(false);
      setShowCustomer360Modal(false);
    }, 300);
  };

  const openAgentThinkingModal = () => {
    setShouldRenderAgentThinking(true);
    setTimeout(() => {
      setIsAgentThinkingAnimating(true);
    }, 50);
  };

  const closeAgentThinkingModal = () => {
    setIsAgentThinkingAnimating(false);
    setTimeout(() => {
      setShouldRenderAgentThinking(false);
    }, 300);
  };

  const openProductDetail = (product: Product) => {
    setSelectedProduct(product);
    setShouldRenderProductDetail(true);
    setTimeout(() => {
      setIsProductDetailAnimating(true);
    }, 50);
  };

  const closeProductDetail = () => {
    setIsProductDetailAnimating(false);
    setTimeout(() => {
      setShouldRenderProductDetail(false);
      setSelectedProduct(null);
    }, 300);
  };

  const closeScanModal = useCallback(() => {
    if (scannerRef.current) {
      scannerRef.current.stop().catch(() => {});
      scannerRef.current = null;
    }
    setShowScanProductModal(false);
    setScanningState("ready");
    setScannedProductId(null);
  }, []);

  const startScanning = useCallback(() => {
    setScanningState("scanning");
  }, []);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const extractProductId = (text: string): { productId: number | null; decodedText: string } => {
    console.log("QR Code decoded text:", text);
    
    if (text.startsWith("PRODUCT:")) {
      return { productId: parseInt(text.replace("PRODUCT:", ""), 10), decodedText: text };
    }
    
    if (/^\d+$/.test(text.trim())) {
      return { productId: parseInt(text.trim(), 10), decodedText: text };
    }
    
    const patterns = [
      /product[\/=](\d+)/i,
      /productId[=:](\d+)/i,
      /id[=:](\d+)/i,
      /\/(\d+)$/,
      /[?&]id=(\d+)/i,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return { productId: parseInt(match[1], 10), decodedText: text };
      }
    }
    
    return { productId: null, decodedText: text };
  };

  const handleQrUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    setScanningState("loading");
    
    try {
      const html5QrCode = new Html5Qrcode("qr-upload-reader");
      const decodedText = await html5QrCode.scanFile(file, true);
      
      const { productId, decodedText: qrText } = extractProductId(decodedText);
      
      toast({
        description: `QR decoded: "${qrText.substring(0, 100)}${qrText.length > 100 ? '...' : ''}"`,
      });
      
      if (productId && !isNaN(productId)) {
        setScannedProductId(productId);
        
        try {
          const response = await fetch(`/api/products/${productId}`);
          if (response.ok) {
            const productData = await response.json();
            setShowScanProductModal(false);
            setScanningState("ready");
            setScannedProductId(null);
            setSelectedProduct(productData);
            setShouldRenderProductDetail(true);
            setTimeout(() => setIsProductDetailAnimating(true), 50);
          } else {
            setScanningState("not_found");
          }
        } catch {
          setScanningState("not_found");
        }
      } else {
        setScanningState("not_found");
      }
    } catch (err) {
      console.error("Failed to scan QR from image:", err);
      toast({
        description: "Could not read QR code from the image. Please try a clearer image.",
        variant: "destructive",
      });
      setScanningState("ready");
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [toast]);

  useEffect(() => {
    if (scanningState !== "scanning") return;
    
    const initScanner = async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const element = document.getElementById("qr-reader");
      if (!element) {
        console.error("QR reader element not found");
        setScanningState("ready");
        return;
      }
      
      try {
        const html5QrCode = new Html5Qrcode("qr-reader");
        scannerRef.current = html5QrCode;
        
        await html5QrCode.start(
          { facingMode: "environment" },
          {
            fps: 10,
            qrbox: { width: 200, height: 200 },
          },
          async (decodedText) => {
            await html5QrCode.stop();
            scannerRef.current = null;
            
            const { productId } = extractProductId(decodedText);
            
            if (productId && !isNaN(productId)) {
              setScanningState("loading");
              setScannedProductId(productId);
              
              try {
                const response = await fetch(`/api/products/${productId}`);
                if (response.ok) {
                  const productData = await response.json();
                  setShowScanProductModal(false);
                  setScanningState("ready");
                  setScannedProductId(null);
                  setSelectedProduct(productData);
                  setShouldRenderProductDetail(true);
                  setTimeout(() => setIsProductDetailAnimating(true), 50);
                } else {
                  setScanningState("not_found");
                }
              } catch {
                setScanningState("not_found");
              }
            } else {
              setScanningState("not_found");
            }
          },
          () => {}
        );
      } catch (err) {
        console.error("Failed to start scanner:", err);
        toast({
          description: "Could not access camera. Please check permissions.",
          variant: "destructive",
        });
        setScanningState("ready");
      }
    };
    
    initScanner();
    
    return () => {
      if (scannerRef.current) {
        scannerRef.current.stop().catch(() => {});
        scannerRef.current = null;
      }
    };
  }, [scanningState, toast]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      setShouldRender(true);
      const timer = setTimeout(() => {
        setIsAnimating(true);
      }, 50);
      return () => clearTimeout(timer);
    } else {
      document.body.style.overflow = '';
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

    if (isOpen && storedCustomerId) {
      if (messages.length === 0) {
        loadConversation(storedCustomerId);
      }
      if (!customer360Data) {
        fetchCustomer360(storedCustomerId);
      }
    }
  }, [isOpen]);

  const loadConversation = async (storedCustomerId: string) => {
    const userId = parseInt(storedCustomerId.replace("CUST-", "")) || 1;
    
    const greetingRes = await fetch(`/api/greeting/${storedCustomerId}`);
    const greetingData = await greetingRes.json();
    const greetingMessage: Message = { 
      role: "assistant", 
      content: greetingData.greeting || "How may I assist you?",
      timestamp: new Date()
    };
    
    const convRes = await fetch(`/api/conversation/${userId}`);
    const convData = await convRes.json();
    
    if (convData.messages && convData.messages.length > 0) {
      const restoredMessages: Message[] = convData.messages.map((msg: { role: string; content: string; products?: Product[] }) => ({
        role: msg.role as "user" | "assistant",
        content: msg.content,
        products: msg.products || undefined,
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
        agentThinking: data.agent_thinking,
        timestamp: new Date(),
        suggestions: data.suggestions
      };
      setMessages((prev) => [...prev, assistantMessage]);
      if (data.agent_thinking && data.agent_thinking.length > 0) {
        setAgentThinkingLogs(data.agent_thinking);
      }
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

    const userMessage: Message = { role: "user", content: input, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    chatMutation.mutate(input);
    setInput("");
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (chatMutation.isPending) return;
    
    const userMessage: Message = { role: "user", content: suggestion, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    chatMutation.mutate(suggestion);
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
    setAgentThinkingLogs([]);

    if (storedId) {
      const res = await fetch(`/api/greeting/${storedId}`);
      const data = await res.json();
      setMessages(
        data.greeting ? [{ role: "assistant", content: data.greeting, timestamp: new Date() }] : [],
      );
    } else {
      setMessages([]);
      setAgentThinkingLogs([]);
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
        fetchCustomer360(data.customer.customer_id);
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
    setAgentThinkingLogs([]);
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
      className={`chat-overlay ${isAnimating ? 'chat-overlay--visible' : 'chat-overlay--hidden'}`} 
      data-testid="chat-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div 
        ref={chatModalRef}
        className={`chat-modal-container ${isAnimating ? 'chat-modal--visible' : 'chat-modal--hidden'}`} 
        data-testid="chat-modal"
      >
        <div className="chat-header-bar" data-testid="chat-header">
          <div className="chat-header-left">
            <div className="chat-header-avatar">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="chat-header-avatar-icon">
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <Logo className="chat-header-logo" />
          </div>

          <div className="chat-header-right">
            <button
              onClick={() => setShoppingMode(shoppingMode === "online" ? "instore" : "online")}
              className={`chat-mode-btn ${shoppingMode === "online" ? "chat-mode-btn--online" : "chat-mode-btn--instore"}`}
              data-testid="toggle-shopping-mode"
            >
              {shoppingMode === "online" ? (
                <>
                  <svg className="chat-mode-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                  <span className="chat-mode-btn-text">Online</span>
                </>
              ) : (
                <>
                  <svg className="chat-mode-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                    <polyline points="9 22 9 12 15 12 15 22" />
                  </svg>
                  <span className="chat-mode-btn-text">In-Store</span>
                </>
              )}
            </button>
            <button 
              className="hover:bg-gray-100 p-1 rounded text-gray-700" 
              data-testid="btn-globe"
              onClick={() => {
                if (customerId && customer360Data) {
                  openCustomer360Modal();
                } else if (!customerId) {
                  toast({
                    title: "Login Required",
                    description: "Please login to view your profile",
                  });
                }
              }}
            >
              <div className="relative">
                <div className="w-5 h-5 rounded-full border-[1.5px] border-gray-700 flex items-center justify-center">
                  <User className="w-3 h-3" />
                </div>
                <div className="absolute -bottom-0.5 -right-1 bg-gray-700 text-white text-[5px] font-bold px-0.5 rounded leading-tight">360</div>
              </div>
            </button>
            <button 
              className="chat-header-btn" 
              data-testid="btn-settings"
              onClick={openAgentThinkingModal}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="chat-header-btn-icon">
                <path fillRule="evenodd" d="M14.269 1.322a3.751 3.751 0 0 1 4.456 3.25 4.753 4.753 0 0 1 3.022 4.62 4.757 4.757 0 0 1-.318 1.522 4.75 4.75 0 0 1-.537 7.055c-.047.036-.096.07-.144.104a4.752 4.752 0 0 1-4.44 4.863A4.753 4.753 0 0 1 12 20.555a4.752 4.752 0 0 1-7.667.459 4.75 4.75 0 0 1-1.082-3.14 4.751 4.751 0 0 1-.682-7.16 4.756 4.756 0 0 1 .079-3.62 4.75 4.75 0 0 1 2.626-2.52A3.752 3.752 0 0 1 12 2.751a3.748 3.748 0 0 1 2.269-1.43Zm-4.83 1.471a2.252 2.252 0 0 0-2.387 3.332.75.75 0 0 1-1.299.75 3.762 3.762 0 0 1-.32-.722 3.25 3.25 0 0 0-1.411 1.543 3.251 3.251 0 0 0-.171 2.108.748.748 0 0 1 .524 1.382A3.252 3.252 0 0 0 2.86 14.84 3.252 3.252 0 0 0 6 17.251a.75.75 0 0 1 0 1.5 4.75 4.75 0 0 1-1.194-.154 3.276 3.276 0 0 0 .685 1.464 3.251 3.251 0 0 0 5.76-2.062v-5.467a4.92 4.92 0 0 1-2.04 1.188.75.75 0 0 1-.42-1.44 3.421 3.421 0 0 0 2.447-3.004L11.25 9V5a2.252 2.252 0 0 0-1.81-2.207Zm6.143.034a2.252 2.252 0 0 0-1.952.388 2.25 2.25 0 0 0-.865 1.527L12.75 5v4l.01.276a3.42 3.42 0 0 0 2.45 3.005.75.75 0 0 1-.42 1.439 4.92 4.92 0 0 1-2.04-1.187V18a3.252 3.252 0 0 0 2.154 3.056 3.253 3.253 0 0 0 3.605-.994 3.251 3.251 0 0 0 .683-1.464A4.75 4.75 0 0 1 18 18.75a.75.75 0 0 1 0-1.5 3.251 3.251 0 0 0 1.625-6.064.747.747 0 0 1 .522-1.382 3.235 3.235 0 0 0-1.581-3.652c-.082.25-.186.494-.319.723a.75.75 0 0 1-1.299-.75 2.252 2.252 0 0 0-.465-2.816 2.251 2.251 0 0 0-.9-.482Z" clipRule="evenodd"></path>
              </svg>
            </button>
            <button 
              className="chat-header-btn" 
              data-testid="btn-info"
              onClick={openContextInsightsModal}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="chat-header-btn-icon">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path>
                <path d="M2 12h20"></path>
              </svg>
            </button>
            <button 
              className="chat-header-btn chat-header-btn--relative" 
              data-testid="btn-cart"
              onClick={openBasket}
            >
              <ShoppingCart className="chat-header-btn-icon" />
              {totalItems > 0 && (
                <span className="chat-cart-badge">{totalItems}</span>
              )}
            </button>
            {customerName ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button 
                    className="chat-user-menu-btn" 
                    data-testid="btn-user"
                  >
                    <User className="chat-header-btn-icon" />
                    <span className="chat-user-menu-name">{customerName.split(' ')[0]}</span>
                    <ChevronDown className="chat-user-menu-chevron" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" side="bottom" sideOffset={8} className="w-48" container={chatModalRef.current || undefined}>
                  <div className="px-3 py-3 border-b">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                        <User className="w-4 h-4 text-gray-600" />
                      </div>
                      <span className="font-medium text-gray-800 text-sm">{customerName}</span>
                    </div>
                  </div>
                  <div className="py-1">
                    <DropdownMenuItem 
                      className="cursor-pointer px-3 py-2"
                      data-testid="menu-edit-profile"
                    >
                      <User className="w-4 h-4 mr-3 text-gray-500" />
                      <span>Edit Profile</span>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      onClick={handleLogout}
                      className="cursor-pointer px-3 py-2 text-red-600 focus:text-red-600"
                      data-testid="menu-logout"
                    >
                      <svg className="w-4 h-4 mr-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 3v9" />
                        <path d="M18.36 6.64A9 9 0 1 1 5.64 6.64" />
                      </svg>
                      <span>Logout</span>
                    </DropdownMenuItem>
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <button 
                className="chat-header-btn chat-login-link" 
                data-testid="btn-user"
                onClick={() => setShowLoginModal(true)}
                title="Login"
              >
                <svg 
                  className="chat-header-btn-icon" 
                  viewBox="0 0 24 24" 
                  fill="currentColor"
                >
                  <circle cx="8" cy="6" r="3.5" />
                  <path d="M1 21v-1c0-4 2.5-6 7-6s7 2 7 6v1H1z" />
                  <path d="M17 15h5m-2-2.5l2.5 2.5-2.5 2.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
              </button>
            )}
            <button onClick={handleClose} className="chat-close-btn" data-testid="btn-close-chat">
              <X className="chat-header-btn-icon" />
            </button>
          </div>
        </div>

        <div className="chat-main-content">
          <div className="chat-sidebar" data-testid="chat-sidebar">
            <button
              onClick={resetConversation}
              className="chat-new-btn"
              data-testid="button-reset"
            >
              <svg className="chat-new-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
              <span className="chat-new-btn-text">New Chat</span>
            </button>
            <h3 className="chat-sidebar-title">CONVERSATION PROGRESS</h3>
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

          <div className="chat-messages-container">
            <ScrollArea className="chat-messages-scroll" data-testid="chat-messages">
              <div className="chat-messages-list">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`chat-message-row ${message.role === "user" ? "chat-message-row--user" : ""}`}
                  >
                    {message.role === "assistant" && (
                      <div className="chat-assistant-avatar" data-testid="assistant-avatar">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="chat-assistant-avatar-icon">
                          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                          <circle cx="9" cy="7" r="4"></circle>
                          <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                          <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                        </svg>
                      </div>
                    )}
                    <div
                      className={`chat-message-content ${message.role === "user" ? "chat-message-content--user" : ""}`}
                    >
                      <div
                        className={`chat-bubble ${message.role === "user" ? "chat-bubble--user" : "chat-bubble--assistant"}`}
                        data-testid={`message-${message.role}-${index}`}
                      >
                        {message.role === "assistant" ? (
                          <div className="chat-prose">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <p className="chat-user-text">
                            {message.content}
                          </p>
                        )}
                      </div>
                      {message.timestamp && (
                        <span 
                          className={`chat-message-time ${message.role === "user" ? "chat-message-time--user" : ""}`}
                          data-testid={`message-time-${index}`}
                        >
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}

                      {message.products && message.products.length > 0 && (
                        <div className="chat-products-grid">
                          {message.products.slice(0, 6).map((product) => (
                            <ProductCard
                              key={product.id}
                              product={product}
                              onProductClick={openProductDetail}
                              shoppingMode={shoppingMode}
                            >
                              {shoppingMode === "instore" && (
                                <div className="px-3 pt-1 pb-1.5 flex items-center gap-1 text-xs text-gray-600">
                                  <svg className="w-3 h-3 text-red-500" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                  </svg>
                                  <span>Floor 1 •</span>
                                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                  <span className="text-green-600 font-medium">In Stock</span>
                                </div>
                              )}
                              
                              <div className="px-3 pb-3">
                                <div className="flex flex-wrap gap-1.5">
                                  <Button
                                    size="sm"
                                    className={`text-xs h-7 text-white border-0 rounded-[6px] px-2 min-w-0 ${
                                      shoppingMode === "instore" ? "flex-1 basis-[calc(50%-0.1875rem)]" : "flex-1"
                                    } ${
                                      isInCart(product.id)
                                        ? "bg-green-600 hover:bg-green-700"
                                        : "bg-[#0D6EFD] hover:bg-[#0B5ED7]"
                                    }`}
                                    onClick={() => addToCart(product)}
                                    data-testid={`button-add-cart-${product.id}`}
                                  >
                                    <ShoppingCart className="h-3 w-3 mr-0.5 shrink-0" />
                                    <span className="truncate">{isInCart(product.id) ? "Added" : "Cart"}</span>
                                  </Button>
                                  <Button
                                    size="sm"
                                    className={`text-xs h-7 text-white bg-[#C9A961] hover:bg-[#B89851] border-0 rounded-[6px] px-2 min-w-0 ${
                                      shoppingMode === "instore" ? "flex-1 basis-[calc(50%-0.1875rem)]" : "flex-1"
                                    }`}
                                    data-testid={`button-buy-now-${product.id}`}
                                  >
                                    <svg className="h-3 w-3 mr-0.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                                    </svg>
                                    <span className="truncate">Buy</span>
                                  </Button>
                                  {shoppingMode === "instore" && (
                                    <Button
                                      size="sm"
                                      className="w-full text-xs h-7 text-white bg-[#6B7280] hover:bg-[#4B5563] border-0 rounded-[6px] px-2"
                                      onClick={() => {
                                        setLocationProduct(product);
                                        setShowLocationModal(true);
                                      }}
                                      data-testid={`button-show-me-${product.id}`}
                                    >
                                      <svg className="h-3 w-3 mr-0.5 shrink-0" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                      </svg>
                                      <span>Show me</span>
                                    </Button>
                                  )}
                                </div>
                              </div>
                            </ProductCard>
                          ))}
                        </div>
                      )}

                      {message.role === "assistant" && message.suggestions && message.suggestions.length > 0 && index === messages.length - 1 && (
                        <div className="chat-suggestions" data-testid="chat-suggestions">
                          {message.suggestions.map((suggestion, suggestionIndex) => (
                            <button
                              key={suggestionIndex}
                              className="chat-suggestion-bubble"
                              onClick={() => handleSuggestionClick(suggestion)}
                              data-testid={`suggestion-${suggestionIndex}`}
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    {message.role === "user" && (
                      <div className="chat-user-avatar" id="user-message-avatar" data-testid="user-avatar">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="chat-user-avatar-icon" id="user-avatar-icon">
                          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                      </div>
                    )}
                  </div>
                ))}

                {chatMutation.isPending && (
                  <div className="chat-typing-row">
                    <div className="chat-assistant-avatar" data-testid="typing-avatar">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="chat-assistant-avatar-icon">
                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                      </svg>
                    </div>
                    <div className="chat-typing-bubble">
                      <div className="chat-typing-dots">
                        <span className="chat-typing-dot" />
                        <span className="chat-typing-dot" style={{ animationDelay: "0.1s" }} />
                        <span className="chat-typing-dot" style={{ animationDelay: "0.2s" }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="chat-input-area">
              {shoppingMode === "instore" && (
                <div className="chat-instore-actions">
                  <button
                    onClick={() => setShowScanProductModal(true)}
                    className="chat-scan-btn"
                    data-testid="btn-scan-product"
                  >
                    <QrCode className="chat-action-icon" />
                    <span>Scan Product</span>
                  </button>
                  <button
                    className="chat-help-btn"
                    data-testid="btn-get-help"
                  >
                    <Phone className="chat-action-icon" />
                    <span>Get Help</span>
                  </button>
                </div>
              )}
              <div className="chat-input-wrapper">
                <div className="chat-input-container">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        if (!input.trim()) {
                          toast({
                            description: "Enter what you're looking for to get started",
                            variant: "destructive",
                          });
                          return;
                        }
                        handleSend();
                      }
                    }}
                    placeholder="What are you looking for today?"
                    className="chat-input-field"
                    disabled={chatMutation.isPending}
                    data-testid="input-message"
                    rows={1}
                  />
                </div>
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || chatMutation.isPending}
                  size="icon"
                  className="chat-send-btn"
                  data-testid="button-send"
                >
                  <Send className="chat-send-icon" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
      {showLoginModal && (
        <div 
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowLoginModal(false);
          }}
        >
          <Card className="w-full max-w-md mx-4 shadow-2xl rounded-[5px]">
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
      {shouldRenderCustomer360 && customer360Data && (
        <div 
          className={`fixed inset-0 z-[60] flex items-center justify-end bg-black/50 transition-opacity duration-300 ${isCustomer360Animating ? 'opacity-100' : 'opacity-0'}`}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeCustomer360Modal();
          }}
          data-testid="customer360-modal-overlay"
        >
          <div className={`bg-white w-full sm:w-[380px] h-full shadow-2xl flex flex-col overflow-hidden transition-transform duration-300 ease-in-out ${isCustomer360Animating ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="bg-[#1565C0] text-white px-3 py-2 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="w-5 h-5 rounded-full border-2 border-white flex items-center justify-center">
                    <User className="w-3 h-3" />
                  </div>
                  <div className="absolute -bottom-0.5 -right-1.5 bg-white text-[#1565C0] text-[6px] font-bold px-0.5 rounded leading-tight">
                    360
                  </div>
                </div>
                <span className="font-semibold text-sm">Customer 360</span>
              </div>
              <button 
                onClick={closeCustomer360Modal}
                className="text-white hover:bg-white/10 p-1 rounded"
                data-testid="btn-close-customer360"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-5">
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Profile</h3>
                <div className="space-y-1 text-sm">
                  <p><span className="font-medium text-gray-600">Name:</span> {customer360Data.profile.name}</p>
                  <p><span className="font-medium text-gray-600">Age:</span> {customer360Data.profile.age}</p>
                  <p><span className="font-medium text-gray-600">Location:</span> {customer360Data.profile.location}</p>
                  <p><span className="font-medium text-gray-600">Tier:</span> {customer360Data.profile.tier}</p>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Sizes & Fit</h3>
                <div className="space-y-1 text-sm">
                  <p><span className="font-medium text-gray-600">Tops:</span> {customer360Data.sizes_fit.tops}</p>
                  <p><span className="font-medium text-gray-600">Bottoms:</span> {customer360Data.sizes_fit.bottoms}</p>
                  <p><span className="font-medium text-gray-600">Shoes:</span> {customer360Data.sizes_fit.shoes}</p>
                  <p><span className="font-medium text-gray-600">Height:</span> {customer360Data.sizes_fit.height}</p>
                  <p><span className="font-medium text-gray-600">Build:</span> {customer360Data.sizes_fit.build}</p>
                  <p><span className="font-medium text-gray-600">Skin:</span> {customer360Data.sizes_fit.skin}</p>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Style Preferences</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <p className="font-medium text-gray-600 mb-1">Preferred Colors:</p>
                    <div className="flex flex-wrap gap-1">
                      {customer360Data.style_preferences.preferred_colors.map((color, i) => (
                        <Badge key={i} variant="secondary" className="text-xs bg-gray-100">
                          {color}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <p><span className="font-medium text-gray-600">Style:</span> {customer360Data.style_preferences.style}</p>
                  <p><span className="font-medium text-gray-600">Budget:</span> {customer360Data.style_preferences.budget}</p>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Favorite Brands</h3>
                <div className="flex flex-wrap gap-1">
                  {customer360Data.favorite_brands.map((brand, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {brand}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {shouldRenderContextInsights && (
        <div 
          className={`fixed inset-0 z-[60] flex items-center justify-end bg-black/50 transition-opacity duration-300 ${isContextInsightsAnimating ? 'opacity-100' : 'opacity-0'}`}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeContextInsightsModal();
          }}
          data-testid="context-insights-modal-overlay"
        >
          <div className={`bg-white w-full sm:w-[380px] h-full shadow-2xl flex flex-col overflow-hidden transition-transform duration-300 ease-in-out ${isContextInsightsAnimating ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="bg-[#1565C0] text-white px-3 py-2 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path>
                  <path d="M2 12h20"></path>
                </svg>
                <span className="font-semibold text-sm">External Context</span>
              </div>
              <button 
                onClick={closeContextInsightsModal}
                className="text-white hover:bg-white/10 p-1 rounded"
                data-testid="btn-close-context-insights"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-5">
              {currentContext?.intent && (
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Understood Intent</h3>
                  <div className="flex flex-wrap gap-1">
                    {currentContext.intent.category && (
                      <Badge variant="secondary" className="text-xs">
                        {currentContext.intent.category}
                      </Badge>
                    )}
                    {currentContext.intent.occasion &&
                      !currentContext.intent.trip_segments?.length && (
                        <Badge variant="outline" className="text-xs">
                          {currentContext.intent.occasion}
                        </Badge>
                      )}
                    {currentContext.intent.style && (
                      <Badge variant="outline" className="text-xs">
                        {currentContext.intent.style}
                      </Badge>
                    )}
                  </div>
                </div>
              )}

              {currentContext?.intent?.trip_segments &&
                currentContext.intent.trip_segments.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <Calendar className="h-4 w-4" /> Trip Destinations
                      </h3>
                      <div className="space-y-2">
                        {currentContext.intent.trip_segments.map((segment, i) => (
                          <div key={i} className="bg-gray-50 rounded-lg p-3">
                            <p className="text-sm font-medium">{segment.destination}</p>
                            <p className="text-xs text-gray-500">
                              {segment.start_date} to {segment.end_date}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

              {isTravelIntent(currentContext) && currentContext?.environmental?.segments &&
                currentContext.environmental.segments.length > 0 ? (
                  <>
                    <Separator />
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <Cloud className="h-4 w-4" /> Weather by Destination
                      </h3>
                      <div className="space-y-2">
                        {currentContext.environmental.segments.map((seg, i) => (
                          <div key={i} className="bg-gray-50 rounded-lg p-3">
                            <p className="text-sm font-medium">{seg.destination}</p>
                            {seg.weather && (
                              <p className="text-xs text-gray-500">
                                {seg.weather.temperature}°C - {seg.weather.description}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : isTravelIntent(currentContext) && currentContext?.environmental?.weather ? (
                  <>
                    <Separator />
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <MapPin className="h-4 w-4" /> Destination
                      </h3>
                      <div className="bg-gray-50 rounded-lg p-3 mb-3">
                        <p className="text-sm font-medium">{currentContext.intent?.location || 'Travel destination'}</p>
                        {currentContext.intent?.travel_date && (
                          <p className="text-xs text-gray-500">
                            {currentContext.intent.travel_date}
                            {currentContext.intent?.trip_duration_days && currentContext.intent.trip_duration_days > 1 
                              ? ` (${currentContext.intent.trip_duration_days} days)` 
                              : ''}
                          </p>
                        )}
                      </div>
                      <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <Cloud className="h-4 w-4" /> Weather
                      </h3>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-sm font-medium">
                          {currentContext.environmental.weather.temperature}°C 
                          {currentContext.environmental.weather.high_temp && (
                            <span className="text-gray-500"> (High: {currentContext.environmental.weather.high_temp}°C)</span>
                          )}
                        </p>
                        <p className="text-xs text-gray-500">
                          {currentContext.environmental.weather.description}
                        </p>
                        {currentContext.environmental.weather.precipitation !== undefined && (
                          <p className="text-xs text-gray-500">
                            Precipitation: {currentContext.environmental.weather.precipitation}mm
                          </p>
                        )}
                      </div>
                    </div>
                  </>
                ) : null}

              {currentContext?.environmental?.trends &&
                currentContext.environmental.trends.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" /> Trending
                      </h3>
                      <div className="flex flex-wrap gap-1">
                        {currentContext.environmental.trends.slice(0, 5).map((trend, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {trend}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </>
                )}

              {!currentContext && (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Sparkles className="w-12 h-12 mb-4 opacity-30" />
                  <p className="text-sm">No context insights yet</p>
                  <p className="text-xs text-gray-400 mt-1">Start a conversation to see insights</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {shouldRenderAgentThinking && (
        <div 
          className={`fixed inset-0 z-[60] flex items-center justify-end bg-black/50 transition-opacity duration-300 ${isAgentThinkingAnimating ? 'opacity-100' : 'opacity-0'}`}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeAgentThinkingModal();
          }}
          data-testid="agent-thinking-modal-overlay"
        >
          <div className={`bg-white w-full sm:w-[420px] h-full shadow-2xl flex flex-col overflow-hidden transition-transform duration-300 ease-in-out ${isAgentThinkingAnimating ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="bg-[#1565C0] text-white px-3 py-2 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                  <path fillRule="evenodd" d="M14.269 1.322a3.751 3.751 0 0 1 4.456 3.25 4.753 4.753 0 0 1 3.022 4.62 4.757 4.757 0 0 1-.318 1.522 4.75 4.75 0 0 1-.537 7.055c-.047.036-.096.07-.144.104a4.752 4.752 0 0 1-4.44 4.863A4.753 4.753 0 0 1 12 20.555a4.752 4.752 0 0 1-7.667.459 4.75 4.75 0 0 1-1.082-3.14 4.751 4.751 0 0 1-.682-7.16 4.756 4.756 0 0 1 .079-3.62 4.75 4.75 0 0 1 2.626-2.52A3.752 3.752 0 0 1 12 2.751a3.748 3.748 0 0 1 2.269-1.43Zm-4.83 1.471a2.252 2.252 0 0 0-2.387 3.332.75.75 0 0 1-1.299.75 3.762 3.762 0 0 1-.32-.722 3.25 3.25 0 0 0-1.411 1.543 3.251 3.251 0 0 0-.171 2.108.748.748 0 0 1 .524 1.382A3.252 3.252 0 0 0 2.86 14.84 3.252 3.252 0 0 0 6 17.251a.75.75 0 0 1 0 1.5 4.75 4.75 0 0 1-1.194-.154 3.276 3.276 0 0 0 .685 1.464 3.251 3.251 0 0 0 5.76-2.062v-5.467a4.92 4.92 0 0 1-2.04 1.188.75.75 0 0 1-.42-1.44 3.421 3.421 0 0 0 2.447-3.004L11.25 9V5a2.252 2.252 0 0 0-1.81-2.207Zm6.143.034a2.252 2.252 0 0 0-1.952.388 2.25 2.25 0 0 0-.865 1.527L12.75 5v4l.01.276a3.42 3.42 0 0 0 2.45 3.005.75.75 0 0 1-.42 1.439 4.92 4.92 0 0 1-2.04-1.187V18a3.252 3.252 0 0 0 2.154 3.056 3.253 3.253 0 0 0 3.605-.994 3.251 3.251 0 0 0 .683-1.464A4.75 4.75 0 0 1 18 18.75a.75.75 0 0 1 0-1.5 3.251 3.251 0 0 0 1.625-6.064.747.747 0 0 1 .522-1.382 3.235 3.235 0 0 0-1.581-3.652c-.082.25-.186.494-.319.723a.75.75 0 0 1-1.299-.75 2.252 2.252 0 0 0-.465-2.816 2.251 2.251 0 0 0-.9-.482Z" clipRule="evenodd"></path>
                </svg>
                <span className="font-semibold text-sm">Agent Thinking Log</span>
              </div>
              <button 
                onClick={closeAgentThinkingModal}
                className="text-white hover:bg-white/10 p-1 rounded"
                data-testid="btn-close-agent-thinking"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4">
              {agentThinkingLogs.length > 0 ? (
                <div className="space-y-4">
                  {agentThinkingLogs.map((step, index) => {
                    const getPhaseId = (agent: string, idx: number) => {
                      const name = agent.toLowerCase();
                      if (name.includes('discovery')) return `#discovery-${idx + 1}`;
                      if (name.includes('planning')) return `#planning-${idx + 1}`;
                      if (name.includes('profile')) return `#profile-${idx + 1}`;
                      if (name.includes('context')) return `#context-${idx + 1}`;
                      if (name.includes('styling')) return `#styling-${idx + 1}`;
                      return `#message-${idx + 1}`;
                    };
                    const formatTime = (timestamp: string) => {
                      const date = new Date(timestamp);
                      return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit', hour12: true}).toUpperCase();
                    };
                    return (
                      <div key={index} className="border-b border-gray-100 pb-3 last:border-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-mono font-semibold text-blue-600">
                            Message {getPhaseId(step.agent, index)}
                          </span>
                          <span className="text-xs text-gray-400">-</span>
                          {step.timestamp && (
                            <span className="text-xs text-gray-500 font-mono">
                              {formatTime(step.timestamp)}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-700 leading-relaxed">{step.action}</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <span className="text-5xl mb-4 opacity-30">🧠</span>
                  <p className="text-sm">No activity yet</p>
                  <p className="text-xs text-gray-400 mt-1">Start a conversation to see what's happening behind the scenes</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {showScanProductModal && (
        <div 
          className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeScanModal();
          }}
          data-testid="scan-product-modal-overlay"
        >
          <div className="bg-white rounded-[6px] w-[90vw] sm:w-[360px] max-w-[360px] shadow-2xl overflow-hidden">
            <div className="p-4 h-[380px] flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <QrCode className="w-4 h-4 text-gray-600" />
                <h2 className="text-sm font-semibold text-gray-900">Scan Product QR Code</h2>
              </div>
              
              <div className="flex flex-col items-center flex-1 justify-center">
                {scanningState === "ready" && (
                  <>
                    <div className="w-24 h-24 border-2 border-gray-300 rounded-[6px] flex items-center justify-center mb-3 bg-gray-50">
                      <svg width="60" height="60" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="8" y="8" width="24" height="24" rx="2" fill="#666"/>
                        <rect x="48" y="8" width="24" height="24" rx="2" fill="#666"/>
                        <rect x="8" y="48" width="24" height="24" rx="2" fill="#666"/>
                        <rect x="14" y="14" width="12" height="12" fill="white"/>
                        <rect x="54" y="14" width="12" height="12" fill="white"/>
                        <rect x="14" y="54" width="12" height="12" fill="white"/>
                        <rect x="17" y="17" width="6" height="6" fill="#666"/>
                        <rect x="57" y="17" width="6" height="6" fill="#666"/>
                        <rect x="17" y="57" width="6" height="6" fill="#666"/>
                        <rect x="36" y="8" width="4" height="4" fill="#666"/>
                        <rect x="36" y="16" width="4" height="4" fill="#666"/>
                        <rect x="36" y="28" width="4" height="4" fill="#666"/>
                        <rect x="8" y="36" width="4" height="4" fill="#666"/>
                        <rect x="16" y="36" width="4" height="4" fill="#666"/>
                        <rect x="28" y="36" width="4" height="4" fill="#666"/>
                        <rect x="48" y="40" width="8" height="8" fill="#666"/>
                        <rect x="60" y="40" width="8" height="8" fill="#666"/>
                        <rect x="48" y="52" width="8" height="8" fill="#666"/>
                        <rect x="60" y="52" width="8" height="8" fill="#666"/>
                        <rect x="48" y="64" width="8" height="8" fill="#666"/>
                        <rect x="60" y="64" width="8" height="8" fill="#666"/>
                        <rect x="36" y="48" width="8" height="8" fill="#666"/>
                        <rect x="36" y="64" width="8" height="8" fill="#666"/>
                      </svg>
                    </div>
                    
                    <h3 className="text-sm font-semibold text-gray-900 mb-1">Ready to Scan</h3>
                    <p className="text-xs text-gray-500 text-center mb-3">
                      Find the QR code on any product tag and scan to get instant information
                    </p>
                    
                    <button
                      onClick={startScanning}
                      className="w-full h-9 flex items-center justify-center gap-2 text-sm text-white font-medium rounded-[6px] mb-2"
                      style={{ backgroundColor: '#C5A572' }}
                      data-testid="btn-start-scanning"
                    >
                      <Camera className="w-3.5 h-3.5" />
                      <span>Start Scanning</span>
                    </button>
                    
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleQrUpload}
                      className="hidden"
                      data-testid="input-qr-upload"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full h-9 flex items-center justify-center gap-2 text-sm text-gray-700 font-medium border border-gray-300 rounded-[6px] mb-2 hover:bg-gray-50"
                      data-testid="btn-upload-qr"
                    >
                      <Upload className="w-3.5 h-3.5" />
                      <span>Upload QR Image</span>
                    </button>
                  </>
                )}
                
                <div id="qr-upload-reader" className="hidden" />

                {scanningState === "scanning" && (
                  <>
                    <div id="qr-reader" className="w-full h-44 rounded-[6px] overflow-hidden mb-3" />
                    <p className="text-xs text-gray-500 text-center mb-3">
                      Point your camera at a product QR code
                    </p>
                  </>
                )}

                {scanningState === "loading" && (
                  <>
                    <div className="w-24 h-24 flex items-center justify-center mb-3">
                      <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" />
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-1">Loading Product...</h3>
                    <p className="text-xs text-gray-500 text-center mb-3">
                      Fetching product details
                    </p>
                  </>
                )}

                {scanningState === "not_found" && (
                  <>
                    <div className="w-24 h-24 flex items-center justify-center mb-3 bg-red-50 rounded-[6px]">
                      <X className="w-10 h-10 text-red-400" />
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-1">Product Not Found</h3>
                    <p className="text-xs text-gray-500 text-center mb-3">
                      {scannedProductId 
                        ? `No product found with ID: ${scannedProductId}` 
                        : "The scanned code doesn't contain valid product information"}
                    </p>
                    <button
                      onClick={() => setScanningState("ready")}
                      className="w-full h-9 flex items-center justify-center gap-2 text-sm text-white font-medium rounded-[6px] mb-2"
                      style={{ backgroundColor: '#C5A572' }}
                      data-testid="btn-try-again"
                    >
                      <Camera className="w-3.5 h-3.5" />
                      <span>Try Again</span>
                    </button>
                  </>
                )}
                
                <button
                  onClick={closeScanModal}
                  className="w-full h-9 flex items-center justify-center text-sm text-gray-700 font-medium border border-gray-300 rounded-[6px] hover:bg-gray-50"
                  data-testid="btn-cancel-scan"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {showLocationModal && locationProduct && (
        <div 
          className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowLocationModal(false);
          }}
          data-testid="location-modal-overlay"
        >
          <div className="bg-white rounded-[6px] w-[90vw] sm:w-[400px] max-w-[400px] shadow-2xl overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                </svg>
                <h2 className="text-sm font-semibold text-gray-900">Find {locationProduct.name}</h2>
              </div>
              
              <div className="bg-gray-50 rounded-[6px] p-3 mb-3">
                <h3 className="text-xs font-semibold text-gray-900 mb-2">Location Details</h3>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Floor:</span>
                    <span className="font-medium text-gray-900">1</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Zone:</span>
                    <span className="font-medium text-gray-900">{locationProduct.category || "General"}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Aisle:</span>
                    <span className="font-medium text-gray-900">1B</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">In Stock:</span>
                    <span className="font-medium text-green-600">Yes</span>
                  </div>
                </div>
              </div>

              <div className="bg-amber-50 rounded-[6px] p-3 mb-4">
                <div className="flex items-center gap-2 mb-0.5">
                  <svg className="w-3.5 h-3.5 text-amber-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  <span className="text-xs font-semibold text-gray-900">Estimated Walk Time</span>
                </div>
                <p className="text-xs text-gray-600">2-3 minutes from your current location</p>
              </div>

              <button
                onClick={() => {
                  setIsStartingNavigation(true);
                  setTimeout(() => {
                    toast({
                      title: "Navigation Started",
                      description: `Follow the in-store directions to find ${locationProduct.name}`,
                    });
                    setIsStartingNavigation(false);
                    setShowLocationModal(false);
                  }, 1500);
                }}
                disabled={isStartingNavigation}
                className={`w-full h-9 flex items-center justify-center gap-2 text-sm text-white font-medium rounded-[6px] mb-2 ${isStartingNavigation ? 'opacity-70 cursor-not-allowed' : ''}`}
                style={{ backgroundColor: '#C5A572' }}
                data-testid="btn-start-navigation"
              >
                <svg className={`w-3.5 h-3.5 ${isStartingNavigation ? 'animate-spin' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
                <span>{isStartingNavigation ? 'Starting Navigation...' : 'Start In-Store Navigation'}</span>
              </button>
              
              <button
                onClick={() => setShowLocationModal(false)}
                className="w-full h-9 flex items-center justify-center text-sm text-gray-700 font-medium border border-gray-300 rounded-[6px] hover:bg-gray-50"
                data-testid="btn-cancel-location"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
      <ProductDetailPanel
        product={selectedProduct}
        isOpen={shouldRenderProductDetail}
        isAnimating={isProductDetailAnimating}
        onClose={closeProductDetail}
        onAddToCart={addToCart}
        isInCart={isInCart}
      />
    </div>
  );
}
