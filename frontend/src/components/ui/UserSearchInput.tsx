'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, User, X, Loader2 } from 'lucide-react';
import { usersService, UserSearchResult } from '@/lib/api/users';
import { useDebounce } from '@/hooks/useDebounce';

interface UserSearchInputProps {
  label?: string;
  placeholder?: string;
  value: UserSearchResult | null;
  onChange: (user: UserSearchResult | null) => void;
  required?: boolean;
  error?: string;
}

export const UserSearchInput: React.FC<UserSearchInputProps> = ({
  label = 'Joint Owner',
  placeholder = 'Search for a user...',
  value,
  onChange,
  required = false,
  error,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  // Search for users when query changes
  useEffect(() => {
    const searchUsers = async () => {
      if (!debouncedSearchQuery || debouncedSearchQuery.length < 2) {
        setSearchResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const results = await usersService.searchUsers(debouncedSearchQuery);
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    searchUsers();
  }, [debouncedSearchQuery]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectUser = (user: UserSearchResult) => {
    onChange(user);
    setSearchQuery('');
    setIsOpen(false);
    setSearchResults([]);
  };

  const handleClearSelection = () => {
    onChange(null);
    setSearchQuery('');
    setSearchResults([]);
  };

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
          {label}
          {required && <span className="text-[var(--primary-red)] ml-1">*</span>}
        </label>
      )}

      {/* Selected User Display */}
      {value ? (
        <div className="flex items-center justify-between p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.3)] border border-[var(--border-1)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[rgba(var(--glass-rgb),0.3)] border border-[var(--border-1)] flex items-center justify-center">
              <User size={18} className="text-[var(--text-2)]" />
            </div>
            <div>
              <p className="font-medium text-[var(--text-1)]">{value.full_name}</p>
              <p className="text-sm text-[var(--text-2)]">@{value.username}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClearSelection}
            className="p-1 rounded hover:bg-[rgba(var(--glass-rgb),0.3)] transition-colors"
          >
            <X size={18} className="text-[var(--text-2)]" />
          </button>
        </div>
      ) : (
        <>
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--text-2)] w-5 h-5" />
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setIsOpen(true);
              }}
              onFocus={() => setIsOpen(true)}
              placeholder={placeholder}
              className={`
                w-full pl-10 pr-10 py-3 rounded-lg 
                bg-[rgba(var(--glass-rgb),0.3)] border 
                ${error ? 'border-[var(--primary-red)]' : 'border-[var(--border-1)]'}
                text-[var(--text-1)] placeholder-[var(--text-2)]
                focus:outline-none focus:border-[var(--primary-blue)]
                transition-colors
              `}
            />
            {isLoading && (
              <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[var(--text-2)] w-5 h-5 animate-spin" />
            )}
          </div>

          {/* Search Results Dropdown */}
          <AnimatePresence>
            {isOpen && (searchResults.length > 0 || (searchQuery.length >= 2 && !isLoading)) && (
              <motion.div
                ref={dropdownRef}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="absolute z-50 w-full mt-2 rounded-lg bg-[var(--bg-color)] border border-[var(--border-1)] shadow-lg overflow-hidden"
              >
                {searchResults.length > 0 ? (
                  <div className="max-h-60 overflow-y-auto">
                    {searchResults.map((user) => (
                      <button
                        key={user.id}
                        type="button"
                        onClick={() => handleSelectUser(user)}
                        className="w-full p-3 flex items-center gap-3 hover:bg-[rgba(var(--glass-rgb),0.3)] transition-colors text-left"
                      >
                        <div className="w-10 h-10 rounded-full bg-[rgba(var(--glass-rgb),0.3)] border border-[var(--border-1)] flex items-center justify-center">
                          <User size={18} className="text-[var(--text-2)]" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-[var(--text-1)]">{user.full_name}</p>
                          <p className="text-sm text-[var(--text-2)]">@{user.username} • {user.email}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-center text-[var(--text-2)]">
                    No users found
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}

      {error && (
        <p className="mt-1 text-sm text-[var(--primary-red)]">{error}</p>
      )}
    </div>
  );
};

export default UserSearchInput;