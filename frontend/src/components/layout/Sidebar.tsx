import { NavLink } from "react-router-dom";
import { LayoutDashboard, Users, Settings } from "lucide-react";
import { useUIStore } from "@/store/uiStore";

export function Sidebar() {
  const { activeTab, setActiveTab } = useUIStore();

  const navItems = [
    {
      path: "/",
      label: "Дашборд",
      icon: <LayoutDashboard className="w-5 h-5" />,
    },
    { path: "/leads", label: "Ліди", icon: <Users className="w-5 h-5" /> },
    {
      path: "/config",
      label: "Налаштування",
      icon: <Settings className="w-5 h-5" />,
    },
  ];

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col h-full flex-shrink-0">
      <div className="p-6 font-bold text-xl tracking-tight text-primary">
        FastGram
      </div>
      <nav className="flex-1 px-4 flex flex-col gap-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={() => setActiveTab(item.path)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                isActive || activeTab === item.path
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
