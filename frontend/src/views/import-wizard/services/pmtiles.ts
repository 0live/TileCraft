import { PMTiles } from 'pmtiles';

export interface PMTilesMetadata {
    header: any;
    metadata: any;
    layers: string[];
}

export async function inspectPMTiles(url: string): Promise<PMTilesMetadata> {
    const p = new PMTiles(url);
    const header = await p.getHeader();
    const metadata = await p.getMetadata() as any;
    console.log(metadata);
    // Extract vector layers if present
    let layers: string[] = [];
    if (metadata.vector_layers) {
        layers = metadata.vector_layers.map((l: any) => l.id);
    } else if (metadata.tilestats && metadata.tilestats.layers) {
        // PMTiles v3 (tilestats)
        layers = metadata.tilestats.layers.map((l: any) => l.layer);
    }

    return {
        header: header,
        metadata: metadata,
        layers: layers
    };
}
