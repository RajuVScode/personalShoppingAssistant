import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Heart, ShoppingCart, BarChart3, User, MessageCircle, LogOut, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import ChatWidget from "@/components/ChatWidget";
import "@/styles/home.css";

export default function HomePage() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [customerName, setCustomerName] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = () => {
      const name = localStorage.getItem("customer_name");
      setCustomerName(name);
    };
    
    checkAuth();
    window.addEventListener("storage", checkAuth);
    const interval = setInterval(checkAuth, 500);
    
    return () => {
      window.removeEventListener("storage", checkAuth);
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("customer_id");
    localStorage.removeItem("customer_name");
    setCustomerName(null);
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: 'Calibri, sans-serif' }}>
      {/* Promo Banner */}
      <div id="promo-banner" data-testid="promo-banner">
        LAST CALL® DESIGNER SALE: UP TO 70% OFF | FREE SHIPPING ON QUALIFYING ORDERS OF $300+
      </div>

      {/* Header */}
      <header id="main-header" data-testid="main-header">
        <div className="header-container">
          <div className="header-content">
            <nav id="main-nav" data-testid="main-nav">
              <a href="#" className="nav-link" data-testid="nav-women">WOMEN</a>
              <a href="#" className="nav-link" data-testid="nav-men">MEN</a>
              <a href="#" className="nav-link" data-testid="nav-shoes">SHOES</a>
              <a href="#" className="nav-link" data-testid="nav-handbags">HANDBAGS</a>
              <a href="#" className="nav-link" data-testid="nav-beauty">BEAUTY</a>
              <a href="#" className="nav-link" data-testid="nav-home">HOME</a>
            </nav>

            <div id="header-icons" data-testid="header-icons">
              <button className="header-icon-btn" data-testid="btn-dashboard">
                <BarChart3 className="w-4 h-4" />
                <span>DASHBOARD</span>
              </button>
              <button className="header-icon-btn" data-testid="btn-search">
                <Search className="w-5 h-5" />
              </button>
              
              {customerName ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="header-icon-btn" data-testid="btn-account">
                      <User className="w-5 h-5" />
                      <ChevronDown className="w-3 h-3" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56 mt-2">
                    <div className="user-dropdown-header">
                      <div className="user-dropdown-avatar-wrapper">
                        <div className="user-dropdown-avatar">
                          <User className="w-5 h-5" />
                        </div>
                        <span className="user-dropdown-name">{customerName}</span>
                      </div>
                    </div>
                    <div className="user-dropdown-menu">
                      <DropdownMenuItem asChild className="user-dropdown-item cursor-pointer">
                        <a href="/profile" data-testid="menu-edit-profile">
                          <User className="w-4 h-4" />
                          <span>Edit Profile</span>
                        </a>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onSelect={handleLogout}
                        className="user-dropdown-item user-dropdown-item--logout cursor-pointer"
                        data-testid="menu-logout"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Logout</span>
                      </DropdownMenuItem>
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <button 
                  className="header-icon-btn" 
                  data-testid="btn-account"
                  onClick={() => setIsChatOpen(true)}
                >
                  <User className="w-5 h-5" />
                </button>
              )}
              
              <button className="header-icon-btn" data-testid="btn-wishlist">
                <Heart className="w-5 h-5" />
              </button>
              <button className="header-icon-btn" data-testid="btn-cart">
                <ShoppingCart className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section id="hero-section" data-testid="hero-section">
        <div className="hero-background">
          <div className="hero-label">
            <span className="hero-label-text">Last Call Designer Sale</span>
          </div>
          <div className="hero-content">
            <h1 id="hero-title" data-testid="hero-title">LAST CALL®</h1>
            <h2 className="hero-subtitle">DESIGNER SALE</h2>
            <p className="hero-description">Up to 70% off luxury favorites</p>
            <div className="hero-buttons">
              <Button variant="outline" className="hero-btn hero-btn--outline" data-testid="btn-shop-women">
                SHOP WOMEN
              </Button>
              <Button className="hero-btn hero-btn--solid" data-testid="btn-shop-men">
                SHOP MEN
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Denim Section */}
      <section id="denim-section" data-testid="denim-section">
        <div className="denim-container">
          <div className="denim-content">
            <div className="denim-text">
              <h3 id="denim-title" data-testid="denim-title">Denim Dreams</h3>
              <p className="denim-description">Shop the latest in premium denim</p>
              <Button className="denim-btn" data-testid="btn-shop-denim">
                SHOP DENIM
              </Button>
            </div>
            <div className="denim-image-placeholder">
              Denim Collection
            </div>
          </div>
        </div>
      </section>

      {/* Featured Categories */}
      <section id="featured-section" data-testid="featured-section">
        <div className="featured-container">
          <h3 className="featured-title">Featured Categories</h3>
          <div className="category-grid">
            {["Dresses", "Handbags", "Shoes", "Accessories"].map((category) => (
              <div key={category} className="category-card" data-testid={`category-${category.toLowerCase()}`}>
                <div className="category-image-placeholder">
                  <span>{category}</span>
                </div>
                <h4 className="category-name">{category}</h4>
                <p className="category-cta">Shop Now</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Brands Section */}
      <section id="brands-section" data-testid="brands-section">
        <div className="brands-container">
          <h3 className="brands-title">Shop by Brand</h3>
          <div className="brands-grid">
            {["Gucci", "Prada", "Versace", "Dior", "Chanel", "Louis Vuitton"].map((brand) => (
              <div key={brand} className="brand-card" data-testid={`brand-${brand.toLowerCase().replace(' ', '-')}`}>
                <span className="brand-name">{brand}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Chat Widget Trigger */}
      <button
        id="chat-widget-trigger"
        onClick={() => setIsChatOpen(true)}
        data-testid="chat-widget-button"
      >
        <MessageCircle className="w-5 h-5 chat-trigger-icon" />
        <span className="chat-trigger-text">Personal Shopping</span>
        <div className="chat-trigger-badge">
          AI
        </div>
      </button>

      <ChatWidget isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
