import { AnalysisService } from '@/src/services/AnalysisService';
import { BackendService } from '@/src/services/BackendService';
import { GUEST_DEMO_HISTORY } from '@/src/services/mockData';

describe('AnalysisService', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(BackendService, 'uploadImage').mockResolvedValue({ analysis_id: 1 });
    jest.spyOn(BackendService, 'deleteAnalysis').mockResolvedValue({ deleted: true });
    jest.spyOn(BackendService, 'cancelAnalysis').mockResolvedValue({ cancelled: true });
    jest.spyOn(BackendService, 'getAnalysisHistory').mockResolvedValue([{ id: '1', status: 'completed', date: 'today' }]);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it('delegates upload, delete and cancel operations to the backend', async () => {
    await expect(AnalysisService.uploadImage('file.jpg', 'Gijon', 1, 2, 'fcm', true)).resolves.toEqual({ analysis_id: 1 });
    await expect(AnalysisService.deleteAnalysis('1')).resolves.toEqual({ deleted: true });
    await expect(AnalysisService.cancelAnalysis('1')).resolves.toEqual({ cancelled: true });

    expect(BackendService.uploadImage).toHaveBeenCalledWith('file.jpg', 'Gijon', 1, 2, 'fcm', true);
    expect(BackendService.deleteAnalysis).toHaveBeenCalledWith('1');
    expect(BackendService.cancelAnalysis).toHaveBeenCalledWith('1');
  });

  it('returns backend history for logged-in users', async () => {
    const promise = AnalysisService.getHistory(true);
    jest.advanceTimersByTime(1000);

    await expect(promise).resolves.toEqual([{ id: '1', status: 'completed', date: 'today' }]);
  });

  it('returns an empty history when logged-in history fails', async () => {
    jest.mocked(BackendService.getAnalysisHistory).mockRejectedValue(new Error('backend failed'));

    const promise = AnalysisService.getHistory(true);
    jest.advanceTimersByTime(1000);

    await expect(promise).resolves.toEqual([]);
  });

  it('returns guest demo history for guest users', async () => {
    const promise = AnalysisService.getHistory(false);
    jest.advanceTimersByTime(1000);

    await expect(promise).resolves.toBe(GUEST_DEMO_HISTORY);
  });
});
