import * as duckdb from '@duckdb/duckdb-wasm';
import eh_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url';
import mvp_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url';
import duckdb_eh_wasm from '@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url';
import duckdb_wasm from '@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url';

export interface FileMetadata {
    fileName: string;
    format: string;
    geometryType: string;
    rowCount: number;
    columns: { name: string; type: string }[];
    bbox: number[];
    sample: unknown;
    crs?: string;
}

const MANUAL_BUNDLES: duckdb.DuckDBBundles = {
    mvp: {
        mainModule: duckdb_wasm,
        mainWorker: mvp_worker,
    },
    eh: {
        mainModule: duckdb_eh_wasm,
        mainWorker: eh_worker,
    },
};

let db: duckdb.AsyncDuckDB | null = null;

export async function initDuckDB() {
    if (db) return db;
    
    // Select bundle based on browser support
    const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);
    const worker = new Worker(bundle.mainWorker!);
    const logger = new duckdb.ConsoleLogger();
    db = new duckdb.AsyncDuckDB(logger, worker);
    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    return db;
}

export async function analyzeFile(file: File): Promise<FileMetadata> {
    const db = await initDuckDB();
    const conn = await db.connect();
    
    const tableName = `import_${Math.random().toString(36).substring(7)}`;
    const fileName = file.name;
    
    try {
        await db.registerFileHandle(fileName, file, duckdb.DuckDBDataProtocol.BROWSER_FILEREADER, true);
        
        // Detect format and create view
        // Using ST_Read for geospatial support if spatial extension loads, but for now standard read
        // duckdb-wasm spatial extension might need explicit loading.
        // For prototype, we assume Parquet/CSV/JSON or use spatial extension if available.
        // Wait, standard duckdb-wasm has spatial? Not by default. 
        // We will try standard loading first.
        
        let fileType = 'unknown';
        if (fileName.endsWith('.csv')) fileType = 'csv';
        if (fileName.endsWith('.json') || fileName.endsWith('.geojson')) fileType = 'json';
        if (fileName.endsWith('.parquet')) fileType = 'parquet';
        
        let rowCount = 0;
        let columns: { name: string; type: string }[] = [];
        let sampleRows: any[] = [];
        let geometryType = 'Unknown';
        let bbox = [0, 0, 0, 0];
        let crs = 'EPSG:4326'; // Default for GeoJSON

        if (fileType === 'json') {
             // Load JSON into a temporary table first to inspect structure
             await conn.query(`CREATE TABLE raw_json AS SELECT * FROM read_json_auto('${fileName}')`);
             
             // Check if it looks like a FeatureCollection
             const schemaRaw = await conn.query(`DESCRIBE raw_json`);
             const hasFeatures = schemaRaw.toArray().some((c: any) => c.column_name === 'features');

             if (hasFeatures) {
                 // It's a FeatureCollection.
                 // Step 1: Unnest features into a temp view to inspect structure
                 const tempView = `temp_features_${Math.random().toString(36).substring(7)}`;
                 await conn.query(`CREATE VIEW ${tempView} AS SELECT unnest(features) as feature FROM raw_json`);
                 
                 // Step 2: Describe the temp view to see what 'feature' looks like (struct?)
                 await conn.query(`DESCRIBE ${tempView}`);
                 // schemaTemp typically has column_name='feature', type='STRUCT(...)'
                 // But we can check if we can select feature.properties
                 
                 // We can try to bind a query to check existence, or just check the type string.
                 // Simpler: Try to CREATE the final view with properties. If it fails, fallback.
                 
                 try {
                     // Try to flatten properties
                     await conn.query(`CREATE VIEW ${tableName} AS 
                        SELECT feature.properties.*, feature.geometry 
                        FROM ${tempView}`);
                 } catch (e) {
                     console.warn("Could not flatten properties, falling back to raw feature", e);
                     // Fallback: Just select the feature struct and geometry if possible, or just feature
                     // If geometry is missing from struct, this might also fail.
                     
                     // Try selecting just feature.* (expands the feature struct)
                     try {
                        await conn.query(`CREATE VIEW ${tableName} AS SELECT feature.* FROM ${tempView}`);
                     } catch (e2) {
                         // Fallback to raw features array if all else fails
                         console.warn("Could not expand feature, reverting to raw", e2);
                         await conn.query(`DROP VIEW IF EXISTS ${tempView}`);
                         await conn.query(`CREATE VIEW ${tableName} AS SELECT * FROM raw_json`);
                     }
                 }
                 
                 // Cleanup temp view if we successfully created tableName (or if we fell back to raw_json which doesn't use it)
                 // Note: If tableName depends on tempView, we CANNOT drop tempView yet if it's a VIEW (logical dependency).
                 // Actually, DuckDB views are macro-ish.
                 // Safe to leave tempView for the session or drop it if we materialized.
                 // We'll leave it for now, it's session scoped.
                 
                 // Get count
                 const countRes = await conn.query(`SELECT json_array_length(features) as c FROM raw_json`);
                 rowCount = Number(countRes.toArray()[0].c);
                 
                 // Get Sample
                 const sampleRes = await conn.query(`SELECT * FROM ${tableName} LIMIT 10`);
                 // Force strict JSON serialization to strip Arrow 'StructRow' wrappers
                 sampleRows = sampleRes.toArray().map((r: any) => JSON.parse(JSON.stringify(r.toJSON())));
                 
                 // Get Schema from View
                 const schemaView = await conn.query(`DESCRIBE ${tableName}`);
                 columns = schemaView.toArray().map((r: any) => ({ name: r.column_name, type: r.column_type }));

                 // Try to determine geometry type from sample
                 if (sampleRows.length > 0 && sampleRows[0].geometry) {
                    geometryType = sampleRows[0].geometry.type;
                 }
                 
                 // Try to get CRS from raw_json 
                 // (Naive check for 'crs' property at root)
                 const hasCrs = schemaRaw.toArray().some((c: any) => c.column_name === 'crs');
                 if (hasCrs) {
                     const crsRes = await conn.query(`SELECT crs FROM raw_json`);
                     // Inspect safely
                     const crsRow = crsRes.toArray()[0]; 
                     // Arrow row might need access
                     const crsObj = crsRow['crs'] || (crsRow.toJSON ? crsRow.toJSON().crs : null);
                     
                     if (crsObj && crsObj.properties && crsObj.properties.name) {
                         crs = crsObj.properties.name;
                     }
                 }

             } else {
                 // Plain JSON array or object
                 await conn.query(`CREATE VIEW ${tableName} AS SELECT * FROM raw_json`);
                 const countRes = await conn.query(`SELECT count(*) as c FROM ${tableName}`);
                 rowCount = Number(countRes.toArray()[0].c);
                 
                 const sampleRes = await conn.query(`SELECT * FROM ${tableName} LIMIT 10`);
                 sampleRows = sampleRes.toArray().map((r: any) => JSON.parse(JSON.stringify(r.toJSON())));
                 
                 const schemaView = await conn.query(`DESCRIBE ${tableName}`);
                 columns = schemaView.toArray().map((r: any) => ({ name: r.column_name, type: r.column_type }));
             }

        } else {
            // CSV / Parquet
            if (fileType === 'csv') {
                await conn.query(`CREATE VIEW ${tableName} AS SELECT * FROM read_csv_auto('${fileName}')`);
            } else if (fileType === 'parquet') {
                await conn.query(`CREATE VIEW ${tableName} AS SELECT * FROM read_parquet('${fileName}')`);
            }
            
            const countRes = await conn.query(`SELECT count(*) as c FROM ${tableName}`);
            rowCount = Number(countRes.toArray()[0].c);
            
            const sampleRes = await conn.query(`SELECT * FROM ${tableName} LIMIT 10`);
            sampleRows = sampleRes.toArray().map((r: any) => JSON.parse(JSON.stringify(r.toJSON())));
            
            const schemaView = await conn.query(`DESCRIBE ${tableName}`);
            columns = schemaView.toArray().map((r: any) => ({ name: r.column_name, type: r.column_type }));
        }

        // Calculate BBox from sample
        // Helper to recursively extract numbers from coordinates
        const flattenCoords = (coords: any): number[] => {
            if (!Array.isArray(coords)) return [];
            if (coords.length === 0) return [];
            // If it's a number, wrap it (shouldn't happen with correct GeoJSON if starting from array)
            if (typeof coords[0] === 'number') return coords;
            return coords.reduce((acc, val) => acc.concat(flattenCoords(val)), []);
        };

        const geomCol = columns.find(c => c.name === 'geometry' || c.name === 'wkb_geometry');
        if (geomCol && sampleRows.length > 0) {
             let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
             sampleRows.forEach(row => {
                 const g = row[geomCol.name];
                 if (g && g.coordinates) {
                     // Flatten coordinates to find extent safely
                     const flat = flattenCoords(g.coordinates);
                     for (let i = 0; i < flat.length; i += 2) {
                         const x = flat[i];
                         const y = flat[i+1];
                         if (x < minX) minX = x;
                         if (y < minY) minY = y;
                         if (x > maxX) maxX = x;
                         if (y > maxY) maxY = y;
                     }
                 }
             });
             if (minX !== Infinity) {
                 bbox = [minX, minY, maxX, maxY];
             }
        }
        
        return {
            fileName: file.name,
            format: fileType,
            geometryType: geometryType,
            rowCount: rowCount,
            columns: columns,
            bbox: bbox,
            sample: sampleRows,
            crs: crs
        };

    } finally {
        await conn.close();
        // keep DB alive for reuse
    }
}
