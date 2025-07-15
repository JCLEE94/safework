import React, { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  activeMenu: string;
  setActiveMenu: (menu: string) => void;
  onLogout?: () => void;
}

export function Layout({ 
  children, 
  sidebarOpen, 
  setSidebarOpen, 
  activeMenu, 
  setActiveMenu,
  onLogout 
}: LayoutProps) {
  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Sidebar 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeMenu={activeMenu}
        onMenuSelect={setActiveMenu}
        onLogout={onLogout}
      />
      
      <div className="flex-1 flex flex-col md:ml-64">
        <Header 
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)} 
          onLogout={onLogout}
        />
        
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}