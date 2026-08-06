import { computeBoundingBoxes } from '@/src/utils/analysisGeometry';

describe('analysisGeometry', () => {
  it('returns an empty list when layout or analysis details are unavailable', () => {
    expect(computeBoundingBoxes(
      { id: '1', status: 'completed', date: '2026-07-05T00:00:00.000Z' },
      null,
      { width: 400, height: 200 },
    )).toEqual([]);
  });

  it('computes rendered bounding boxes and offsets overlapping labels', () => {
    const boxes = computeBoundingBoxes(
      {
        id: '1',
        status: 'completed',
        date: '2026-07-05T00:00:00.000Z',
        results: {
          cloudTypes: ['cirrus'],
          forecast: '',
          warnings: [],
          cloudDetails: [
            { type: 'cirrus', box: [0.1, 0.1, 0.3, 0.3] },
            { type: 'cumulus', box: [0.11, 0.11, 0.31, 0.31] },
          ],
        },
      },
      { width: 200, height: 100 },
      { width: 400, height: 200 },
    );

    expect(boxes).toHaveLength(2);
    expect(boxes[0]).toMatchObject({ type: 'cirrus', top: 10, left: 20, width: 40, height: 20, labelTopOffset: 0 });
    expect(boxes[1].labelTopOffset).toBe(18);
  });

  it('skips cloud details without boxes', () => {
    const boxes = computeBoundingBoxes(
      {
        id: '1',
        status: 'completed',
        date: '2026-07-05T00:00:00.000Z',
        results: {
          cloudTypes: ['cirrus'],
          forecast: '',
          warnings: [],
          cloudDetails: [
            { type: 'cirrus', box: null },
            { type: 'cumulus', box: [0, 0, 1, 1] },
          ],
        },
      },
      { width: 100, height: 100 },
      { width: 100, height: 100 },
    );

    expect(boxes).toHaveLength(1);
    expect(boxes[0].type).toBe('cumulus');
  });
});
