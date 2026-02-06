import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useEffect, useRef, useState } from 'react';

interface MapPreviewProps {
    data: any; // GeoJSON
    bbox?: number[];
}

export function MapPreview({ data, bbox }: MapPreviewProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);

    const [styleLoaded, setStyleLoaded] = useState(false);

    useEffect(() => {
        if (!mapContainer.current) return;
        if (map.current) return;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: 'https://demotiles.maplibre.org/style.json', // Basic style
            center: [0, 0],
            zoom: 1,
            attributionControl: false
        });

        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
        map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

        map.current.on('load', () => {
             setStyleLoaded(true);
        });
        
        return () => {
            map.current?.remove();
            map.current = null;
        }
    }, []);

    useEffect(() => {
        if (!map.current || !styleLoaded) return;
        
        const sourceId = 'preview-source';
        const layerId = 'preview-layer';
        const lineLayerId = 'preview-line';

        const source = map.current.getSource(sourceId) as maplibregl.GeoJSONSource;

        if (source) {
            source.setData(data);
        } else {
            map.current.addSource(sourceId, {
                type: 'geojson',
                data: data
            });

            // Fallback for polygon/point/line
            // Simple generic styling
            
            // Fill
            map.current.addLayer({
                id: layerId, // Use variable
                type: 'fill',
                source: sourceId,
                paint: {
                    'fill-color': '#0080ff',
                    'fill-opacity': 0.4
                },
                filter: ['==', '$type', 'Polygon']
            });

             // Line
            map.current.addLayer({
                id: lineLayerId, // Use variable
                type: 'line',
                source: sourceId,
                paint: {
                    'line-color': '#0080ff',
                    'line-width': 2
                }
            });

             // Point
            map.current.addLayer({
                id: 'preview-point',
                type: 'circle',
                source: sourceId,
                paint: {
                    'circle-radius': 6,
                    'circle-color': '#0080ff',
                    'circle-stroke-width': 1,
                    'circle-stroke-color': '#fff'
                },
                filter: ['==', '$type', 'Point']
            });
        }
        
        // Fit bounds if bbox is provided and valid (non-zero area or at least distinct points)
        if (bbox && bbox.length === 4) {
             const [minX, minY, maxX, maxY] = bbox;
             if (minX !== 0 || maxX !== 0 || minY !== 0 || maxY !== 0) {
                 try {
                     map.current.fitBounds([minX, minY, maxX, maxY], {
                         padding: 40,
                         animate: true
                     });
                 } catch (e) {
                     console.warn("Invalid bbox", bbox);
                 }
             }
        }

    }, [data, bbox, styleLoaded]);

    return <div ref={mapContainer} className="w-full h-[400px] rounded-md border" />;
}
