import { useEffect, useState } from 'react';
import { AuthenticatedImageSource, getAuthenticatedImageSource } from '@/src/services/BackendService';
import { Logger } from '@/src/services/LoggerService';

export const useAuthenticatedImageSource = (imageUrl?: string): AuthenticatedImageSource | null => {
  const [resolved, setResolved] = useState<{ imageUrl: string; source: AuthenticatedImageSource } | null>(null);

  useEffect(() => {
    if (!imageUrl) {
      return;
    }
    let cancelled = false;
    getAuthenticatedImageSource(imageUrl)
      .then((source) => {
        if (!cancelled) setResolved({ imageUrl, source });
      })
      .catch((error) => {
        Logger.error('Could not build authenticated image source', error);
      });
    return () => {
      cancelled = true;
    };
  }, [imageUrl]);

  return imageUrl && resolved?.imageUrl === imageUrl ? resolved.source : null;
};
