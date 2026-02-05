import { MainLayout } from '@/components/layout/MainLayout';
import { EditorView } from '@/views/editor/EditorView';
import { LoadDataView } from '@/views/load-data/LoadDataView';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/editor" replace />} />
          <Route path="editor" element={<EditorView />} />
          <Route path="load-data" element={<LoadDataView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
