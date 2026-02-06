import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, CheckCircle, Loader2, UploadCloud } from 'lucide-react';
import { useState } from 'react';
import { MapPreview } from './components/MapPreview';
import type { FileMetadata } from './services/duckdb';
import { analyzeFile } from './services/duckdb';

export function LoadDataView() {
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [metadata, setMetadata] = useState<FileMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [targetSchema, setTargetSchema] = useState('geodata');
  const [tableName, setTableName] = useState('');

  // Helper to construct GeoJSON from sample (Now simpler as data is flattened)
  const getPreviewData = () => {
    if (!metadata || !metadata.sample) return null;
    
    const rows = metadata.sample as any[];
    
    // If rows have 'geometry' (flattened GeoJSON)
    if (rows.length > 0 && rows[0].geometry) {
        return {
            type: 'FeatureCollection',
            features: rows.map(r => ({
                type: 'Feature',
                geometry: r.geometry,
                properties: Object.fromEntries(
                    Object.entries(r).filter(([k]) => k !== 'geometry')
                )
            }))
        };
    }
    return null; 
  };
  
  const previewData = getPreviewData();

  const processFile = async (file: File) => {
      setFile(file);
      setAnalyzing(true);
      setError(null);
      setMetadata(null);
      
      const cleanName = file.name.split('.')[0].replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
      setTableName(cleanName);

      try {
        const meta = await analyzeFile(file);
        setMetadata(meta);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Failed to analyze file.");
      } finally {
        setAnalyzing(false);
      }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };
  
  const [isDragging, setIsDragging] = useState(false);

  const onDragOver = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(true);
  };
  
  const onDragLeave = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
  };
  
  const onDrop = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          processFile(e.dataTransfer.files[0]);
      }
  };

  const handleUpload = async () => {
      alert(`Ready to upload ${file?.name} to ${targetSchema}.${tableName}`);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Import Data</h2>
        <p className="text-muted-foreground">
          Upload geospatial files to your Canopy database.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
         {/* Upload Card */}
        <Card>
          <CardHeader>
            <CardTitle>Source File</CardTitle>
            <CardDescription>Select a file to analyze.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div 
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                className={`
                border-2 border-dashed rounded-lg p-10 text-center transition-colors
                ${isDragging ? 'border-primary bg-primary/10' : 'border-muted-foreground/25 hover:bg-muted/50'}
                ${file ? 'border-primary bg-muted/20' : ''}
            `}>
                <input 
                    type="file" 
                    id="file-upload" 
                    className="hidden" 
                    onChange={handleFileChange}
                    accept=".csv,.json,.geojson,.parquet" 
                />
                <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center justify-center gap-2">
                    {analyzing ? (
                        <Loader2 className="h-10 w-10 text-primary animate-spin" />
                    ) : (
                        <UploadCloud className={`h-10 w-10 ${file ? 'text-primary' : 'text-muted-foreground'}`} />
                    )}
                    <span className="text-sm font-medium">
                        {file ? file.name : "Click to select or drag file here"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                        Supported: GeoJSON, CSV, Parquet components
                    </span>
                </label>
            </div>

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {metadata && (
                <Alert className="bg-green-500/10 text-green-600 border-green-500/20">
                    <CheckCircle className="h-4 w-4" />
                    <AlertTitle>Analysis Complete</AlertTitle>
                    <AlertDescription>
                        <div className="flex flex-col gap-1 mt-1">
                            <span>Detected <strong>{metadata.format.toUpperCase()}</strong> with <strong>{metadata.rowCount.toLocaleString()}</strong> rows.</span>
                            {metadata.crs && <span className="text-xs opacity-80 font-mono">CRS: {metadata.crs}</span>}
                            <div className="text-[10px] opacity-70 font-mono mt-1 border-t pt-1">
                                <p>BBox: {JSON.stringify(metadata.bbox.map(x => Math.round(x*100)/100))}</p>
                            </div>
                        </div>
                    </AlertDescription>
                </Alert>
            )}
          </CardContent>
        </Card>

        {/* Settings Card */}
        <Card className={!metadata ? 'opacity-50 pointer-events-none' : ''}>
           <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Target settings in PostGIS.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
             <div className="space-y-2">
                <Label>Target Schema</Label>
                <Input value={targetSchema} onChange={e => setTargetSchema(e.target.value)} />
             </div>
             <div className="space-y-2">
                <Label>Table Name</Label>
                <Input value={tableName} onChange={e => setTableName(e.target.value)} />
             </div>
             
             <div className="pt-4">
                 <Button className="w-full" onClick={handleUpload} disabled={!metadata || analyzing}>
                    {analyzing ? 'Analyzing...' : 'Start Import'}
                 </Button>
             </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Preview Section */}
      {metadata && (
        <div className="space-y-6">
            {/* Map Preview */}
             {previewData && (
                <Card>
                    <CardHeader>
                        <CardTitle>Map Preview</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0 overflow-hidden rounded-b-lg">
                        <MapPreview data={previewData} bbox={metadata.bbox} />
                    </CardContent>
                </Card>
             )}

            {/* Data Table Preview */}
            <Card>
                <CardHeader>
                    <CardTitle>Data Preview</CardTitle>
                    <CardDescription>First 5 rows of the dataset.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-muted/50 text-muted-foreground font-medium">
                                <tr>
                                    {metadata.columns.map(c => (
                                        <th key={c.name} className="p-3 whitespace-nowrap">{c.name} <span className="text-xs opacity-50">({c.type})</span></th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                                {(metadata.sample as any[]).map((row, i) => (
                                    <tr key={i} className="border-t">
                                        {metadata.columns.map(c => (
                                            <td key={c.name} className="p-3 max-w-[200px] truncate">
                                                {typeof row[c.name] === 'object' ? JSON.stringify(row[c.name]) : String(row[c.name])}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
      )}

    </div>
  );
}
