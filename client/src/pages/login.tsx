import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { LogIn, Twitter, Facebook, Linkedin } from "lucide-react";

export default function LoginPage() {
  const [customerId, setCustomerId] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [, setLocation] = useLocation();
  const { toast } = useToast();

  useEffect(() => {
    const existingCustomer = localStorage.getItem("customer_name");
    if (existingCustomer) {
      setLocation("/chat");
    }
  }, [setLocation]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!customerId.trim() || !password.trim()) {
      toast({
        title: "Error",
        description: "Please enter both Customer ID and Password",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          customer_id: customerId.toUpperCase().trim(), 
          password: password 
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        localStorage.setItem("customer_id", data.customer.customer_id);
        localStorage.setItem("customer_name", `${data.customer.first_name} ${data.customer.last_name}`);
        toast({
          title: "Welcome!",
          description: `Logged in as ${data.customer.first_name} ${data.customer.last_name}`,
        });
        setLocation("/chat");
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
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-6 bg-gray-50" style={{ fontFamily: 'Calibri, sans-serif' }}>
        <div className="w-full max-w-4xl grid md:grid-cols-2 gap-0 shadow-xl rounded-lg overflow-hidden">
          <div 
            className="bg-gradient-to-br from-[#1565C0] to-[#0D47A1] text-white p-10 flex flex-col justify-center"
            data-testid="welcome-panel"
          >
            <h1 className="text-3xl font-bold mb-4" style={{ fontFamily: 'Calibri, sans-serif' }}>
              Welcome to PSA —
            </h1>
            <h2 className="text-2xl font-semibold mb-6" style={{ fontFamily: 'Calibri, sans-serif' }}>
              Your AI Shopping Assistant
            </h2>
            <p className="text-white/90 text-lg leading-relaxed" style={{ fontFamily: 'Calibri, sans-serif' }}>
              Find better items faster with personalized suggestions, smart price tracking and curated picks.
            </p>
          </div>
          
          <Card className="rounded-none border-0 shadow-none">
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-xl font-bold text-gray-800" data-testid="text-title" style={{ fontFamily: 'Calibri, sans-serif' }}>
                Welcome back
              </CardTitle>
              <CardDescription data-testid="text-description" style={{ fontFamily: 'Calibri, sans-serif' }}>
                Sign in with your Customer ID to get personalized recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="customerId" style={{ fontFamily: 'Calibri, sans-serif' }}>Customer ID/ User Name</Label>
                  <Input
                    id="customerId"
                    type="text"
                    placeholder="e.g., CUST-0000001"
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                    data-testid="input-customer-id"
                    disabled={isLoading}
                    className="h-11"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" style={{ fontFamily: 'Calibri, sans-serif' }}>Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    data-testid="input-password"
                    disabled={isLoading}
                    className="h-11 pt-[0px] pb-[0px]"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="remember" 
                      checked={rememberMe}
                      onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                      data-testid="checkbox-remember"
                    />
                    <Label htmlFor="remember" className="text-sm font-normal cursor-pointer" style={{ fontFamily: 'Calibri, sans-serif' }}>
                      Remember Me
                    </Label>
                  </div>
                  <a href="#" className="text-sm text-[#1565C0] hover:underline" data-testid="link-forgot-password" style={{ fontFamily: 'Calibri, sans-serif' }}>
                    Forgot Password?
                  </a>
                </div>
                
                <div className="pt-2">
                  <p className="text-center text-sm text-gray-500 mb-3" style={{ fontFamily: 'Calibri, sans-serif' }}>You can login with</p>
                  <div className="flex justify-center gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="rounded-full w-10 h-10 bg-[#1DA1F2] hover:bg-[#1a8cd8] border-0"
                      data-testid="button-social-twitter"
                    >
                      <Twitter className="w-5 h-5 text-white" />
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="rounded-full w-10 h-10 bg-[#1877F2] hover:bg-[#166fe5] border-0"
                      data-testid="button-social-facebook"
                    >
                      <Facebook className="w-5 h-5 text-white" />
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="rounded-full w-10 h-10 bg-[#EA4335] hover:bg-[#d33426] border-0"
                      data-testid="button-social-google"
                    >
                      <span className="text-white font-bold text-sm">G</span>
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="rounded-full w-10 h-10 bg-[#0A66C2] hover:bg-[#095196] border-0"
                      data-testid="button-social-linkedin"
                    >
                      <Linkedin className="w-5 h-5 text-white" />
                    </Button>
                  </div>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full h-11 bg-[#1565C0] hover:bg-[#0D47A1]" 
                  disabled={isLoading}
                  data-testid="button-login"
                >
                  <LogIn className="w-4 h-4 mr-2" />
                  {isLoading ? "Signing in..." : "Sign In"}
                </Button>
              </form>
              <p className="text-sm text-gray-500 text-center mt-4" data-testid="text-hint" style={{ fontFamily: 'Calibri, sans-serif' }}>
                Default password: password123
              </p>
            </CardContent>
          </Card>
        </div>
    </div>
  );
}
