import { BrowserRouter, useRoutes } from "react-router-dom";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { routes } from "@/routes";

function AppRoutes() {
  const element = useRoutes(routes);
  return element;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col" style={{ fontFamily: 'Calibri, sans-serif' }}>
            <Header showAuthButtons={true} />
            <main className="flex-1">
              <AppRoutes />
            </main>
            <Footer />
          </div>
          <Toaster />
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
