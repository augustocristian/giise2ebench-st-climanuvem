import { BackendService } from '@/src/services/BackendService';
import { Logger } from '@/src/services/LoggerService';
import { GUEST_DEMO_HISTORY } from '@/src/services/mockData';

export interface AnalysisHistoryItem {
  id: string;
  status: 'completed' | 'analyzing' | 'cancelled';
  date: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  imageUrl?: string;
  results?: {
    cloudTypes: string[];
    cloudDetails?: { type: string; box: [number, number, number, number] | null }[];
    forecast: string;
    warnings: { text: string; level: number }[];
  };
}

export class AnalysisService {
  static async uploadImage(imageUri: string, locationStr: string, latitude?: number, longitude?: number, fcmToken?: string, includeExplainability: boolean = false) {
    return BackendService.uploadImage(imageUri, locationStr, latitude, longitude, fcmToken, includeExplainability);
  }

  static async deleteAnalysis(analysisId: string) {
    return BackendService.deleteAnalysis(analysisId);
  }

  static async cancelAnalysis(analysisId: string) {
    return BackendService.cancelAnalysis(analysisId);
  }

  static async getHistory(isLoggedIn: boolean): Promise<AnalysisHistoryItem[]> {
    // Keep a short delay so the loading state is visible and does not flash.
    await new Promise((resolve) => setTimeout(resolve, 1000));

    if (isLoggedIn) {
      try {
        const history = await BackendService.getAnalysisHistory();
        return history as AnalysisHistoryItem[];
      } catch (error) {
        Logger.error('Error al obtener el historial de análisis', error);
        return [];
      }
    }
    return GUEST_DEMO_HISTORY;
  }
}
