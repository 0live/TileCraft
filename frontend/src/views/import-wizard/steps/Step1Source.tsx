import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, FileUp, Globe, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { analyzeFile } from '../../load-data/services/duckdb';
import { StepNavigation } from '../components/StepNavigation';
import { inspectPMTiles } from '../services/pmtiles';
import { useImportStore } from '../store';

export function Step1Source() {
   
  const { 
    sourceType, setSourceType, 
    file, setFile, 
    remoteUrl, setRemoteUrl, 
    setMetadata, 
    nextStep
  } = useImportStore();
   

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);


  // -- Local File Handlers --
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
    if (e.dataTransfer.files?.[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };
  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setIsAnalyzing(true);
    setMetadata(null); // Reset prev metadata
    
    try {
      const meta = await analyzeFile(selectedFile);
      setMetadata(meta);
      // Removed auto-next to allow user to see success first? 
      // Actually, standard wizard flow usually validates then either stays or allows next.
      // We'll behave like: Analysis success enables 'Next' button.
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to analyze file.");
      setFile(null); // Reset if failed
    } finally {
      setIsAnalyzing(false);
    }
  };

  // -- Remote URL Handlers --
  const handleUrlValidation = async () => {
    if (!remoteUrl) return;
    setIsAnalyzing(true);
    setError(null);
    
    try {
        const info = await inspectPMTiles(remoteUrl);
        // Normalize PMTiles metadata to common format
        setMetadata({
            fileName: remoteUrl.split('/').pop() || 'remote.pmtiles',
            format: 'pmtiles',
            geometryType: 'Vector Tiles',
            rowCount: 0, // Not applicable
            columns: [], // Not easily accessible without tile parsing
            bbox: [info.header.minLon, info.header.minLat, info.header.maxLon, info.header.maxLat],
            sample: null,
            crs: 'EPSG:4326', // Web Mercator usually, but strictly 3857 map wise
            layers: info.layers
        } as any); // Using 'any' cast for now as FileMetadata might not perfectly match yet
    } catch (e: any) {
        console.error(e);
        setError("Failed to access PMTiles: " + e.message);
        setMetadata(null);
    } finally {
        setIsAnalyzing(false);
    }
  };

  // -- Next Navigation --
  const onNext = () => {
    nextStep();
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-semibold tracking-tight">Select Data Source</h2>
        <p className="text-muted-foreground">Upload a local file or connect to a remote PMTiles source.</p>
      </div>

      <Tabs 
        defaultValue={sourceType} 
        onValueChange={(v: string) => {
            setSourceType(v as any);
            setError(null);
        }} 
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="local"><FileUp className="w-4 h-4 mr-2"/> Local File</TabsTrigger>
          <TabsTrigger value="remote"><Globe className="w-4 h-4 mr-2"/> Remote PMTiles</TabsTrigger>
        </TabsList>

        <TabsContent value="local" className="mt-6 space-y-4">
          <div 
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className={`
                border-2 border-dashed rounded-lg p-10 text-center transition-all duration-200 cursor-pointer
                ${isDragging ? 'border-primary bg-primary/5 scale-[1.01]' : 'border-muted-foreground/25 hover:bg-muted/50'}
                ${file ? 'border-primary bg-primary/5' : ''}
            `}
            onClick={() => document.getElementById('file-upload')?.click()}
          >
            <input 
                id="file-upload" 
                type="file" 
                className="hidden" 
                onChange={onFileChange}
                accept=".json,.geojson,.csv,.parquet"
            />
            
            {isAnalyzing ? (
                <div className="flex flex-col items-center gap-4 py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">Analyzing file structure...</p>
                </div>
            ) : file ? (
                <div className="py-4">
                    <div className="bg-primary/10 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                        <FileUp className="h-6 w-6 text-primary" />
                    </div>
                    <p className="font-medium text-lg">{file.name}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <p className="text-xs text-primary mt-4 font-medium">Click or Drop to replace</p>
                </div>
            ) : (
                <div className="py-8">
                     <div className="bg-muted w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                        <FileUp className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="font-medium text-lg">Drag & Drop or Click to Upload</p>
                    <p className="text-sm text-muted-foreground mt-2">
                        Supports GeoJSON, CSV, Parquet, JSON
                    </p>
                </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="remote" className="mt-6 space-y-4">
            <div className="space-y-2">
                <Label htmlFor="url">PMTiles URL</Label>
                <div className="flex gap-2">
                    <Input 
                        id="url" 
                        placeholder="https://example.com/data.pmtiles" 
                        value={remoteUrl}
                        onChange={(e) => {
                            setRemoteUrl(e.target.value);
                            setMetadata(null); // Reset when URL changes
                        }}
                    />
                    <button 
                        onClick={handleUrlValidation}
                        disabled={!remoteUrl || isAnalyzing}
                        className="bg-primary text-primary-foreground h-9 px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                    >
                        {isAnalyzing ? <Loader2 className="w-4 h-4 animate-spin"/> : "Check"}
                    </button>
                </div>
                <p className="text-[0.8rem] text-muted-foreground">
                    Enter a publicly accessible HTTPS URL to a PMTiles archive.
                </p>
            </div>
            
            {/* Show success indicator for remote */}
            {useImportStore.getState().metadata && sourceType === 'remote' && (
                 <Alert className="bg-green-500/10 border-green-500/50 text-green-700 dark:text-green-400">
                    <AlertTitle>Valid PMTiles Archive</AlertTitle>
                    <AlertDescription>
                        Found {useImportStore.getState().metadata?.layers?.length || 0} vector layers.
                    </AlertDescription>
                </Alert>
            )}
        </TabsContent>
      </Tabs>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <StepNavigation 
        canBack={false}
        canNext={!!useImportStore.getState().metadata}
        onNext={onNext}
        isNectProcessing={isAnalyzing}
      />
    </div>
  );
}
