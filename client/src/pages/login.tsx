import { useState } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

export default function LoginPage() {
  const [customerId, setCustomerId] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [, setLocation] = useLocation();
  const { toast } = useToast();

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-800" data-testid="text-title">
            Personal Shopping Assistant
          </CardTitle>
          <CardDescription data-testid="text-description">
            Sign in with your Customer ID to get personalized recommendations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="customerId">Customer ID</Label>
              <Input
                id="customerId"
                type="text"
                placeholder="e.g., CUST-0000001"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                data-testid="input-customer-id"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                data-testid="input-password"
                disabled={isLoading}
              />
            </div>
            <Button 
              type="submit" 
              className="w-full" 
              disabled={isLoading}
              data-testid="button-login"
            >
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          <p className="text-sm text-gray-500 text-center mt-4" data-testid="text-hint">
            Default password: password123
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
