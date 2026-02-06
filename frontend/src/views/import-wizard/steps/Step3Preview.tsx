import { useState } from 'react';
import { MapPreview } from '../../load-data/components/MapPreview';
import { StepNavigation } from '../components/StepNavigation';
import { useImportStore } from '../store';
// We need to slightly adapt MapPreview or pass correct props.
// MapPreview currently expects GeoJSON 'data' prop.
// For PMTiles, we need to pass a URL and type.
// Let's modify MapPreview slightly to accept 'sourceType' and 'url' logic, OR
// We can handle the distinction here and render a adapted Map.

// For speed, let's reuse MapPreview but we might need to patch it to support 'url' source or 'pmtiles'.
// Currently MapPreview takes `data: any` (GeoJSON).
// We should update MapPreview to support PMTiles.

export function Step3Preview() {
  const { metadata, sourceType, remoteUrl, file, prevStep } = useImportStore();
  const [isImporting, setIsImporting] = useState(false);

  const handleImport = async () => {
    setIsImporting(true);
    try {
        if (sourceType === 'local' && file) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('table_name', file.name.split('.')[0].replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()); 
            formData.append('schema', 'public'); // Default to public or make configurable

            const res = await fetch('/api/import', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail || "Upload failed");
            }
            // Success
            alert("Import started successfully! (Task ID: " + (await res.json()).task_id + ")");
        } else {
             // Remote Import Logic
             await new Promise(resolve => setTimeout(resolve, 1000));
             alert("Remote import via URL is not yet supported by the backend.");
        }
    } catch (err: any) {
        alert("Error: " + err.message);
    } finally {
        setIsImporting(false);
    }
  };

  // Prepare data for map
  // If local, we have previewData (GeoJSON) from Step 1 analysis? 
  // Wait, Step 1 analysis in 'duckdb.ts' returns 'sample'.
  // We need the full geojson or a sample geojson for preview?
  // Use 'metadata.sample' if it's geojson-like rows?
  
  // Actually, 'metadata.sample' is an array of rows. We need to convert back to FeatureCollection for MapPreview.
  const localGeoJSON = metadata?.sample ? {
      type: "FeatureCollection",
      features: (metadata.sample as any[]).map((row: any) => ({
          type: "Feature",
          properties: row, // Flattened properties are in row
          geometry: row.geometry
      }))
  } : null;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-500">
        <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold tracking-tight">Preview & Import</h2>
            <p className="text-muted-foreground">Visualize final data and confirm import.</p>
        </div>

        <div className="border rounded-lg overflow-hidden h-[400px]">
             {sourceType === 'local' && localGeoJSON && (
                 <MapPreview 
                    data={localGeoJSON} 
                    bbox={metadata?.bbox} 
                 />
             )}
             
             {sourceType === 'remote' && remoteUrl && (
                  <MapPreview 
                    type="pmtiles"
                    url={remoteUrl}
                    bbox={metadata?.bbox}
                    layers={metadata?.layers}
                 />
             )}
        </div>

        <StepNavigation 
            onBack={prevStep}
            onNext={handleImport}
            isLastStep={true}
            isNectProcessing={isImporting}
        />
    </div>
  );
}
