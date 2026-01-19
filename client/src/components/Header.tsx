import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { UserPlus, User, LogOut, ChevronDown } from "lucide-react";
import Logo from "@/components/Logo";
import UpdateUserProfile from "@/components/UpdateUserProfile";

interface HeaderProps {
  onSignUp?: () => void;
  showAuthButtons?: boolean;
}

export default function Header({ onSignUp, showAuthButtons = true }: HeaderProps) {
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
    <>
    <header className="w-full bg-[#1565C0] text-white py-3 px-6 flex items-center justify-between" style={{ fontFamily: 'Calibri, sans-serif' }} data-testid="header">
      <div data-testid="header-logo">
        <Logo className="h-10" />
      </div>
      
      {showAuthButtons && (
        <div className="flex items-center gap-3">
          {customerName ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="text-white hover:bg-white/10 text-[14px] flex items-center gap-2"
                  data-testid="button-user-menu"
                >
                  <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <span>{customerName}</span>
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent 
                align="end" 
                className="w-56 mt-2"
                style={{ fontFamily: 'Calibri, sans-serif' }}
              >
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
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:bg-white/10 text-[14px]"
              onClick={onSignUp}
              data-testid="button-header-signup"
            >
              <UserPlus className="w-4 h-4 mr-0.5" />
              Sign up
            </Button>
          )}
        </div>
      )}
    </header>
    
    {customerId && (
      <UpdateUserProfile
        isOpen={showUpdateProfile}
        onClose={() => setShowUpdateProfile(false)}
        customerId={customerId}
        onUpdate={handleProfileUpdate}
      />
    )}
    </>
  );
}
