import { Button } from "@/components/ui/button";
import { UserPlus } from "lucide-react";

interface HeaderProps {
  onSignUp?: () => void;
  showAuthButtons?: boolean;
}

export default function Header({ onSignUp, showAuthButtons = true }: HeaderProps) {
  return (
    <header className="w-full bg-[#1565C0] text-white py-3 px-6 flex items-center justify-between" style={{ fontFamily: 'Calibri, sans-serif' }} data-testid="header">
      <div className="flex items-center gap-3" data-testid="header-logo">
        <div className="relative bg-white/20 rounded-lg w-10 h-10 flex items-center justify-center">
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-1.5 h-2 bg-white rounded-full"></div>
          <div className="flex gap-2">
            <div className="w-2 h-2 bg-white rounded-full"></div>
            <div className="w-2 h-2 bg-white rounded-full"></div>
          </div>
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-lg leading-tight">PSA</span>
          <span className="text-xs opacity-90 leading-tight">AI Shopping Assistant</span>
        </div>
      </div>
      
      {showAuthButtons && (
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/10"
            onClick={onSignUp}
            data-testid="button-header-signup"
          >
            <UserPlus className="w-4 h-4 mr-0.5" />
            Sign up
          </Button>
        </div>
      )}
    </header>
  );
}
