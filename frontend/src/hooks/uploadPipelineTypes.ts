import { BulletPointExpandResponse as ExpandedBulletResult, UploadResponse } from '../services/apiService';

export type JobStatus =
  | { stage: 'idle' }
  | { stage: 'uploading' | 'preprocessing' | 'saving_output' }
  | { stage: 'transcribing'; current: number; total: number }
  | { stage: 'done'; result: UploadResponse }
  | { stage: 'error'; error: string };

export type NestedExpansions = {
  [bulletKey: string]: {
    expansion: ExpandedBulletResult;
    subExpansions?: NestedExpansions;
  };
};

export type BulletExpansion = {
  expansion: ExpandedBulletResult;
  subExpansions?: NestedExpansions;
};
