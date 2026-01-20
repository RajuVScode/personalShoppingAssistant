import { RouteObject } from "react-router-dom";
import HomePage from "@/pages/home";
import ProfilePage from "@/pages/profile";
import NotFound from "@/pages/not-found";
import ProtectedRoute from "@/components/ProtectedRoute";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <HomePage />,
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
