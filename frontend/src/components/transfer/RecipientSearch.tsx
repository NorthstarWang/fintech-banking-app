'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Search, Loader2, X } from 'lucide-react';
import { usersService, UserSearchResult } from '@/lib/api/users';
import { useDebounce } from '@/hooks/useDebounce';

interface RecipientSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: (user: UserSearchResult) => void;
  error?: string;
  placeholder?: string;
}

export const RecipientSearch: React.FC<RecipientSearchProps> = ({
  value,
  onChange,
  onSelect,
  error,
  placeholder = "Email, phone, or username"
}) => {
  const [searchQuery, setSearchQuery] = useState(value);
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserSearchResult | null>(null);
  const debouncedSearch = useDebounce(searchQuery, 300);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Handle clicking outside dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Search for users when query changes
  useEffect(() => {
    if (debouncedSearch && debouncedSearch.length >= 2 && !selectedUser) {
      searchUsers();
    } else {
      setSearchResults([]);
      setShowDropdown(false);
    }
  }, [debouncedSearch, selectedUser]);

  const searchUsers = async () => {
    setIsSearching(true);
    try {
      const results = await usersService.searchUsers(debouncedSearch);
      setSearchResults(results);
      setShowDropdown(results.length > 0);
    } catch (error) {
      console.error('Failed to search users:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setSearchQuery(newValue);
    onChange(newValue);
    
    // Clear selected user if input is changed
    if (selectedUser) {
      setSelectedUser(null);
    }
  };

  const handleSelectUser = (user: UserSearchResult) => {
    setSelectedUser(user);
    setSearchQuery(user.username);
    onChange(user.username);
    onSelect(user);
    setShowDropdown(false);
  };

  const clearSelection = () => {
    setSelectedUser(null);
    setSearchQuery('');
    onChange('');
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
        Recipient
      </label>
      
      {/* Selected User Display */}
      {selectedUser && (
        <div className="mb-2 p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--primary-blue)] to-[var(--primary-indigo)] flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-medium text-[var(--text-1)]">{selectedUser.full_name}</p>
              <p className="text-sm text-[var(--text-2)]">{selectedUser.username}</p>
            </div>
          </div>
          <button
            onClick={clearSelection}
            className="p-1 hover:bg-[rgba(var(--glass-rgb),0.2)] rounded-md transition-colors"
          >
            <X className="w-4 h-4 text-[var(--text-2)]" />
          </button>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={searchQuery}
          onChange={handleInputChange}
          onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
          placeholder={placeholder}
          disabled={!!selectedUser}
          className={`
            w-full px-4 py-3 pl-10 
            bg-[rgba(var(--glass-rgb),0.05)] 
            border ${error ? 'border-[var(--primary-red)]' : 'border-[var(--border-1)]'}
            rounded-lg
            text-[var(--text-1)]
            placeholder-[var(--text-3)]
            focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all
          `}
        />
        <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
          {isSearching ? (
            <Loader2 className="w-5 h-5 text-[var(--text-2)] animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-[var(--text-2)]" />
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <p className="text-sm text-[var(--primary-red)] mt-1">{error}</p>
      )}

      {/* Help Text */}
      {!selectedUser && (
        <p className="text-xs text-[var(--text-2)] mt-1">
          Search by username, email, or full name
        </p>
      )}

      {/* Search Results Dropdown */}
      <AnimatePresence>
        {showDropdown && (
          <motion.div
            ref={dropdownRef}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-2 z-50 bg-[var(--bg-color)] border border-[var(--border-1)] rounded-lg shadow-xl overflow-hidden"
          >
            {searchResults.map((user) => (
              <motion.button
                key={user.id}
                whileHover={{ backgroundColor: 'rgba(var(--glass-rgb), 0.1)' }}
                onClick={() => handleSelectUser(user)}
                className="w-full p-3 flex items-center gap-3 text-left transition-colors"
              >
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--primary-blue)] to-[var(--primary-indigo)] flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-[var(--text-1)] truncate">{user.full_name}</p>
                  <p className="text-sm text-[var(--text-2)] truncate">
                    @{user.username} • {user.email}
                  </p>
                </div>
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RecipientSearch;