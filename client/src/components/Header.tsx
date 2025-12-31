import { Button } from "@/components/ui/button";
import { UserPlus, LogIn } from "lucide-react";

interface HeaderProps {
  onSignIn?: () => void;
  onSignUp?: () => void;
  showAuthButtons?: boolean;
}

export default function Header({ onSignIn, onSignUp, showAuthButtons = true }: HeaderProps) {
  return (
    <header className="w-full bg-[#1565C0] text-white py-3 px-6 flex items-center justify-between" style={{ fontFamily: 'Calibri, sans-serif' }} data-testid="header">
      <div className="flex items-center gap-2">
        <div className="bg-white text-[#1565C0] font-bold px-2 py-1 rounded text-sm" data-testid="header-logo">
          PSA
        </div>
        <span className="text-xs opacity-90">AI Shopping Assistant</span>
      </div>
      
      {showAuthButtons && (
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/10"
            onClick={onSignIn}
            data-testid="button-header-signin"
          >
            <LogIn className="w-4 h-4 mr-1" />
            Sign in
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/10"
            onClick={onSignUp}
            data-testid="button-header-signup"
          >
            <UserPlus className="w-4 h-4 mr-1" />
            Sign up
          </Button>
        </div>
      )}
    </header>
  );
}
