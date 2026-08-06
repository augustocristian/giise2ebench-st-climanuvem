const getIdToken = jest.fn();
const authMock = {
  currentUser: null as null | { getIdToken: jest.Mock },
};

jest.mock('@/src/config/firebaseConfig', () => ({ auth: authMock }));

const loadBackendService = () => {
  jest.resetModules();
  return require('@/src/services/BackendService').BackendService;
};

const jsonResponse = (ok: boolean, status: number, body: unknown) => ({
  ok,
  status,
  json: jest.fn().mockResolvedValue(body),
});

describe('BackendService', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_BACKEND_URL = 'http://api.test';
    authMock.currentUser = { getIdToken };
    getIdToken.mockResolvedValue('firebase-token');
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
    delete process.env.EXPO_PUBLIC_BACKEND_URL;
  });

  it('rejects requests when there is no authenticated user', async () => {
    authMock.currentUser = null;
    const BackendService = loadBackendService();

    await expect(BackendService.testEndpoint()).rejects.toThrow(
      'No hay usuario autenticado',
    );
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('sends authenticated requests to the test endpoint', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 200, { ok: true }),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.testEndpoint()).resolves.toEqual({ ok: true });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/test',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer firebase-token',
          'Content-Type': 'application/json',
        }),
      }),
    );
  });

  it('maps oversized image backend errors to the shared code', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(false, 413, { detail: 'anything' }),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.testEndpoint()).rejects.toThrow(
      'IMAGE_TOO_LARGE_MAX_5MB',
    );
  });

  it('maps network failures to a reachability message', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new TypeError('Failed to fetch'));
    const BackendService = loadBackendService();

    await expect(BackendService.getAnalysisHistory()).rejects.toThrow(
      'No se pudo contactar con el backend en http://api.test/analysis/history',
    );
  });

  it('normalizes relative upload image URLs in history responses', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 200, [
        { id: '1', imageUrl: '/uploads/user/cloud.jpg' },
        { id: '2', imageUrl: 'https://cdn.test/cloud.jpg' },
      ]),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.getAnalysisHistory()).resolves.toEqual([
      { id: '1', imageUrl: 'http://api.test/uploads/user/cloud.jpg' },
      { id: '2', imageUrl: 'https://cdn.test/cloud.jpg' },
    ]);
  });

  it('uploads images with form data and auth header', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 200, { analysis_id: 12 }),
    );
    const BackendService = loadBackendService();

    await expect(
      BackendService.uploadImage('file:///tmp/cloud.jpg', 'Gijon', 43.5, -5.6, 'fcm-token', true),
    ).resolves.toEqual({ analysis_id: 12 });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/analysis/upload',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer firebase-token',
        }),
        body: expect.any(FormData),
      }),
    );
  });

  it('deletes all user data with the authenticated request helper', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 200, { deleted: true }),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.deleteUserData()).resolves.toEqual({ deleted: true });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/analysis/user-data',
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({
          Authorization: 'Bearer firebase-token',
          'Content-Type': 'application/json',
        }),
      }),
    );
  });

  it('deletes a single analysis by id', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 200, { deleted: true }),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.deleteAnalysis('42')).resolves.toEqual({ deleted: true });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/analysis/42',
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('cancels an analysis by id', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 200, { cancelled: true }),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.cancelAnalysis('42')).resolves.toEqual({ cancelled: true });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/analysis/42/cancel',
      expect.objectContaining({ method: 'PATCH' }),
    );
  });
});
