import { Button } from "@/components/ui/button";
import { UserPlus } from "lucide-react";
import Logo from "@/components/Logo";

interface HeaderProps {
  onSignUp?: () => void;
  showAuthButtons?: boolean;
}

export default function Header({ onSignUp, showAuthButtons = true }: HeaderProps) {
  return (
    <header className="w-full bg-[#1565C0] text-white py-3 px-6 flex items-center justify-between" style={{ fontFamily: 'Calibri, sans-serif' }} data-testid="header">
      <div data-testid="header-logo">
        <Logo className="h-10" />
      </div>
      
      {showAuthButtons && (
        <div className="flex items-center gap-3">
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
        </div>
      )}
    </header>
  );
}
