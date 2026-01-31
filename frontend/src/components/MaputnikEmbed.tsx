import React, { useRef, useState } from 'react';

interface MaputnikEmbedProps {
  styleUrl: string;
}

export const MaputnikEmbed: React.FC<MaputnikEmbedProps> = ({ styleUrl }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [savedStyle, setSavedStyle] = useState<string | null>(null);

  // Function to save/retrieve the style
  const handleSave = () => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      try {
        // Accessing localStorage of the iframe (same origin)
        const storage = iframeRef.current.contentWindow.localStorage;
        const latestStyleId = storage.getItem('maputnik:latest_style');
        
        // 1. Try getting the style using the ID from latest_style
        let styleStr = latestStyleId ? storage.getItem(`maputnik:style:${latestStyleId}`) : null;

        // 2. If valid JSON in latest_style itself (unlikely but possible in some versions)
        if (!styleStr && latestStyleId && latestStyleId.trim().startsWith('{')) {
             styleStr = latestStyleId;
        }

        // 3. Fallback: Find the first key looking like a style
        if (!styleStr) {
             const styleKey = Object.keys(storage).find(k => k.startsWith('maputnik:style:'));
             if (styleKey) {
                 styleStr = storage.getItem(styleKey);
             }
        }

        if (styleStr) {
          const parsedStyle = JSON.parse(styleStr);
          console.log('Retrieved style:', parsedStyle);
          setSavedStyle(JSON.stringify(parsedStyle, null, 2));
          alert('Style retrieved successfully!');
        } else {
          console.warn('Available keys:', Object.keys(storage));
          alert('No style found in Maputnik storage. Try modifying the style first.');
        }
      } catch (e) {
        console.error('Error accessing iframe storage:', e);
        alert('Error accessing Maputnik storage. Are they on the same origin?');
      }
    }
  };

  // Maputnik expects URL to the style. 
  // We use the proxy path.
  const iframeSrc = `/editor/?style=${encodeURIComponent(styleUrl)}`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', border: 'none' }}>
      <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>Maputnik Embed</strong>
        <button 
          onClick={handleSave} 
          style={{ 
            padding: '8px 16px', 
            background: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: 'pointer' 
          }}
        >
          Sauvegarder le Style
        </button>
      </div>
      
      <iframe
        ref={iframeRef}
        src={iframeSrc}
        style={{ flex: 1, border: 'none', width: '100%' }}
        title="Maputnik Editor"
        onLoad={() => {
            // Because we are same-origin, we can override window.confirm inside the iframe
            // to automatically accept "discard changes" alerts.
            if (iframeRef.current && iframeRef.current.contentWindow) {
                try {
                    const iframeWindow = iframeRef.current.contentWindow as any;
                    const iframeDocument = iframeRef.current.contentDocument;

                    // 1. Override confirm
                    iframeWindow._originalConfirm = iframeWindow.confirm;
                    iframeWindow.confirm = (message: string) => {
                        console.log("Suppressed confirm:", message);
                        if (message && message.includes("discard current changes")) {
                            return true;
                        }
                        return true; 
                    };

                    // 2. Inject CSS to hide toolbar actions and add title
                    if (iframeDocument) {
                        const style = iframeDocument.createElement('style');
                        style.textContent = `
                            .maputnik-toolbar__actions > * { 
                                display: none !important; 
                            }
                            .maputnik-toolbar__actions::after {
                                content: "Canopy edition";
                                color: #1FC98F;
                                font-size: 16px;
                                font-weight: bold;
                                display: flex;
                                align-items: center;
                                height: 100%;
                            }
                        `;
                        iframeDocument.head.appendChild(style);
                    }

                } catch (e) {
                    console.error("Could not customize iframe:", e);
                }
            }
        }}
      />
      
      {savedStyle && (
        <div style={{ padding: '10px', background: '#333', color: '#fff', maxHeight: '150px', overflow: 'auto', fontSize: '0.8em' }}>
            <p><strong>Style récupéré (appercu):</strong></p>
            <pre>{savedStyle.slice(0, 300)}...</pre>
        </div>
      )}
    </div>
  );
};
