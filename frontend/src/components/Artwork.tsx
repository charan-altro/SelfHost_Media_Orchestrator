import React, { useEffect, useState } from 'react';
import { getLocalArtwork } from '../api/client';

interface ArtworkProps {
  path: string | null | undefined;
  type: 'poster' | 'fanart' | 'profile' | 'thumb';
  className?: string;
  alt?: string;
}

export const Artwork: React.FC<ArtworkProps> = ({ path, type, className, alt = "" }) => {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!path) {
      setSrc(null);
      return;
    }

    if (path.startsWith('local://')) {
      getLocalArtwork(path).then(base64 => {
        setSrc(base64);
      });
    } else {
      const baseMap = {
        poster: 'https://image.tmdb.org/t/p/w500',
        fanart: 'https://image.tmdb.org/t/p/original',
        profile: 'https://image.tmdb.org/t/p/w185',
        thumb: 'https://image.tmdb.org/t/p/w300',
      };
      setSrc(`${baseMap[type]}${path}`);
    }
  }, [path, type]);

  if (!src) return null;

  return <img src={src} alt={alt} className={className} />;
};
