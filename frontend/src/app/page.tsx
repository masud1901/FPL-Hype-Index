'use client';

import { PixelButton } from '@/components/PixelButton';
import { fplAPI, GutCheckResult, Player } from '@/lib/api';
import { motion } from 'framer-motion';
import { useState } from 'react';

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Player[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [gutCheckResult, setGutCheckResult] = useState<GutCheckResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  // Search players
  const handleSearch = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await fplAPI.searchPlayers(query);
      setSearchResults(results.slice(0, 5)); // Limit to 5 results
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    handleSearch(query);
  };

  // Select a player
  const handlePlayerSelect = (player: Player) => {
    setSelectedPlayer(player);
    setSearchQuery(player.name);
    setSearchResults([]);
  };

  // Check gut feeling
  const handleGutCheck = async () => {
    if (!selectedPlayer) return;

    setIsLoading(true);
    try {
      const result = await fplAPI.getGutCheckResult(selectedPlayer.id);
      setGutCheckResult(result);
    } catch (error) {
      console.error('Gut check failed:', error);
      // You could show an error message here
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="main-container">
        <div className="compact-layout">
          {/* Header */}
          <div className="compact-header">
            <h1 className="pixel-title">
              FPL HYPE INDEX
            </h1>
            <p className="pixel-subtitle">
              Empower Your Gut Feelings
            </p>
          </div>

          {/* Horizontal Dividers */}
          <div className="pixel-divider"></div>
          <div className="pixel-divider"></div>

          {/* Main Content */}
          <div className="compact-content">
            {/* Search Section */}
            <div className="text-center">
              <div className="mb-4">
                <label className="pixel-body block mb-2">
                  "I think [Player Name] is going to..."
                </label>
                <div className="relative max-w-md mx-auto">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={handleSearchChange}
                    placeholder="Type player name here..."
                    className="pixel-input"
                  />
                  {isSearching && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <div className="pixel-loading"></div>
                    </div>
                  )}
                </div>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="space-y-2 max-w-md mx-auto">
                  {searchResults.map((player) => (
                    <div
                      key={player.id}
                      onClick={() => handlePlayerSelect(player)}
                      className="pixel-hover-effect cursor-pointer p-2 border border-gray-600 hover:border-green-400 bg-blue-900"
                    >
                      <div className="pixel-body">
                        <strong>{player.name}</strong> - {player.team} ({player.position})
                      </div>
                      <div className="pixel-body text-sm text-gray-400">
                        £{(player.price / 10).toFixed(1)}m • {player.form} pts form
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Check Button */}
              <div className="mt-6">
                <PixelButton
                  variant="primary"
                  onClick={handleGutCheck}
                  disabled={!selectedPlayer || isLoading}
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2 justify-center">
                      <div className="pixel-loading"></div>
                      Checking...
                    </span>
                  ) : (
                    '🔍 CHECK MY GUT FEELING'
                  )}
                </PixelButton>
              </div>
            </div>

            {/* Horizontal Dividers */}
            <div className="pixel-divider"></div>
            <div className="pixel-divider"></div>

            {/* Gut Check Result */}
            {gutCheckResult && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-center"
              >
                <div className={`pixel-card ${gutCheckResult.result_type === 'success' ? 'pixel-card-success' : 
                  gutCheckResult.result_type === 'warning' ? 'pixel-card-warning' : 'pixel-card-danger'}`}>
                  <h2 className="pixel-subtitle mb-4">
                    🎯 {gutCheckResult.player.name}
                  </h2>
                  
                  <div className="mb-4">
                    <div className={`pixel-title text-xl mb-2 ${
                      gutCheckResult.result_type === 'success' ? 'text-green-400' :
                      gutCheckResult.result_type === 'warning' ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {gutCheckResult.message}
                    </div>
                    <div className="pixel-subtitle">
                      Hype Index: {gutCheckResult.hype_index.toFixed(1)}/10
                    </div>
                  </div>

                  {/* Insights */}
                  <div className="text-left">
                    <h3 className="pixel-subtitle mb-2">💡 Why your instinct is right:</h3>
                    <ul className="space-y-1">
                      {gutCheckResult.insights.map((insight, index) => (
                        <li key={index} className="pixel-body flex items-center gap-2">
                          <span>•</span>
                          <span>{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Footer */}
          <div className="compact-footer">
            <p className="pixel-body text-gray-400">
              TRUST YOUR GUT. WE'LL HANDLE THE NUMBERS.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
