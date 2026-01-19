import { RouteObject } from "react-router-dom";
import HomePage from "@/pages/home";
import LoginPage from "@/pages/login";
import ChatPage from "@/pages/chat";
import ProfilePage from "@/pages/profile";
import NotFound from "@/pages/not-found";
import ProtectedRoute from "@/components/ProtectedRoute";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/login",
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
    path: "/profile",
    element: (
      <ProtectedRoute>
        <ProfilePage />
      </ProtectedRoute>
    ),
  },
  {
    path: "*",
    element: <NotFound />,
  },
];
