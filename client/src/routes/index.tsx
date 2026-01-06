import { RouteObject } from "react-router-dom";
import LoginPage from "@/pages/login";
import ChatPage from "@/pages/chat";
import NotFound from "@/pages/not-found";
import ProtectedRoute from "@/components/ProtectedRoute";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <LoginPage />,
  },
  {
    path: "/chat",
    element: (
      <ProtectedRoute>
        <ChatPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "*",
    element: <NotFound />,
  },
];
