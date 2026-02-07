import { create } from 'zustand';
import type { FileMetadata } from '../load-data/services/duckdb';

export type SourceType = 'local' | 'remote';

export interface ImportWizardState {
  step: number;
  sourceType: SourceType;
  file: File | null;
  remoteUrl: string;
  metadata: FileMetadata | null;
  tableName: string;
  
  // Actions
  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  setSourceType: (type: SourceType) => void;
  setFile: (file: File | null) => void;
  setRemoteUrl: (url: string) => void;
  setMetadata: (metadata: FileMetadata | null) => void;
  setTableName: (name: string) => void;
  reset: () => void;
}

export const useImportStore = create<ImportWizardState>((set) => ({
  step: 1, // 1-based index (1: Source, 2: Metadata, 3: Preview)
  sourceType: 'local',
  file: null,
  remoteUrl: '',
  metadata: null,
  tableName: '',

  setStep: (step) => set({ step }),
  nextStep: () => set((state) => ({ step: Math.min(state.step + 1, 3) })),
  prevStep: () => set((state) => ({ step: Math.max(state.step - 1, 1) })),
  setSourceType: (sourceType) => set({ sourceType }),
  setFile: (file) => set({ 
      file,
      tableName: file ? file.name.split('.')[0].replace(/[^a-zA-Z0-9]/g, '_').toLowerCase() : ''
  }),
  setRemoteUrl: (remoteUrl) => set({ remoteUrl }),
  setMetadata: (metadata) => set({ metadata }),
  setTableName: (tableName) => set({ tableName }),
  
  reset: () => set({
    step: 1,
    sourceType: 'local',
    file: null,
    remoteUrl: '',
    metadata: null,
    tableName: ''
  })
}));
