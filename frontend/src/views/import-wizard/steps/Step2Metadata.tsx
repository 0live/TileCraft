import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Database, Layers, MapPin } from 'lucide-react';
import { StepNavigation } from '../components/StepNavigation';
import { useImportStore } from '../store';

export function Step2Metadata() {
  const { metadata, setMetadata, nextStep, prevStep } = useImportStore();

  if (!metadata) return <div>No metadata loaded.</div>;

  const handleCrsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMetadata({ ...metadata, crs: e.target.value });
  };

  const isPMTiles = metadata.format === 'pmtiles';

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-500">
        <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold tracking-tight">Review Metadata</h2>
            <p className="text-muted-foreground">Verify the detected information before proceeding.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                        <Database className="w-4 h-4 mr-2"/> Format
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{metadata.format.toUpperCase()}</div>
                    <p className="text-xs text-muted-foreground">{metadata.fileName}</p>
                </CardContent>
            </Card>
            
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                        <MapPin className="w-4 h-4 mr-2"/> Projection (CRS)
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {/* Editable CRS */}
                    <Input 
                        value={metadata.crs || ''} 
                        onChange={handleCrsChange} 
                        className="h-8 text-lg font-bold px-2 -mx-2 w-full border-dashed border-transparent hover:border-input focus:border-input"
                    />
                     <p className="text-xs text-muted-foreground pt-1">
                        Detected or Default (EPSG)
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                        <Layers className="w-4 h-4 mr-2"/> Content
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">
                        {isPMTiles 
                            ? `${metadata.layers?.length || 0} Layers` 
                            : `${metadata.rowCount.toLocaleString()} Rows`
                        }
                    </div>
                    <p className="text-xs text-muted-foreground">
                        {metadata.geometryType || 'Unknown Geometry'}
                    </p>
                </CardContent>
            </Card>
        </div>

        {/* Detailed Schema or Layer List */}
        <Card className="h-[300px] flex flex-col">
            <CardHeader className="border-b bg-muted/30 py-3">
                 <CardTitle className="text-sm font-medium">
                    {isPMTiles ? 'Vector Layers' : 'Attribute Schema'}
                 </CardTitle>
            </CardHeader>
            <ScrollArea className="flex-1">
                {isPMTiles ? (
                    <div className="p-4 grid gap-2">
                        {metadata.layers?.map(layer => (
                            <div key={layer} className="flex items-center p-2 rounded-md border bg-card">
                                <Layers className="w-4 h-4 mr-3 text-muted-foreground"/>
                                <span className="font-mono text-sm">{layer}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[200px]">Column Name</TableHead>
                                <TableHead>Type</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {metadata.columns.map((col) => (
                                <TableRow key={col.name}>
                                    <TableCell className="font-medium font-mono text-xs">{col.name}</TableCell>
                                    <TableCell>
                                        <Badge variant="outline" className="font-mono text-[10px]">{col.type}</Badge>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </ScrollArea>
        </Card>

        <StepNavigation 
            onBack={prevStep}
            onNext={nextStep}
        />
    </div>
  );
}
