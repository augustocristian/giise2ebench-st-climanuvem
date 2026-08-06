import type { AnalysisHistoryItem } from '@/src/services/AnalysisService';

export const GUEST_DEMO_HISTORY: AnalysisHistoryItem[] = [
  {
    id: 'temp-1',
    status: 'analyzing',
    date: new Date().toISOString(),
    location: 'Ubicación actual',
    imageUrl: 'https://picsum.photos/id/1015/800/600',
  },
];
