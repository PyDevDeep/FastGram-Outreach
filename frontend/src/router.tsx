import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import DashboardPage from "@/pages/DashboardPage";
import LeadsPage from "@/pages/LeadsPage";
import ConfigPage from "@/pages/ConfigPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: "leads",
        element: <LeadsPage />,
      },
      {
        path: "config",
        element: <ConfigPage />,
      },
    ],
  },
]);
