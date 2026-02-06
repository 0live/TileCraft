import { create } from 'zustand';
import type { FileMetadata } from '../load-data/services/duckdb';

export type SourceType = 'local' | 'remote';

export interface ImportWizardState {
  step: number;
  sourceType: SourceType;
  file: File | null;
  remoteUrl: string;
  metadata: FileMetadata | null;
  
  // Actions
  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  setSourceType: (type: SourceType) => void;
  setFile: (file: File | null) => void;
  setRemoteUrl: (url: string) => void;
  setMetadata: (metadata: FileMetadata | null) => void;
  reset: () => void;
}

export const useImportStore = create<ImportWizardState>((set) => ({
  step: 1, // 1-based index (1: Source, 2: Metadata, 3: Preview)
  sourceType: 'local',
  file: null,
  remoteUrl: '',
  metadata: null,

  setStep: (step) => set({ step }),
  nextStep: () => set((state) => ({ step: Math.min(state.step + 1, 3) })),
  prevStep: () => set((state) => ({ step: Math.max(state.step - 1, 1) })),
  setSourceType: (sourceType) => set({ sourceType }),
  setFile: (file) => set({ file }),
  setRemoteUrl: (remoteUrl) => set({ remoteUrl }),
  setMetadata: (metadata) => set({ metadata }),
  
  reset: () => set({
    step: 1,
    sourceType: 'local',
    file: null,
    remoteUrl: '',
    metadata: null
  })
}));
