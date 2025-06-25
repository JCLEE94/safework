import React from 'react';
import { Menu, Bell, Search } from 'lucide-react';
import { BUILD_TIME } from '../../constants';

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="bg-white shadow-lg border-b border-gray-200">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <button
              onClick={onMenuToggle}
              className="md:hidden text-gray-500 hover:text-gray-700 focus:outline-none"
            >
              <Menu size={24} />
            </button>
            
            <div className="ml-4 md:ml-0">
              <h2 className="text-xl font-semibold text-gray-800">
                SafeWork Pro
              </h2>
              <p className="text-xs text-gray-500">Build: {BUILD_TIME}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center bg-gray-100 rounded-lg px-3 py-2">
              <Search size={18} className="text-gray-500" />
              <input
                type="text"
                placeholder="검색..."
                className="ml-2 bg-transparent border-none focus:outline-none text-sm"
              />
            </div>
            
            <button className="relative p-2 text-gray-500 hover:text-gray-700 transition-colors">
              <Bell size={20} />
              <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full"></span>
            </button>
            
            <div className="flex items-center">
              <img
                src="https://ui-avatars.com/api/?name=Admin&background=4F46E5&color=fff"
                alt="User"
                className="h-8 w-8 rounded-full"
              />
              <span className="ml-2 text-sm font-medium text-gray-700 hidden md:block">
                관리자
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}