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
import UpdateUserProfile from "@/components/UpdateUserProfile";

export default function HomePage() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [customerName, setCustomerName] = useState<string | null>(null);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [showUpdateProfile, setShowUpdateProfile] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = () => {
      const name = localStorage.getItem("customer_name");
      const id = localStorage.getItem("customer_id");
      setCustomerName(name);
      setCustomerId(id);
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
    setCustomerId(null);
    navigate("/login");
  };

  const handleEditProfile = () => {
    setTimeout(() => {
      setShowUpdateProfile(true);
    }, 100);
  };

  const handleProfileUpdate = () => {
    const name = localStorage.getItem("customer_name");
    setCustomerName(name);
  };

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: 'Calibri, sans-serif' }}>
      <div className="bg-[#1a1a2e] text-white text-center py-2 text-sm" data-testid="promo-banner">
        LAST CALL® DESIGNER SALE: UP TO 70% OFF | FREE SHIPPING ON QUALIFYING ORDERS OF $300+
      </div>
      <header className="bg-white border-b" data-testid="main-header">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between py-4">
            <nav className="flex items-center gap-8" data-testid="main-nav">
              <a href="#" className="text-sm font-medium text-gray-800 hover:text-gray-600" data-testid="nav-women">WOMEN</a>
              <a href="#" className="text-sm font-medium text-gray-800 hover:text-gray-600" data-testid="nav-men">MEN</a>
              <a href="#" className="text-sm font-medium text-gray-800 hover:text-gray-600" data-testid="nav-shoes">SHOES</a>
              <a href="#" className="text-sm font-medium text-gray-800 hover:text-gray-600" data-testid="nav-handbags">HANDBAGS</a>
              <a href="#" className="text-sm font-medium text-gray-800 hover:text-gray-600" data-testid="nav-beauty">BEAUTY</a>
              <a href="#" className="text-sm font-medium text-gray-800 hover:text-gray-600" data-testid="nav-home">HOME</a>
            </nav>

            <div className="flex items-center gap-4" data-testid="header-icons">
              <button className="flex items-center gap-1 text-sm text-gray-700 hover:text-gray-900" data-testid="btn-dashboard">
                <BarChart3 className="w-4 h-4" />
                <span>DASHBOARD</span>
              </button>
              <button className="text-gray-700 hover:text-gray-900" data-testid="btn-search">
                <Search className="w-5 h-5" />
              </button>
              
              {customerName ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-1 text-gray-700 hover:text-gray-900" data-testid="btn-account">
                      <User className="w-5 h-5" />
                      <ChevronDown className="w-3 h-3" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56 mt-2">
                    <div className="px-3 py-3 border-b">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                          <User className="w-5 h-5 text-gray-600" />
                        </div>
                        <span className="font-medium text-gray-800">{customerName}</span>
                      </div>
                    </div>
                    <div className="py-1">
                      <DropdownMenuItem 
                        onClick={handleEditProfile}
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
                        <LogOut className="w-4 h-4 mr-3" />
                        <span>Logout</span>
                      </DropdownMenuItem>
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <button 
                  className="text-gray-700 hover:text-gray-900" 
                  data-testid="btn-account"
                  onClick={() => navigate("/login")}
                >
                  <User className="w-5 h-5" />
                </button>
              )}
              
              <button className="text-gray-700 hover:text-gray-900" data-testid="btn-wishlist">
                <Heart className="w-5 h-5" />
              </button>
              <button className="text-gray-700 hover:text-gray-900" data-testid="btn-cart">
                <ShoppingCart className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>
      <section className="relative" data-testid="hero-section">
        <div className="bg-gradient-to-r from-gray-300 via-gray-400 to-gray-500 py-32">
          <div className="absolute inset-0 flex items-start p-4">
            <span className="text-xs text-gray-600">Last Call Designer Sale</span>
          </div>
          <div className="max-w-7xl mx-auto px-4 text-center">
            <h1 className="text-5xl font-bold text-gray-800 mb-2" data-testid="hero-title">LAST CALL®</h1>
            <h2 className="text-4xl font-bold text-gray-800 mb-4">DESIGNER SALE</h2>
            <p className="text-lg text-gray-700 mb-8">Up to 70% off luxury favorites</p>
            <div className="flex items-center justify-center gap-4">
              <Button variant="outline" className="bg-white border-gray-800 text-gray-800 hover:bg-gray-100 px-8" data-testid="btn-shop-women">
                SHOP WOMEN
              </Button>
              <Button className="bg-gray-800 text-white hover:bg-gray-700 px-8" data-testid="btn-shop-men">
                SHOP MEN
              </Button>
            </div>
          </div>
        </div>
      </section>
      <section className="py-16 bg-[#fdf5f5]" data-testid="denim-section">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-start justify-between">
            <div className="max-w-md">
              <h3 className="text-3xl font-bold text-gray-900 mb-2" data-testid="denim-title">Denim Dreams</h3>
              <p className="text-gray-600 mb-6">Shop the latest in premium denim</p>
              <Button className="bg-[#1a1a2e] text-white hover:bg-[#2a2a4e] px-6" data-testid="btn-shop-denim">
                SHOP DENIM
              </Button>
            </div>
            <div className="text-center">
              <div className="w-48 h-48 bg-gray-200 rounded flex items-center justify-center text-gray-500 text-sm">
                Denim Collection
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="py-16" data-testid="featured-section">
        <div className="max-w-7xl mx-auto px-4">
          <h3 className="text-2xl font-bold text-gray-900 mb-8 text-center">Featured Categories</h3>
          <div className="grid grid-cols-4 gap-6">
            {["Dresses", "Handbags", "Shoes", "Accessories"].map((category) => (
              <div key={category} className="text-center" data-testid={`category-${category.toLowerCase()}`}>
                <div className="w-full aspect-square bg-gray-100 rounded-lg mb-4 flex items-center justify-center">
                  <span className="text-gray-500">{category}</span>
                </div>
                <h4 className="font-medium text-gray-800">{category}</h4>
                <p className="text-sm text-gray-500">Shop Now</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="py-16 bg-gray-50" data-testid="brands-section">
        <div className="max-w-7xl mx-auto px-4">
          <h3 className="text-2xl font-bold text-gray-900 mb-8 text-center">Shop by Brand</h3>
          <div className="grid grid-cols-6 gap-4">
            {["Gucci", "Prada", "Versace", "Dior", "Chanel", "Louis Vuitton"].map((brand) => (
              <div key={brand} className="bg-white p-4 rounded-lg text-center shadow-sm" data-testid={`brand-${brand.toLowerCase().replace(' ', '-')}`}>
                <span className="text-sm font-medium text-gray-700">{brand}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
      <button
        onClick={() => setIsChatOpen(true)}
        className="fixed bottom-8 right-8 bg-[#1a1a2e] text-white px-6 py-4 rounded-full shadow-lg hover:bg-[#2a2a3e] transition-all duration-300 z-50 flex items-center gap-2 group pl-[12px] pr-[12px] pt-[5px] pb-[5px]"
        data-testid="chat-widget-button"
      >
        <MessageCircle className="w-5 h-5 mr-2" />
        <span className="text-[14px] font-thin">Personal Shopping</span>
        <div className="absolute -top-2 -right-2 bg-[#c9a227] text-white text-xs rounded-full w-6 h-6 flex items-center justify-center animate-pulse">
          AI
        </div>
      </button>
      <ChatWidget isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
      
      {customerId && (
        <UpdateUserProfile
          isOpen={showUpdateProfile}
          onClose={() => setShowUpdateProfile(false)}
          customerId={customerId}
          onUpdate={handleProfileUpdate}
        />
      )}
    </div>
  );
}
