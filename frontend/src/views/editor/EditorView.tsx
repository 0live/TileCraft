import { useState } from 'react';
import { MaputnikEmbed } from './components/MaputnikEmbed';

const STYLES = [
  { name: 'OSM Liberty', url: 'https://maputnik.github.io/osm-liberty/style.json' },
  { name: 'Positron (OpenMapTiles)', url: 'https://openmaptiles.github.io/positron-gl-style/style.json' },
  { name: 'Dark Matter (OpenMapTiles)', url: 'https://openmaptiles.github.io/dark-matter-gl-style/style.json' }
];

export function EditorView() {
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null);

  const handleStyleSelect = (url: string) => {
    // Clear Maputnik local storage aggressively
    try {
      console.log('Clearing storage. Keys before:', Object.keys(localStorage));
      
      // Clear specific maputnik keys
      Object.keys(localStorage).forEach(key => {
        if (key.includes('maputnik')) {
          localStorage.removeItem(key);
        }
      });
      
      // Also clear session storage just in case
      sessionStorage.clear();
      
      console.log('Keys after:', Object.keys(localStorage));
    } catch (e) {
      console.error("Could not clear local storage", e);
    }
    
    // Force a small delay to ensure storage event propagates if needed
    setTimeout(() => {
        setSelectedStyle(url);
    }, 50);
  };

  return (
    <div className="flex flex-col h-full w-full">
      <header className="px-6 py-4 border-b flex items-center justify-between">
          <h1 className="text-xl font-semibold tracking-tight">Style Editor</h1>
          {selectedStyle && (
              <button 
                onClick={() => setSelectedStyle(null)}
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  Change Style
              </button>
          )}
      </header>
      
      <div className="flex-1 relative overflow-hidden">
        {!selectedStyle ? (
          <div className="p-8">
            <h2 className="text-2xl font-bold mb-6">Choose a base style</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {STYLES.map((style) => (
                <button 
                  key={style.url} 
                  onClick={() => handleStyleSelect(style.url)}
                  className="flex flex-col items-center justify-center p-8 border rounded-lg hover:bg-muted/50 transition-colors text-center space-y-4 group h-48 bg-card text-card-foreground shadow-sm hover:border-primary/50"
                >
                  <div className="text-lg font-medium group-hover:text-primary">{style.name}</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="w-full h-full">
            <MaputnikEmbed 
                styleUrl={selectedStyle} 
                onBack={() => {
                    setSelectedStyle(null);
                }} 
            />
          </div>
        )}
      </div>
    </div>
  );
}
