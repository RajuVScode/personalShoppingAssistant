import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { UserPlus, User, LogOut, ChevronDown } from "lucide-react";
import Logo from "@/components/Logo";
import "../styles/header.css";

interface HeaderProps {
  onSignUp?: () => void;
  showAuthButtons?: boolean;
}

export default function Header({ onSignUp, showAuthButtons = true }: HeaderProps) {
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
    <header className="header" id="header" data-testid="header">
      <div id="header-logo" data-testid="header-logo">
        <Logo className="header-logo" />
      </div>
      
      {showAuthButtons && (
        <div className="header-auth" id="header-auth">
          {customerName ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="header-user-menu-btn"
                  id="header-user-menu-btn"
                  data-testid="button-user-menu"
                >
                  <div className="header-user-avatar" id="header-user-avatar">
                    <User className="header-user-avatar-icon" />
                  </div>
                  <span className="header-user-name">{customerName}</span>
                  <ChevronDown className="header-chevron-icon" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent 
                align="end" 
                className="header-dropdown-content"
              >
                <div className="header-dropdown-profile">
                  <div className="header-dropdown-profile-inner">
                    <div className="header-dropdown-avatar">
                      <User className="header-dropdown-avatar-icon" />
                    </div>
                    <span className="header-dropdown-name">{customerName}</span>
                  </div>
                </div>
                <div className="header-dropdown-items">
                  <DropdownMenuItem asChild className="header-dropdown-item">
                    <a href="/profile" id="header-menu-edit-profile" data-testid="menu-edit-profile">
                      <User className="header-dropdown-item-icon" />
                      <span>Edit Profile</span>
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onSelect={handleLogout}
                    className="header-dropdown-item header-dropdown-logout"
                    id="header-menu-logout"
                    data-testid="menu-logout"
                  >
                    <LogOut className="header-dropdown-item-icon" />
                    <span>Logout</span>
                  </DropdownMenuItem>
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <button
              className="header-signup-btn"
              id="header-signup-btn"
              onClick={onSignUp}
              data-testid="button-header-signup"
            >
              <UserPlus className="header-signup-icon" />
              Sign up
            </button>
          )}
        </div>
      )}
    </header>
  );
}
