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
      'http://api.test/api/v1/test',
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
      'No se pudo contactar con el backend en http://api.test/api/v1/analyses?page=0&size=100',
    );
  });

  it('keeps relative image URLs untouched in history responses', async () => {
    const items = [
      { id: 1, imageUrl: '/api/v1/analyses/1/image' },
      { id: 2, imageUrl: 'https://cdn.test/cloud.jpg' },
    ];
    (global.fetch as jest.Mock).mockResolvedValue(jsonResponse(true, 200, items));
    const BackendService = loadBackendService();

    await expect(BackendService.getAnalysisHistory()).resolves.toEqual(items);
  });

  it('builds an absolute authenticated image source for relative paths', async () => {
    const service = loadBackendService();

    await expect(service.getAuthenticatedImageSource('/api/v1/analyses/7/image')).resolves.toEqual({
      uri: 'http://api.test/api/v1/analyses/7/image',
      headers: { Authorization: 'Bearer firebase-token' },
    });
  });

  it('returns absolute (mock/guest) image URLs without headers', async () => {
    const service = loadBackendService();

    await expect(service.getAuthenticatedImageSource('https://picsum.photos/id/1015/800/600')).resolves.toEqual({
      uri: 'https://picsum.photos/id/1015/800/600',
    });
    expect(getIdToken).not.toHaveBeenCalled();
  });

  it('rejects image source for relative paths without a user', async () => {
    authMock.currentUser = null;
    const service = loadBackendService();

    await expect(service.getAuthenticatedImageSource('/api/v1/analyses/7/image')).rejects.toThrow(
      'No hay usuario autenticado',
    );
  });

  it('uploads images with form data and auth header', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 202, { id: 12, status: 'analyzing' }),
    );
    const BackendService = loadBackendService();

    await expect(
      BackendService.uploadImage('file:///tmp/cloud.jpg', 'Gijon', 43.5, -5.6, 'fcm-token', true),
    ).resolves.toEqual({ id: 12, status: 'analyzing' });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/api/v1/analyses',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer firebase-token',
        }),
        body: expect.any(FormData),
      }),
    );
  });

  it('deletes all user data without parsing a body', async () => {
    const response = { ok: true, status: 204, json: jest.fn().mockRejectedValue(new Error('no body')) };
    (global.fetch as jest.Mock).mockResolvedValue(response);
    const BackendService = loadBackendService();

    await expect(BackendService.deleteUserData()).resolves.toBeUndefined();

    expect(response.json).not.toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/api/v1/analyses',
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({
          Authorization: 'Bearer firebase-token',
          'Content-Type': 'application/json',
        }),
      }),
    );
  });

  it('deletes a single analysis by integer id', async () => {
    const response = { ok: true, status: 204, json: jest.fn() };
    (global.fetch as jest.Mock).mockResolvedValue(response);
    const BackendService = loadBackendService();

    await expect(BackendService.deleteAnalysis(42)).resolves.toBeUndefined();

    expect(response.json).not.toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/api/v1/analyses/42',
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('cancels an analysis with a PATCH status body', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(true, 200, { id: 42, status: 'cancelled' }),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.cancelAnalysis(42)).resolves.toEqual({ id: 42, status: 'cancelled' });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://api.test/api/v1/analyses/42',
      expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ status: 'cancelled' }) }),
    );
  });

  it('surfaces problem+json machine codes as error messages', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(false, 409, { status: 409, detail: 'ANALYSIS_NOT_CANCELLABLE' }),
    );
    const BackendService = loadBackendService();

    await expect(BackendService.cancelAnalysis(42)).rejects.toThrow('ANALYSIS_NOT_CANCELLABLE');
  });

  it('follows X-Total-Count to load the whole history', async () => {
    const page = (start: number) => Array.from({ length: 100 }, (_, i) => ({ id: start + i }));
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ...jsonResponse(true, 200, page(0)), headers: { get: () => '150' } })
      .mockResolvedValueOnce({ ...jsonResponse(true, 200, [{ id: 100 }]), headers: { get: () => '150' } });
    const BackendService = loadBackendService();

    const result = await BackendService.getAnalysisHistory();

    expect(result).toHaveLength(101);
    expect(global.fetch).toHaveBeenCalledTimes(2);
    expect((global.fetch as jest.Mock).mock.calls[1][0]).toBe('http://api.test/api/v1/analyses?page=1&size=100');
  });
});
