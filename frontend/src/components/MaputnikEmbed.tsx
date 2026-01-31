import React, { useRef, useState } from 'react';
import { createPortal } from 'react-dom';

interface MaputnikEmbedProps {
  styleUrl: string;
  onBack: () => void;
}

export const MaputnikEmbed: React.FC<MaputnikEmbedProps> = ({ styleUrl, onBack }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [savedStyle, setSavedStyle] = useState<string | null>(null);
  const [toolbarNode, setToolbarNode] = useState<HTMLElement | null>(null);

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

  const iframeSrc = `/editor/?style=${encodeURIComponent(styleUrl)}`;



  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', border: 'none' }}>
      {/* We no longer render the top bar here, it's moved into the iframe */}
      
      <iframe
        ref={iframeRef}
        src={iframeSrc}
        style={{ flex: 1, border: 'none', width: '100%' }}
        title="Maputnik Editor"
        onLoad={() => {
            if (iframeRef.current && iframeRef.current.contentWindow) {
                try {
                    const iframeWindow = iframeRef.current.contentWindow as any;
                    const iframeDocument = iframeRef.current.contentDocument;

                    // 1. Override confirm
                    iframeWindow._originalConfirm = iframeWindow.confirm;
                    iframeWindow.confirm = (message: string) => {
                        if (message && message.includes("discard current changes")) {
                            return true;
                        }
                        return true; 
                    };

                    // 2. Setup robust injection using MutationObserver
                    if (iframeDocument) {
                        
                        // Inject global CSS to hide original toolbar items but show ours
                        const stylePath = "canopy-toolbar-style";
                        if (!iframeDocument.getElementById(stylePath)) {
                            const style = iframeDocument.createElement('style');
                            style.id = stylePath;
                            // Hide direct children of toolbar actions that are NOT our mount point
                            style.textContent = `
                                .maputnik-toolbar__actions > *:not(.canopy-toolbar-mount) {
                                    display: none !important;
                                }
                                .canopy-toolbar-mount {
                                    width: 100%;
                                    height: 100%;
                                    display: block;
                                }
                            `;
                            iframeDocument.head.appendChild(style);
                        }

                        // Function to try mounting the portal
                        const tryMount = () => {
                            const toolbarActions = iframeDocument.querySelector('.maputnik-toolbar__actions') as HTMLElement;
                            if (toolbarActions) {
                                // Check if we are already mounted
                                if (!toolbarActions.querySelector('.canopy-toolbar-mount')) {
                                    console.log("Injecting Canopy toolbar mount point...");
                                    const mountPoint = iframeDocument.createElement('div');
                                    mountPoint.className = 'canopy-toolbar-mount';
                                    toolbarActions.appendChild(mountPoint);
                                    setToolbarNode(mountPoint);
                                }
                            }
                        };

                        // Attempt immediately
                        tryMount();

                        // And watch for changes in the body (in case Maputnik re-renders the toolbar)
                        const observer = new MutationObserver((mutations) => {
                           tryMount();
                        });

                        observer.observe(iframeDocument.body, {childList: true, subtree: true});
                        
                        // Cleanup observer when component unmounts?
                        // Ideally checking if iframe is still valid
                    }

                } catch (e) {
                    console.error("Could not customize iframe:", e);
                }
            }
        }}
      />
      

      {toolbarNode && createPortal(
        <div style={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between', paddingRight: '10px' }}>
          <span style={{ color: '#1FC98F', fontWeight: 'bold', fontSize: '16px' }}>Canopy edition</span>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
                onClick={onBack}
                style={{ 
                    padding: '5px 12px', 
                    background: '#444', 
                    color: 'white', 
                    border: '1px solid #666', 
                    borderRadius: '4px', 
                    cursor: 'pointer',
                    fontSize: '13px'
                }}
            >
                &larr; Retour
            </button>
            <button 
                onClick={handleSave} 
                style={{ 
                    padding: '5px 12px', 
                    background: '#007bff', 
                    color: 'white', 
                    border: 'none', 
                    borderRadius: '4px', 
                    cursor: 'pointer',
                    fontSize: '13px' 
                }}
            >
                Sauvegarder
            </button>
          </div>
        </div>,
        toolbarNode
      )}
      
      {savedStyle && (
        <div style={{ padding: '10px', background: '#333', color: '#fff', maxHeight: '150px', overflow: 'auto', fontSize: '0.8em' }}>
            <p><strong>Style récupéré (appercu):</strong></p>
            <pre>{savedStyle.slice(0, 300)}...</pre>
        </div>
      )}
    </div>
  );
};
