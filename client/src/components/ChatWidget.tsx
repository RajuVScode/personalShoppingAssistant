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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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

interface CartItemRowProps {
  item: CartItem;
  onUpdateQuantity: (productId: number, delta: number) => void;
  onRemove: (productId: number) => void;
}

const CartItemRow = memo(function CartItemRow({ item, onUpdateQuantity, onRemove }: CartItemRowProps) {
  return (
    <div className="p-4 hover:bg-gray-50" data-testid={`cart-item-${item.product.id}`}>
      <div className="flex gap-3 mb-3">
        {item.product.image_url && (
          <div className="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 shrink-0">
            <img
              src={item.product.image_url}
              alt={item.product.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.onerror = null;
                target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Crect fill='%23f3f4f6' width='64' height='64'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui' font-size='8' fill='%239ca3af'%3ENo image%3C/text%3E%3C/svg%3E";
              }}
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-gray-800 line-clamp-2">{item.product.name}</p>
          {item.product.brand && (
            <p className="text-xs text-gray-500 mt-0.5">{item.product.brand}</p>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center border rounded">
          <button
            onClick={() => onUpdateQuantity(item.product.id, -1)}
            className="w-7 h-7 flex items-center justify-center text-gray-600 hover:bg-gray-100 border-r text-sm"
            data-testid={`btn-decrease-${item.product.id}`}
          >
            −
          </button>
          <span className="w-8 h-7 flex items-center justify-center text-sm font-medium bg-gray-50">
            {item.quantity}
          </span>
          <button
            onClick={() => onUpdateQuantity(item.product.id, 1)}
            className="w-7 h-7 flex items-center justify-center text-gray-600 hover:bg-gray-100 border-l text-sm"
            data-testid={`btn-increase-${item.product.id}`}
          >
            +
          </button>
        </div>
        <span className="font-semibold text-base text-amber-600">
          ${((item.product.price || 0) * item.quantity).toFixed(2)}
        </span>
        <button
          onClick={() => onRemove(item.product.id)}
          className="text-red-500 hover:text-red-700 p-2"
          data-testid={`btn-remove-cart-${item.product.id}`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
});

interface ChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatWidget({ isOpen, onClose }: ChatWidgetProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [cartItems, setCartItems] = useState<Map<number, CartItem>>(new Map());
  const [showCartModal, setShowCartModal] = useState(false);
  const [isCartAnimating, setIsCartAnimating] = useState(false);
  const [shouldRenderCart, setShouldRenderCart] = useState(false);
  const [showCheckoutSheet, setShowCheckoutSheet] = useState(false);
  const [isCheckoutAnimating, setIsCheckoutAnimating] = useState(false);
  const [shouldRenderCheckout, setShouldRenderCheckout] = useState(false);
  const [input, setInput] = useState("");
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
  const [shoppingMode, setShoppingMode] = useState<"online" | "instore">("online");
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

  const addToCart = (product: Product) => {
    setCartItems((prev) => {
      const newMap = new Map(prev);
      if (newMap.has(product.id)) {
        newMap.delete(product.id);
      } else {
        newMap.set(product.id, { product, quantity: 1 });
      }
      return newMap;
    });
  };

  const removeFromCart = useCallback((productId: number) => {
    setCartItems((prev) => {
      const newMap = new Map(prev);
      newMap.delete(productId);
      return newMap;
    });
  }, []);

  const updateQuantity = useCallback((productId: number, delta: number) => {
    setCartItems((prev) => {
      const item = prev.get(productId);
      if (!item) return prev;
      const newQuantity = item.quantity + delta;
      if (newQuantity < 1) return prev;
      const newMap = new Map(prev);
      newMap.set(productId, { ...item, quantity: newQuantity });
      return newMap;
    });
  }, []);

  const cartItemsArray = useMemo(() => Array.from(cartItems.values()), [cartItems]);

  const totalItems = useMemo(() => 
    cartItemsArray.reduce((sum, item) => sum + item.quantity, 0),
    [cartItemsArray]
  );

  const totalPrice = useMemo(() => 
    cartItemsArray.reduce((sum, item) => sum + (item.product.price || 0) * item.quantity, 0),
    [cartItemsArray]
  );

  const openCartModal = () => {
    setShowCartModal(true);
    setShouldRenderCart(true);
    setTimeout(() => {
      setIsCartAnimating(true);
    }, 50);
  };

  const closeCartModal = () => {
    setIsCartAnimating(false);
    setIsCheckoutAnimating(false);
    setTimeout(() => {
      setShouldRenderCart(false);
      setShowCartModal(false);
      setShouldRenderCheckout(false);
      setShowCheckoutSheet(false);
    }, 300);
  };

  const openCheckoutSheet = () => {
    setShowCheckoutSheet(true);
    setShouldRenderCheckout(true);
    setTimeout(() => {
      setIsCheckoutAnimating(true);
    }, 50);
  };

  const closeCheckoutSheet = () => {
    setIsCheckoutAnimating(false);
    setTimeout(() => {
      setShouldRenderCheckout(false);
      setShowCheckoutSheet(false);
    }, 300);
  };

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
      className={`fixed inset-0 z-50 flex items-center justify-end pr-[1%] bg-black/50 transition-opacity duration-500 ${isAnimating ? 'opacity-100' : 'opacity-0'}`} 
      data-testid="chat-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div 
        ref={chatModalRef}
        className={`bg-white w-[97vw] h-[95vh] rounded-[5px] shadow-2xl flex flex-col overflow-hidden transition-transform duration-500 ease-in-out ${isAnimating ? 'translate-x-0' : 'translate-x-[105%]'}`} 
        data-testid="chat-modal"
      >
        <div className="bg-[#1565C0] text-white px-4 py-1.5 flex items-center justify-between rounded-t-[5px]" data-testid="chat-header">
          <div className="flex items-center gap-3">
            <Logo className="h-10" />
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setShoppingMode(shoppingMode === "online" ? "instore" : "online")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-[6px] text-sm font-medium transition-all ${
                shoppingMode === "online" 
                  ? "bg-green-500 text-white" 
                  : "bg-[#C9A961] text-white"
              }`}
              data-testid="toggle-shopping-mode"
            >
              {shoppingMode === "online" ? (
                <>
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                  <span>Online</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                    <polyline points="9 22 9 12 15 12 15 22" />
                  </svg>
                  <span>In-Store</span>
                </>
              )}
            </button>
            <button 
              className="hover:bg-white/10 p-1 rounded" 
              data-testid="btn-globe"
              onClick={() => {
                if (customerId && customer360Data) {
                  setShowCustomer360Modal(true);
                } else if (!customerId) {
                  toast({
                    title: "Login Required",
                    description: "Please login to view your profile",
                  });
                }
              }}
            >
              <div className="relative">
                <div className="w-5 h-5 rounded-full border-[1.5px] border-white flex items-center justify-center">
                  <User className="w-3 h-3" />
                </div>
                <div className="absolute -bottom-0.5 -right-1 bg-white text-[#1565C0] text-[5px] font-bold px-0.5 rounded leading-tight">
                  360
                </div>
              </div>
            </button>
            <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-settings">
              <Settings className="w-5 h-5" />
            </button>
            <button className="hover:bg-white/10 p-1 rounded" data-testid="btn-info">
              <Info className="w-5 h-5" />
            </button>
            <button 
              className="hover:bg-white/10 p-1 rounded relative" 
              data-testid="btn-cart"
              onClick={openCartModal}
            >
              <ShoppingCart className="w-5 h-5" />
              {totalItems > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center font-medium">
                  {totalItems}
                </span>
              )}
            </button>
            {customerName ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button 
                    className="hover:bg-white/10 p-1 rounded flex items-center gap-1" 
                    data-testid="btn-user"
                  >
                    <User className="w-5 h-5" />
                    <span className="text-xs max-w-[80px] truncate">{customerName.split(' ')[0]}</span>
                    <ChevronDown className="w-3 h-3" />
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
                className="hover:bg-white/10 p-1 rounded flex items-center gap-1" 
                data-testid="btn-user"
                onClick={() => setShowLoginModal(true)}
                title="Login"
              >
                <svg 
                  className="w-5 h-5" 
                  viewBox="0 0 24 24" 
                  fill="currentColor"
                >
                  <circle cx="8" cy="6" r="3.5" />
                  <path d="M1 21v-1c0-4 2.5-6 7-6s7 2 7 6v1H1z" />
                  <path d="M17 15h5m-2-2.5l2.5 2.5-2.5 2.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
              </button>
            )}
            <button onClick={handleClose} className="hover:bg-white/10 p-1 rounded" data-testid="btn-close-chat">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-48 bg-gray-100 p-4 border-r" data-testid="chat-sidebar">
            <button
              onClick={resetConversation}
              className="flex items-center gap-2 w-full px-3 py-1.5 mb-4 text-gray-700 bg-white hover:bg-blue-50 hover:border-blue-300 hover:shadow-md rounded-[6px] border border-gray-300 transition-all"
              data-testid="button-reset"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
              <span className="text-sm font-medium">New Chat</span>
            </button>
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
                      className={`max-w-[95%] ${message.role === "user" ? "order-first max-w-[80%]" : ""}`}
                    >
                      <div
                        className={`px-4 ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground ml-auto"
                            : "bg-muted rounded-2xl py-3"
                        }`}
                        style={message.role === "user" ? { borderRadius: "10px", paddingTop: "3px", paddingBottom: "3px" } : undefined}
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
                        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
                          {message.products.slice(0, 6).map((product) => (
                            <Card
                              key={product.id}
                              className="overflow-hidden hover:shadow-lg transition-shadow flex flex-col"
                              data-testid={`card-product-${product.id}`}
                            >
                              <div className="flex flex-row">
                                {product.image_url && (
                                  <div className="w-28 h-28 shrink-0 bg-muted overflow-hidden">
                                    <img
                                      src={product.image_url}
                                      alt={product.name}
                                      className="w-full h-full object-cover"
                                      onError={(e) => {
                                        const target = e.target as HTMLImageElement;
                                        target.onerror = null;
                                        target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Crect fill='%23f3f4f6' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui' font-size='14' fill='%239ca3af'%3EImage unavailable%3C/text%3E%3C/svg%3E";
                                      }}
                                    />
                                  </div>
                                )}
                                <div className="p-3 flex flex-col flex-1">
                                  <p className="font-medium text-sm line-clamp-1">
                                    {product.name}
                                  </p>
                                  <span className="text-xs text-muted-foreground mt-1">
                                    {product.brand}
                                  </span>
                                  <div className="flex items-center gap-2 mt-1">
                                    {product.price && (
                                      <span className="font-semibold text-sm">
                                        ${product.price}
                                      </span>
                                    )}
                                    {product.rating && (
                                      <div className="flex items-center gap-1">
                                        <span className="text-yellow-500 text-xs">
                                          ★
                                        </span>
                                        <span className="text-xs text-muted-foreground">
                                          {product.rating}
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                  
                                  {shoppingMode === "instore" && (
                                    <div className="flex items-center gap-1 mt-2 text-xs text-gray-600">
                                      <svg className="w-3 h-3 text-red-500" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                      </svg>
                                      <span>Floor 1, Travel Goods •</span>
                                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                      <span className="text-green-600 font-medium">In Stock</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                              <div className="px-3 pb-3 pt-2">
                                {shoppingMode === "online" ? (
                                  <Button
                                    size="sm"
                                    className="text-xs h-7 text-white px-4 rounded-[6px]"
                                    style={{
                                      backgroundColor: cartItems.has(product.id)
                                        ? "rgb(22 163 74)"
                                        : "rgb(13, 110, 253)"
                                    }}
                                    onClick={() => addToCart(product)}
                                    data-testid={`button-add-cart-${product.id}`}
                                  >
                                    {cartItems.has(product.id) ? (
                                      <>
                                        <Check className="h-3 w-3 mr-1" />
                                        Added to Cart
                                      </>
                                    ) : (
                                      <>
                                        <ShoppingCart className="h-3 w-3 mr-1" />
                                        Add to Cart
                                      </>
                                    )}
                                  </Button>
                                ) : (
                                  <div className="flex gap-2">
                                    <Button
                                      size="sm"
                                      className="flex-1 text-xs h-7 text-white bg-[#3D4F5F] hover:bg-[#2D3F4F] border-0 rounded-[6px]"
                                      data-testid={`button-show-me-${product.id}`}
                                    >
                                      <svg className="h-3 w-3 mr-1" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                      </svg>
                                      Show Me
                                    </Button>
                                    <Button
                                      size="sm"
                                      className="flex-1 text-xs h-7 text-white bg-[#C9A961] hover:bg-[#B89851] border-0 rounded-[6px]"
                                      data-testid={`button-try-on-${product.id}`}
                                    >
                                      <svg className="h-3 w-3 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="12" cy="12" r="10" />
                                        <circle cx="12" cy="12" r="3" />
                                      </svg>
                                      Try On
                                    </Button>
                                    <Button
                                      size="sm"
                                      className={`flex-1 text-xs h-7 text-white border-0 rounded-[6px] ${
                                        cartItems.has(product.id)
                                          ? "bg-green-600 hover:bg-green-700"
                                          : "bg-[#0D6EFD] hover:bg-[#0B5ED7]"
                                      }`}
                                      onClick={() => addToCart(product)}
                                      data-testid={`button-basket-${product.id}`}
                                    >
                                      <ShoppingCart className="h-3 w-3 mr-1" />
                                      {cartItems.has(product.id) ? "Added" : "Basket"}
                                    </Button>
                                  </div>
                                )}
                              </div>
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
              <div className="relative flex items-center gap-3 bg-muted/30 border border-muted-foreground/10 p-3 pl-[5px] pr-[5px] pt-[0px] pb-[0px]" style={{ borderRadius: '12px' }}>
                <div className="flex-1">
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
                  className="rounded-full h-7 w-7 shrink-0 disabled:opacity-100 disabled:pointer-events-auto"
                  style={{ 
                    backgroundColor: '#0d6efd',
                    cursor: (!input.trim() || chatMutation.isPending) ? 'not-allowed' : 'pointer'
                  }}
                  data-testid="button-send"
                >
                  <Send className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>

          {currentContext && (
            <div className="w-56 border-l p-3 hidden lg:block overflow-y-auto">
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
      {shouldRenderCart && (
        <div 
          className={`fixed inset-0 z-[60] flex items-center justify-end bg-black/50 transition-opacity duration-300 ${isCartAnimating ? 'opacity-100' : 'opacity-0'}`}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeCartModal();
          }}
          data-testid="cart-modal-overlay"
        >
          <div 
            className={`bg-white w-[400px] h-full shadow-2xl flex flex-col relative transition-transform duration-300 ease-in-out ${isCartAnimating ? 'translate-x-0' : 'translate-x-full'}`}
          >
            <div className="bg-[#1565C0] text-white px-4 py-3 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <ShoppingCart className="w-5 h-5" />
                <span className="font-bold text-lg">Shopping Cart</span>
                <span className="bg-white/20 text-white text-xs rounded-full px-2 py-0.5">
                  {totalItems} items
                </span>
              </div>
              <button 
                onClick={closeCartModal}
                className="text-white hover:bg-white/10 p-1 rounded"
                data-testid="btn-close-cart"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {cartItems.size === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <ShoppingCart className="w-16 h-16 mb-4 opacity-30" />
                  <p className="text-base">Your cart is empty</p>
                  <p className="text-sm text-gray-400 mt-1">Add products from recommendations</p>
                </div>
              ) : (
                <div className="divide-y">
                  {cartItemsArray.map((item) => (
                    <CartItemRow
                      key={item.product.id}
                      item={item}
                      onUpdateQuantity={updateQuantity}
                      onRemove={removeFromCart}
                    />
                  ))}
                </div>
              )}
            </div>
            {cartItems.size > 0 && (
              <div className="border-t p-4 bg-gray-50">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Total Items:</span>
                  <span className="text-sm font-medium text-gray-800">{totalItems}</span>
                </div>
                <div className="flex justify-between items-center mb-4">
                  <span className="text-base font-medium text-gray-800">Total</span>
                  <span className="font-bold text-xl text-gray-800">
                    ${totalPrice.toFixed(2)}
                  </span>
                </div>
                <Button 
                  className="w-full bg-[#1565C0] hover:bg-[#0D47A1] text-white h-9 flex items-center justify-center gap-2 text-sm"
                  data-testid="btn-checkout"
                  onClick={openCheckoutSheet}
                >
                  <ShoppingBag className="w-4 h-4" />
                  Proceed to Checkout
                </Button>
              </div>
            )}

            {shouldRenderCheckout && (
              <div 
                className={`absolute bottom-0 left-0 right-0 bg-white border-t shadow-lg transition-transform duration-300 ease-in-out ${isCheckoutAnimating ? 'translate-y-0' : 'translate-y-full'}`}
                data-testid="checkout-sheet"
              >
                <div className="p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-bold text-lg text-gray-800">Flexible Fulfillment Options</h3>
                    <button
                      onClick={closeCheckoutSheet}
                      className="text-gray-400 hover:text-gray-600 p-1"
                      data-testid="btn-toggle-checkout"
                    >
                      <ChevronDown className="w-5 h-5" />
                    </button>
                  </div>
                  
                  <p className="text-sm text-gray-500 mb-4 bg-gray-50 p-3 rounded-lg border-l-4 border-[#1565C0]">
                    Select items above to customize your order, or choose an option below:
                  </p>

                  <div className="space-y-2">
                    <button
                      className="w-full flex items-center justify-between py-2 px-3 bg-[#1565C0] text-white rounded-lg hover:bg-[#0D47A1] hover:shadow-md transition-all duration-200"
                      data-testid="btn-place-order"
                    >
                      <div className="flex items-center gap-2">
                        <Package className="w-4 h-4" />
                        <span className="font-medium text-sm">Place Order</span>
                      </div>
                      <span className="text-xs opacity-80">Select items first</span>
                    </button>

                    <button
                      className="w-full flex items-center justify-between py-2 px-3 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-[#1565C0] hover:shadow-md transition-all duration-200"
                      data-testid="btn-click-collect"
                    >
                      <div className="flex items-center gap-2">
                        <Store className="w-4 h-4 text-gray-600" />
                        <span className="font-medium text-sm text-gray-800">Click & Collect</span>
                      </div>
                      <span className="text-xs text-gray-500">All items to store</span>
                    </button>

                    <button
                      className="w-full flex items-center justify-between py-2 px-3 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-[#1565C0] hover:shadow-md transition-all duration-200"
                      data-testid="btn-book-session"
                    >
                      <div className="flex items-center gap-2">
                        <CalendarDays className="w-4 h-4 text-gray-600" />
                        <span className="font-medium text-sm text-gray-800">Book Style Session</span>
                      </div>
                      <span className="text-xs text-gray-500">Meet with stylist</span>
                    </button>
                  </div>

                  <button
                    onClick={closeCheckoutSheet}
                    className="w-full mt-3 py-1 text-gray-500 hover:text-gray-700 text-sm font-medium"
                    data-testid="btn-cancel-checkout"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
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
      {showCustomer360Modal && customer360Data && (
        <div 
          className="fixed inset-0 z-[60] flex items-center justify-end bg-black/50"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowCustomer360Modal(false);
          }}
          data-testid="customer360-modal-overlay"
        >
          <div className="bg-white w-[380px] h-full shadow-2xl flex flex-col overflow-hidden">
            <div className="bg-[#1565C0] text-white px-4 py-3 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center">
                    <User className="w-3.5 h-3.5" />
                  </div>
                  <div className="absolute -bottom-0.5 -right-1.5 bg-white text-[#1565C0] text-[7px] font-bold px-0.5 rounded leading-tight">
                    360
                  </div>
                </div>
                <span className="font-bold text-lg">Customer 360</span>
              </div>
              <button 
                onClick={() => setShowCustomer360Modal(false)}
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
    </div>
  );
}
