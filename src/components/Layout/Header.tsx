import React, { useState } from 'react';
import { Menu, Bell, Search, LogOut, User } from 'lucide-react';
import { BUILD_TIME } from '../../constants';
import { authService } from '../../services/authService';

interface HeaderProps {
  onMenuToggle: () => void;
  onLogout?: () => void;
}

export function Header({ onMenuToggle, onLogout }: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const user = authService.getUser();

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    }
    setShowUserMenu(false);
  };

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
          
          <div className="flex items-center space-x-2 md:space-x-4">
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
            
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <img
                  src={`https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || '사용자')}&background=4F46E5&color=fff`}
                  alt="User"
                  className="h-8 w-8 rounded-full"
                />
                <span className="text-sm font-medium text-gray-700 hidden md:block">
                  {user?.name || '사용자'}
                </span>
              </button>
              
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-[9999]">
                  <div className="py-1">
                    <div className="px-4 py-2 text-sm text-gray-500 border-b border-gray-200">
                      {user?.email}
                    </div>
                    <button
                      onClick={handleLogout}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      <LogOut size={16} className="mr-2" />
                      로그아웃
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}