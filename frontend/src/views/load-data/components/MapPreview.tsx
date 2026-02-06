import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Protocol } from 'pmtiles';
import { useEffect, useRef, useState } from 'react';

interface MapPreviewProps {
    data?: any; // GeoJSON
    bbox?: number[];
    type?: 'geojson' | 'pmtiles';
    url?: string;
    layers?: string[];
}

export function MapPreview({ data, bbox, type = 'geojson', url, layers }: MapPreviewProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);

    const [styleLoaded, setStyleLoaded] = useState(false);

    useEffect(() => {
        if (!mapContainer.current) return;
        if (map.current) return;

        // Register PMTiles protocol globally (or idempotently)
        try {
            const protocol = new Protocol();
            maplibregl.addProtocol('pmtiles', protocol.tile);
        } catch (e) {
            // Protocol might be already added, ignore
        }

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json', // Carto Positron
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
        
        // Clean up previous layers/source if they exist (to handle prop changes)
        // Note: strictly doing this might be complex with React lifecycle, 
        // but for this wizard, props likely won't change rapidly.
        if (map.current.getSource(sourceId)) {
             const style = map.current.getStyle();
             if (style && style.layers) {
                 style.layers.forEach(l => {
                     if ('source' in l && l.source === sourceId) {
                         map.current?.removeLayer(l.id);
                     }
                 });
             }
             map.current.removeSource(sourceId);
        }

        if (type === 'geojson' && data) {
            map.current.addSource(sourceId, {
                type: 'geojson',
                data: data
            });

            // Fill
            map.current.addLayer({
                id: `${sourceId}-fill`,
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
                id: `${sourceId}-line`,
                type: 'line',
                source: sourceId,
                paint: {
                    'line-color': '#0080ff',
                    'line-width': 2
                },
                filter: ['==', '$type', 'LineString']
            });

            // Point
            map.current.addLayer({
                id: `${sourceId}-point`,
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

        } else if (type === 'pmtiles' && url) {
            map.current.addSource(sourceId, {
                type: 'vector',
                url: `pmtiles://${url}`
            });

            // Add layers for each vector layer found in metadata
            if (layers && layers.length > 0) {
                layers.forEach((layerName, i) => {
                    const color = `hsl(${(i * 137.5) % 360}, 70%, 50%)`; // Distinct colors

                    // Polygons
                    map.current?.addLayer({
                        id: `${sourceId}-${layerName}-fill`,
                        type: 'fill',
                        source: sourceId,
                        'source-layer': layerName,
                        paint: {
                            'fill-color': color,
                            'fill-opacity': 0.4,
                            'fill-outline-color': color // simple outline
                        }
                    });

                    // Lines
                    map.current?.addLayer({
                        id: `${sourceId}-${layerName}-line`,
                        type: 'line',
                        source: sourceId,
                        'source-layer': layerName,
                        paint: {
                            'line-color': color,
                            'line-width': 2
                        }
                    });

                    // Points
                    map.current?.addLayer({
                        id: `${sourceId}-${layerName}-point`,
                        type: 'circle',
                        source: sourceId,
                        'source-layer': layerName,
                        paint: {
                            'circle-color': color,
                            'circle-radius': 4
                        }
                    });
                });
            }
        }
        
        // Fit bounds if bbox is provided and valid
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

    }, [data, bbox, styleLoaded, type, url, layers]);

    return <div ref={mapContainer} className="w-full h-[400px] rounded-md border" />;
}
