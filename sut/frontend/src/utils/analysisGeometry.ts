import type { AnalysisHistoryItem } from '@/src/services/AnalysisService';

export type Size = {
  width: number;
  height: number;
};

export type ComputedBoundingBox = {
  key: string;
  type: string;
  top: number;
  left: number;
  width: number;
  height: number;
  labelTopOffset: number;
};

export const computeBoundingBoxes = (
  analysis: AnalysisHistoryItem,
  imageLayout: Size | null,
  intrinsicImageSize: Size | null,
): ComputedBoundingBox[] => {
  if (!imageLayout || !intrinsicImageSize || !analysis.results?.cloudDetails) {
    return [];
  }

  const boxes = analysis.results.cloudDetails.flatMap((detail, index) => {
    if (!detail.box) return [];

    const [val1, val2, val3, val4] = detail.box;
    const ymin = Math.min(val1, val3);
    const ymax = Math.max(val1, val3);
    const xmin = Math.min(val2, val4);
    const xmax = Math.max(val2, val4);

    const scale = Math.min(
      imageLayout.width / intrinsicImageSize.width,
      imageLayout.height / intrinsicImageSize.height,
    );

    const renderedWidth = intrinsicImageSize.width * scale;
    const renderedHeight = intrinsicImageSize.height * scale;
    const offsetX = (imageLayout.width - renderedWidth) / 2;
    const offsetY = (imageLayout.height - renderedHeight) / 2;

    return [{
      key: `box-${detail.type}-${index}`,
      type: detail.type,
      top: offsetY + ymin * renderedHeight,
      left: offsetX + xmin * renderedWidth,
      width: (xmax - xmin) * renderedWidth,
      height: (ymax - ymin) * renderedHeight,
      labelTopOffset: 0,
    }];
  });

  boxes.forEach((box, index) => {
    let overlapCount = 0;
    for (let previousIndex = 0; previousIndex < index; previousIndex += 1) {
      const other = boxes[previousIndex];
      if (other && Math.abs(box.top - other.top) < 20 && Math.abs(box.left - other.left) < 20) {
        overlapCount += 1;
      }
    }
    box.labelTopOffset = overlapCount * 18;
  });

  return boxes;
};
