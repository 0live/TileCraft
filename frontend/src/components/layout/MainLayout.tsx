import { cn } from '@/lib/utils';
import { Box, Map, UploadCloud } from 'lucide-react';
import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

interface SidebarNavProps extends React.HTMLAttributes<HTMLElement> {
  items: {
    href: string;
    title: string;
    icon: React.ReactNode;
  }[];
}

function SidebarNav({ className, items, ...props }: SidebarNavProps) {
  return (
    <nav
      className={cn(
        "flex space-x-2 lg:flex-col lg:space-x-0 lg:space-y-1",
        className
      )}
      {...props}
    >
      {items.map((item) => (
        <NavLink
          key={item.href}
          to={item.href}
          className={({ isActive }) =>
            cn(
              "justify-start text-sm font-medium transition-colors hover:text-primary flex items-center py-2 px-3 rounded-md",
              isActive
                ? "bg-secondary text-primary"
                : "text-muted-foreground hover:bg-muted"
            )
          }
        >
          <span className="mr-2">{item.icon}</span>
          {item.title}
        </NavLink>
      ))}
    </nav>
  );
}

export function MainLayout() {
  const navItems = [
    {
      title: "Editor",
      href: "/editor",
      icon: <Map className="h-4 w-4" />,
    },
    {
      title: "Load Data",
      href: "/load-data",
      icon: <UploadCloud className="h-4 w-4" />,
    },
  ];

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <aside className="border-r bg-background lg:w-64 lg:min-h-screen">
        <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
          <NavLink to="/" className="flex items-center gap-2 font-semibold">
            <Box className="h-6 w-6" />
            <span className="">Canopy</span>
          </NavLink>
        </div>
        <div className="py-4 px-3">
          <SidebarNav items={navItems} />
        </div>
      </aside>
      <main className="flex-1 bg-background">
        <Outlet />
      </main>
    </div>
  );
}
