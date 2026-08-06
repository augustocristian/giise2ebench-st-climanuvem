import { auth } from '@/src/config/firebaseConfig';
import { Logger } from '@/src/services/LoggerService';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const IMAGE_TOO_LARGE_CODE = 'IMAGE_TOO_LARGE_MAX_5MB';
const API_PREFIX = '/api/v1';
const HISTORY_PAGE_SIZE = 100;
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
  `Verifica desde el navegador del movil ${BACKEND_URL}${API_PREFIX}/ping, que el movil este en la misma red y que el firewall permita el puerto 8000.`;

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

const parseEmptyResponse = async (response: Response) => {
  if (!response.ok) {
    throw await mapBackendError(response);
  }
};

const parseJsonResponse = async (response: Response) => {
  if (!response.ok) {
    throw await mapBackendError(response);
  }
  return response.json();
};

export type AuthenticatedImageSource = {
  uri: string;
  headers?: Record<string, string>;
};

/**
 * Builds an Image source for an analysis image. Backend-relative paths
 * (e.g. /api/v1/analyses/1/image) are made absolute and carry the Authorization
 * header; absolute URLs (guest/mock data) are returned untouched, without headers.
 */
export const getAuthenticatedImageSource = async (imageUrl: string): Promise<AuthenticatedImageSource> => {
  if (!imageUrl.startsWith('/')) {
    return { uri: imageUrl };
  }
  const user = auth.currentUser;
  if (!user) {
    throw new Error('No hay usuario autenticado. Por favor, inicia sesión.');
  }
  const token = await user.getIdToken();
  return { uri: backendUrl(imageUrl), headers: { Authorization: `Bearer ${token}` } };
};

export const BackendService = {
  getAuthenticatedImageSource,

  testEndpoint: async () => {
    try {
      Logger.debug('Getting Firebase token for test endpoint');
      const response = await authorizedFetch('GET', `${API_PREFIX}/test`);
      Logger.info('Response received from test endpoint', { status: response.status });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('BackendService error in testEndpoint', error);
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
        formData.append('fcmToken', fcmToken);
      }
      formData.append('includeExplainability', String(includeExplainability));

      const response = await authorizedFetch('POST', `${API_PREFIX}/analyses`, { body: formData, timeoutMs: MUTATION_TIMEOUT_MS });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('BackendService error in uploadImage', error);
      throw error;
    }
  },

  getAnalysisHistory: async () => {
    try {
      const items: any[] = [];
      for (let page = 0; ; page++) {
        const response = await authorizedFetch('GET', `${API_PREFIX}/analyses?page=${page}&size=${HISTORY_PAGE_SIZE}`);
        const data = await parseJsonResponse(response);
        items.push(...data);
        const total = Number(response.headers?.get?.('X-Total-Count'));
        if (!Number.isFinite(total) || data.length < HISTORY_PAGE_SIZE || items.length >= total) {
          break;
        }
      }
      return items;
    } catch (error: any) {
      Logger.error('BackendService error in getAnalysisHistory', error);
      throw error;
    }
  },

  deleteUserData: async () => {
    try {
      const response = await authorizedFetch('DELETE', `${API_PREFIX}/analyses`, { timeoutMs: MUTATION_TIMEOUT_MS });
      await parseEmptyResponse(response);
    } catch (error: any) {
      Logger.error('BackendService error in deleteUserData', error);
      throw error;
    }
  },

  deleteAnalysis: async (analysisId: number) => {
    try {
      const path = `${API_PREFIX}/analyses/${analysisId}`;
      const response = await authorizedFetch('DELETE', path, {
        timeoutMs: MUTATION_TIMEOUT_MS,
        reachabilityPath: `${API_PREFIX}/analyses/{analysisId}`,
      });
      await parseEmptyResponse(response);
    } catch (error: any) {
      Logger.error('BackendService error in deleteAnalysis', error);
      throw error;
    }
  },

  cancelAnalysis: async (analysisId: number) => {
    try {
      const path = `${API_PREFIX}/analyses/${analysisId}`;
      const response = await authorizedFetch('PATCH', path, {
        body: JSON.stringify({ status: 'cancelled' }),
        timeoutMs: MUTATION_TIMEOUT_MS,
        reachabilityPath: `${API_PREFIX}/analyses/{analysisId}`,
      });
      return await parseJsonResponse(response);
    } catch (error: any) {
      Logger.error('BackendService error in cancelAnalysis', error);
      throw error;
    }
  },
};
