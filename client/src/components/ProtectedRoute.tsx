import { useEffect, useState } from "react";
import { useLocation } from "wouter";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [, setLocation] = useLocation();

  useEffect(() => {
    const customerId = localStorage.getItem("customer_id");
    if (!customerId) {
      setLocation("/");
    } else {
      setIsAuthenticated(true);
    }
  }, [setLocation]);

  if (isAuthenticated === null) {
    return null;
  }

  return <>{children}</>;
}
