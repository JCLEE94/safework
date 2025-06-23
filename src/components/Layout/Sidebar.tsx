import React from 'react';
import { X } from 'lucide-react';
import * as Icons from 'lucide-react';
import { MENU_ITEMS } from '../../constants';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeMenu: string;
  onMenuSelect: (menuId: string) => void;
}

export function Sidebar({ isOpen, onClose, activeMenu, onMenuSelect }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-gray-900 to-gray-800 
        text-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0
      `}>
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
            SafeWork Pro
          </h1>
          <button 
            onClick={onClose}
            className="md:hidden text-gray-400 hover:text-white"
          >
            <X size={24} />
          </button>
        </div>
        
        <nav className="mt-8 px-4">
          {MENU_ITEMS.map((item) => {
            const Icon = Icons[item.icon as keyof typeof Icons] as React.ComponentType<{ size?: number; className?: string }>;
            
            return (
              <button
                key={item.id}
                onClick={() => {
                  onMenuSelect(item.id);
                  onClose();
                }}
                className={`
                  w-full flex items-center px-4 py-3 rounded-lg mb-2 transition-all duration-200
                  ${activeMenu === item.id 
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 shadow-lg transform scale-105' 
                    : 'hover:bg-gray-700 hover:shadow-md'
                  }
                `}
              >
                <Icon size={20} className={activeMenu === item.id ? 'text-white' : item.color} />
                <span className="ml-3 font-medium">{item.name}</span>
              </button>
            );
          })}
        </nav>
        
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-gray-700 rounded-lg p-3">
            <p className="text-xs text-gray-400">건설업 보건관리 시스템</p>
            <p className="text-xs text-gray-500 mt-1">v1.0.0</p>
          </div>
        </div>
      </aside>
    </>
  );
}