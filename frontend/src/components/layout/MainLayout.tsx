import { cn } from '@/lib/utils';
import { useAuthStore } from '@/store/auth';
import { LoginDialog } from '@/views/auth/LoginDialog';
import { Box, LogIn, LogOut, Map, UploadCloud } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Button } from '../ui/button';

interface SidebarNavProps extends React.HTMLAttributes<HTMLElement> {
  items: {
    href: string;
    title: string;
    icon: React.ReactNode;
  }[];
}

function SidebarNav({ className, items, ...props }: SidebarNavProps) {
  return (
    // ... existing SidebarNav impl ...
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
  const { user, isAuthenticated, logout, checkAuth } = useAuthStore();
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

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
      <aside className="border-r bg-background lg:w-64 lg:min-h-screen flex flex-col">
        <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
          <NavLink to="/" className="flex items-center gap-2 font-semibold">
            <Box className="h-6 w-6" />
            <span className="">Canopy</span>
          </NavLink>
        </div>
        <div className="py-4 px-3 flex-1">
          <SidebarNav items={navItems} />
        </div>
        
        {/* Auth Section at Bottom */}
        <div className="p-4 border-t">
            {isAuthenticated ? (
                <div className="space-y-2">
                    <div className="text-sm font-medium px-2 truncate">
                        {user?.username}
                    </div>
                    <Button 
                        variant="ghost" 
                        size="sm" 
                        className="w-full justify-start text-muted-foreground hover:text-destructive"
                        onClick={() => logout()}
                    >
                        <LogOut className="mr-2 h-4 w-4" />
                        Logout
                    </Button>
                </div>
            ) : (
                <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full justify-start"
                    onClick={() => setShowLogin(true)}
                >
                    <LogIn className="mr-2 h-4 w-4" />
                    Login
                </Button>
            )}
        </div>
      </aside>
      <main className="flex-1 bg-background">
        <Outlet />
      </main>
      
      <LoginDialog open={showLogin} onOpenChange={setShowLogin} />
    </div>
  );
}
