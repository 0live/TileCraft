import { useState } from 'react';
import './App.css';
import { MaputnikEmbed } from './components/MaputnikEmbed';

const STYLES = [
  { name: 'OSM Liberty', url: 'https://maputnik.github.io/osm-liberty/style.json' },
  { name: 'Positron (OpenMapTiles)', url: 'https://openmaptiles.github.io/positron-gl-style/style.json' },
  { name: 'Dark Matter (OpenMapTiles)', url: 'https://openmaptiles.github.io/dark-matter-gl-style/style.json' }
];

function App() {
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null);

  return (
    <div className="container" style={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: '1rem', borderBottom: '1px solid #ddd' }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Canopy Style Editor</h1>
      </header>
      
      {!selectedStyle ? (
        <div className="style-selector" style={{ padding: '2rem' }}>
          <h2>Choisissez un fond de carte de départ</h2>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            {STYLES.map((style) => (
              <button 
                key={style.url} 
                onClick={() => {
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
                  
                  // Force a small delay to ensure storage event propagates if needed (though it should be sync)
                  setTimeout(() => {
                      setSelectedStyle(style.url);
                  }, 50);
                }}
                style={{ 
                  padding: '20px', 
                  fontSize: '1.1em', 
                  cursor: 'pointer',
                  border: '1px solid #ccc',
                  borderRadius: '8px',
                  background: '#333',
                  color: 'white',
                  minWidth: '200px'
                }}
              >
                {style.name}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="editor-view" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1 }}>
            <MaputnikEmbed 
                styleUrl={selectedStyle} 
                onBack={() => {
                    // Force clean up if needed
                    setSelectedStyle(null);
                }} 
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default App
