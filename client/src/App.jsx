import { useState, useEffect, useRef } from 'react';

export default function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const suggestionsRef = useRef(null);
  const [searchTime, setSearchTime] = useState(null);

  // Handle suggestion search with debouncing
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (query.trim()) {
        fetchSuggestions();
      } else {
        setSuggestions([]);
      }
    }, 300); // 300ms delay

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchSuggestions = async () => {
    try {
      const response = await fetch(`/api/v1/hits/?q=${encodeURIComponent(query)}&k=5`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.results || []);
        setSearchTime(data.search_time)
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setHasSearched(true);
    setShowSuggestions(false);
    
    try {
      const response = await fetch(`/api/v1/hits/?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search failed');
      
      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (title) => {
    setQuery(title);
    setShowSuggestions(false);
    handleSearch();
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl mb-8 text-center font-sans">
        Wikipedia Search
      </h1>
      
      <div className="mb-8 relative" ref={suggestionsRef}>
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              className="w-full px-4 py-2.5 border rounded-md text-base"
              placeholder="Enter search query..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setShowSuggestions(true);
              }}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              onFocus={() => query.trim() && setShowSuggestions(true)}
            />
            
            {/* Suggestions dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute w-full mt-1 bg-white border rounded-md shadow-lg z-10">
                {suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    className="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm"
                    onClick={() => handleSuggestionClick(suggestion.title)}
                  >
                    {suggestion.title}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 
                     disabled:opacity-50 disabled:cursor-not-allowed font-sans font-medium
                     transition-colors duration-200"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>
      {hasSearched && searchTime && !error && (
        <div className="text-sm text-gray-600 mb-4">
          Found {results.length} {results.length === 1 ? 'result ' : 'results '} 
          ({(searchTime * 1000).toFixed(2)} milliseconds)
        </div>
      )}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {results.map((result, index) => (
          <article key={index} className="result-card">
            <header className="mb-2">
              <h2 className="text-xl font-serif text-blue-600 hover:text-blue-800 cursor-pointer">
                <a 
                  href={`https://en.wikipedia.org${result.url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 cursor-pointer"
                >
                {result.title}
                </a>
              </h2>
              <div className="text-sm text-gray-500 mt-1 font-sans">
                Score: {result.score.toFixed(4)}
              </div>
            </header>
            
            <p className="wiki-summary">
              {result.summary}
            </p>
          </article>
        ))}
        
        {results.length > 0 && (
          <div className="text-sm text-gray-600 text-center mt-4 font-sans">
            Found {results.length} {results.length === 1 ? 'result' : 'results'}
          </div>
        )}
        
        {hasSearched && query && results.length === 0 && !loading && !error && (
          <div className="text-center text-gray-600 font-sans">
            No results found for "{query}"
          </div>
        )}
      </div>
    </div>
  );
}