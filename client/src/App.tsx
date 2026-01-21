import { BrowserRouter, useRoutes, useLocation } from "react-router-dom";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { BasketProvider } from "@/components/Basket";
import { routes } from "@/routes";

function AppRoutes() {
  const element = useRoutes(routes);
  return element;
}

function AppContent() {
  const location = useLocation();
  const isHomePage = location.pathname === "/";

  if (isHomePage) {
    return (
      <div className="min-h-screen" style={{ fontFamily: 'Calibri, sans-serif' }}>
        <AppRoutes />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ fontFamily: 'Calibri, sans-serif' }}>
      <Header showAuthButtons={true} />
      <main className="flex-1">
        <AppRoutes />
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BasketProvider>
          <BrowserRouter>
            <AppContent />
            <Toaster />
          </BrowserRouter>
        </BasketProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
