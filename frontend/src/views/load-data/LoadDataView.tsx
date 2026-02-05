
export function LoadDataView() {
  return (
    <div className="p-8">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Import Data</h2>
          <p className="text-muted-foreground">
            Import geographical data into your project.
          </p>
        </div>
      </div>
      <div className="mt-8">
        <div className="rounded-md border border-dashed p-8 text-center animate-in fade-in-50">
          <div className="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">
            <h3 className="mt-4 text-lg font-semibold">No data imported yet</h3>
            <p className="mb-4 mt-2 text-sm text-muted-foreground">
              Feature coming soon.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
