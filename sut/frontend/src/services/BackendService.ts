import { auth } from '@/src/config/firebaseConfig';
import { Logger } from '@/src/services/LoggerService';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const IMAGE_TOO_LARGE_CODE = 'IMAGE_TOO_LARGE_MAX_5MB';
const DEFAULT_TIMEOUT_MS = 10000;
const MUTATION_TIMEOUT_MS = 15000;

const backendUrl = (path: string) => `${BACKEND_URL}${path}`;

const logBackendRequest = (method: string, path: string) => {
  Logger.info('Backend request', { method, url: backendUrl(path) });
};

const isNetworkError = (error: any): boolean => {
  const message = String(error?.message || '');
  return error instanceof TypeError || message.includes('Network request failed') || message.includes('Failed to fetch');
};

const backendReachabilityMessage = (path: string) =>
  `No se pudo contactar con el backend en ${backendUrl(path)}. ` +
  `Verifica desde el navegador del movil ${BACKEND_URL}/ping, que el movil este en la misma red y que el firewall permita el puerto 8000.`;

const mapBackendError = async (response: Response): Promise<Error> => {
  const errorData = await response.json().catch(() => ({ detail: 'Error de red desconocido' }));
  const detail = typeof errorData?.detail === 'string' ? errorData.detail : '';
  if (response.status === 413 || detail === IMAGE_TOO_LARGE_CODE) {
    return new Error(IMAGE_TOO_LARGE_CODE);
  }
  return new Error(detail || `Error del servidor: ${response.status}`);
};

type AuthorizedFetchOptions = {
  body?: BodyInit;
  timeoutMs?: number;
  headers?: Record<string, string>;
  reachabilityPath?: string;
};

const authorizedFetch = async (
  method: string,
  path: string,
  options: AuthorizedFetchOptions = {},
) => {
  const { body, timeoutMs = DEFAULT_TIMEOUT_MS, headers = {}, reachabilityPath = path } = options;
  const user = auth.currentUser;
  if (!user) {
    throw new Error('No hay usuario autenticado. Por favor, inicia sesión.');
  }

  const token = await user.getIdToken(true);
  const requestHeaders: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    ...headers,
  };

  if (!body || !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  logBackendRequest(method, path);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(backendUrl(path), {
      method,
      headers: requestHeaders,
      body,
      signal: controller.signal,
    });
  } catch (error: any) {
    if (error.name === 'AbortError') {
      Logger.error(`Backend request timed out after ${timeoutMs}ms`, { method, path, backendUrl: BACKEND_URL });
      throw new Error(backendReachabilityMessage(reachabilityPath));
    }
    if (isNetworkError(error)) {
      Logger.error('Backend network error', { method, path, backendUrl: BACKEND_URL, error });
      throw new Error(backendReachabilityMessage(reachabilityPath));
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
};

const parseJsonResponse = async (response: Response) => {
  if (!response.ok) {
    throw await mapBackendError(response);
  }
  return response.json();
};

const normalizeHistoryImageUrls = (data: any[]) =>
  data.map((item: any) => {
    if (item.imageUrl?.startsWith('/uploads/')) {
      item.imageUrl = `${BACKEND_URL}${item.imageUrl}`;
    }
    return item;
  });

export const BackendService = {
  testEndpoint: async () => {
    try {
      Logger.debug('Obteniendo token de Firebase para endpoint de prueba');
      const response = await authorizedFetch('GET', '/test');
      Logger.info('Respuesta recibida de endpoint de prueba', { status: response.status });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('Error en BackendService.testEndpoint', error);
      throw error;
    }
  },

  uploadImage: async (imageUri: string, locationStr: string, latitude?: number, longitude?: number, fcmToken?: string, includeExplainability: boolean = false) => {
    try {
      const formData = new FormData();
      const filename = imageUri.split('/').pop() || 'photo.jpg';
      const match = /\.(\w+)$/.exec(filename);
      let type = match ? `image/${match[1]}` : `image/jpeg`;
      if (type === 'image/jpg') type = 'image/jpeg'; // Android compatibility

      formData.append('file', {
        uri: imageUri,
        name: filename,
        type: type,
      } as any);

      formData.append('location', locationStr);
      if (latitude !== undefined) formData.append('latitude', String(latitude));
      if (longitude !== undefined) formData.append('longitude', String(longitude));
      
      if (fcmToken) {
        formData.append('fcm_token', fcmToken);
      }
      formData.append('include_explainability', String(includeExplainability));

      const response = await authorizedFetch('POST', '/analysis/upload', { body: formData, timeoutMs: MUTATION_TIMEOUT_MS });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('Error en BackendService.uploadImage', error);
      throw error;
    }
  },

  getAnalysisHistory: async () => {
    try {
      const response = await authorizedFetch('GET', '/analysis/history');
      const data = await parseJsonResponse(response);
      return normalizeHistoryImageUrls(data);
    } catch (error: any) {
      Logger.error('Error en BackendService.getAnalysisHistory', error);
      throw error;
    }
  },

  deleteUserData: async () => {
    try {
      const response = await authorizedFetch('DELETE', '/analysis/user-data', { timeoutMs: MUTATION_TIMEOUT_MS });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('Error en BackendService.deleteUserData', error);
      throw error;
    }
  },

  deleteAnalysis: async (analysisId: string) => {
    try {
      const path = `/analysis/${analysisId}`;
      const response = await authorizedFetch('DELETE', path, {
        timeoutMs: MUTATION_TIMEOUT_MS,
        reachabilityPath: '/analysis/{analysisId}',
      });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('Error en BackendService.deleteAnalysis', error);
      throw error;
    }
  },

  cancelAnalysis: async (analysisId: string) => {
    try {
      const path = `/analysis/${analysisId}/cancel`;
      const response = await authorizedFetch('PATCH', path, {
        timeoutMs: MUTATION_TIMEOUT_MS,
        reachabilityPath: '/analysis/{analysisId}/cancel',
      });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('Error en BackendService.cancelAnalysis', error);
      throw error;
    }
  },
};
