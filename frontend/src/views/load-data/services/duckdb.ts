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
    layers?: string[];
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

const replacer = (_key: string, value: any) => typeof value === 'bigint' ? Number(value) : value;

export async function analyzeFile(file: File): Promise<FileMetadata> {
    const dbInstance = await initDuckDB();
    const conn = await dbInstance.connect();
    
    const tableName = `import_${Math.random().toString(36).substring(7)}`;
    const fileName = file.name;
    
    let tempViewName: string | null = null;

    try {
        await dbInstance.registerFileHandle(fileName, file, duckdb.DuckDBDataProtocol.BROWSER_FILEREADER, true);
        
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
             console.log(`Loading JSON file: ${file.name}, size: ${file.size}`);
             // Load JSON into a temporary table first to inspect structure
             // Set dynamic max object size: at least 32MB, or 4x file size (upto 2GB cap)
             const dynamicMaxSize = Math.min(2 * 1024 * 1024 * 1024, Math.max(33554432, file.size * 4));
             console.log(`Using maximum_object_size: ${dynamicMaxSize}`);

             await conn.query(`CREATE TABLE raw_json AS SELECT * FROM read_json_auto('${fileName}', maximum_object_size=${dynamicMaxSize})`);
             
             // Check if it looks like a FeatureCollection
             console.log("JSON loaded, describing...");
             const schemaRaw = await conn.query(`DESCRIBE raw_json`);
             const hasFeatures = schemaRaw.toArray().some((c: any) => c.column_name === 'features');

             if (hasFeatures) {
                 // It's a FeatureCollection.
                 // Step 1: Unnest features into a temp view to inspect structure
                 const tempView = `temp_features_${Math.random().toString(36).substring(7)}`;
                 tempViewName = tempView;
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
                         tempViewName = null; // Already dropped
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
                 sampleRows = sampleRes.toArray().map((r: any) => JSON.parse(JSON.stringify(r.toJSON(), replacer)));
                 
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
                 console.log("Not a FeatureCollection, treating as standard JSON/array");
                 // Plain JSON array or object
                 await conn.query(`CREATE VIEW ${tableName} AS SELECT * FROM raw_json`);
                 const countRes = await conn.query(`SELECT count(*) as c FROM ${tableName}`);
                 rowCount = Number(countRes.toArray()[0].c);
                 
                 const sampleRes = await conn.query(`SELECT * FROM ${tableName} LIMIT 10`);
                 sampleRows = sampleRes.toArray().map((r: any) => JSON.parse(JSON.stringify(r.toJSON(), replacer)));
                 
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
            sampleRows = sampleRes.toArray().map((r: any) => JSON.parse(JSON.stringify(r.toJSON(), replacer)));
            
            const schemaView = await conn.query(`DESCRIBE ${tableName}`);
            columns = schemaView.toArray().map((r: any) => ({ name: r.column_name, type: r.column_type }));
        }

        // Calculate BBox from sample
        // Helper to recursively extract numbers from coordinates (Iterative/In-place to avoid OOM)
        const flattenCoords = (coords: any, result: number[] = []) => {
            if (!coords) return result;
            if (typeof coords[0] === 'number') {
                for (let i = 0; i < coords.length; i++) {
                    result.push(coords[i]);
                }
                return result;
            }
            if (Array.isArray(coords)) {
                for (let i = 0; i < coords.length; i++) {
                    flattenCoords(coords[i], result);
                }
            }
            return result;
        };

        const geomCol = columns.find(c => c.name === 'geometry' || c.name === 'wkb_geometry');
        if (geomCol && sampleRows.length > 0) {
             console.log("Analyzing BBox...");
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
             console.log("BBox calculated:", bbox);
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
        // Cleanup resources to prevent memory leaks in WASM
        try {
            await conn.query(`DROP VIEW IF EXISTS ${tableName}`);
            await conn.query(`DROP TABLE IF EXISTS raw_json`);
            if (tempViewName) {
                await conn.query(`DROP VIEW IF EXISTS ${tempViewName}`);
            }
            await conn.close();
        } catch (e) {
            console.warn("Error during cleanup", e);
        }

        // AGGRESSIVE CLEANUP: Terminate the worker to free WASM memory
        // This is necessary because loading large files sequentially causes OOM even with drops.
        if (db) {
            await db.terminate();
            db = null; // Reset global variable
        }
    }
}
