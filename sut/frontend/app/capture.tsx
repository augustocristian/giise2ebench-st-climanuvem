import React from 'react';
import { useCapture } from '@/src/controllers/useCapture';
import { CaptureView } from '@/src/views/CaptureView';

export default function CaptureScreen() {
  const captureController = useCapture();
  
  return <CaptureView controller={captureController} />;
}
