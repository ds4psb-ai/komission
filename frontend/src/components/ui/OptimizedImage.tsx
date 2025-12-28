'use client';

/**
 * OptimizedImage - Next.js Image 컴포넌트 래퍼 (PEGL v1.0)
 * 
 * 자동 최적화:
 * - 지연 로딩 (lazy loading)
 * - 블러 플레이스홀더
 * - 반응형 크기
 * - WebP/AVIF 변환
 */
import Image from 'next/image';
import { useState } from 'react';

// 외부 이미지 도메인 설정을 위한 기본 loader
const customLoader = ({ src, width, quality }: { src: string; width: number; quality?: number }) => {
    // 외부 URL인 경우 그대로 반환 (next.config.js에서 remotePatterns 설정 필요)
    if (src.startsWith('http')) {
        return src;
    }
    return `${src}?w=${width}&q=${quality || 75}`;
};

interface OptimizedImageProps {
    src: string;
    alt: string;
    width?: number;
    height?: number;
    fill?: boolean;
    className?: string;
    priority?: boolean;
    quality?: number;
    sizes?: string;
    onLoad?: () => void;
    onError?: () => void;
    fallbackSrc?: string;
}

export function OptimizedImage({
    src,
    alt,
    width,
    height,
    fill = false,
    className = '',
    priority = false,
    quality = 75,
    sizes,
    onLoad,
    onError,
    fallbackSrc = '/placeholder.png',
}: OptimizedImageProps) {
    const [imageSrc, setImageSrc] = useState(src);
    const [isLoaded, setIsLoaded] = useState(false);
    const [hasError, setHasError] = useState(false);

    const handleLoad = () => {
        setIsLoaded(true);
        onLoad?.();
    };

    const handleError = () => {
        if (!hasError && fallbackSrc) {
            setImageSrc(fallbackSrc);
            setHasError(true);
        }
        onError?.();
    };

    // 외부 이미지인지 확인
    const isExternal = imageSrc.startsWith('http');

    // fill 모드용 props
    const imageProps = fill
        ? { fill: true, sizes: sizes || '100vw' }
        : { width: width || 400, height: height || 300 };

    return (
        <div className={`relative overflow-hidden ${className}`}>
            {/* Blur placeholder */}
            {!isLoaded && !hasError && (
                <div className="absolute inset-0 bg-white/5 animate-pulse" />
            )}

            {isExternal ? (
                // 외부 이미지: unoptimized 사용
                <Image
                    src={imageSrc}
                    alt={alt}
                    {...imageProps}
                    className={`object-cover transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
                    priority={priority}
                    quality={quality}
                    unoptimized
                    onLoad={handleLoad}
                    onError={handleError}
                />
            ) : (
                // 내부 이미지: 최적화 적용
                <Image
                    src={imageSrc}
                    alt={alt}
                    {...imageProps}
                    className={`object-cover transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
                    priority={priority}
                    quality={quality}
                    onLoad={handleLoad}
                    onError={handleError}
                />
            )}
        </div>
    );
}

/**
 * Avatar - 프로필 이미지 최적화
 */
interface AvatarProps {
    src?: string | null;
    alt?: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    fallback?: string;
    className?: string;
}

const AVATAR_SIZES = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
};

const AVATAR_PIXELS = {
    sm: 24,
    md: 32,
    lg: 48,
    xl: 64,
};

export function Avatar({
    src,
    alt = 'Avatar',
    size = 'md',
    fallback = '?',
    className = '',
}: AvatarProps) {
    const [hasError, setHasError] = useState(false);

    if (!src || hasError) {
        return (
            <div className={`${AVATAR_SIZES[size]} rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-white font-bold ${className}`}>
                {fallback.charAt(0).toUpperCase()}
            </div>
        );
    }

    return (
        <div className={`${AVATAR_SIZES[size]} rounded-full overflow-hidden ${className}`}>
            <Image
                src={src}
                alt={alt}
                width={AVATAR_PIXELS[size]}
                height={AVATAR_PIXELS[size]}
                className="object-cover w-full h-full"
                unoptimized={src.startsWith('http')}
                onError={() => setHasError(true)}
            />
        </div>
    );
}

/**
 * Thumbnail - 비디오 썸네일 최적화
 */
interface ThumbnailProps {
    src?: string | null;
    alt?: string;
    aspectRatio?: '16:9' | '9:16' | '4:5' | '1:1';
    className?: string;
    priority?: boolean;
}

const ASPECT_RATIOS = {
    '16:9': 'aspect-video',
    '9:16': 'aspect-[9/16]',
    '4:5': 'aspect-[4/5]',
    '1:1': 'aspect-square',
};

export function Thumbnail({
    src,
    alt = 'Thumbnail',
    aspectRatio = '16:9',
    className = '',
    priority = false,
}: ThumbnailProps) {
    const [hasError, setHasError] = useState(false);

    if (!src || hasError) {
        return (
            <div className={`${ASPECT_RATIOS[aspectRatio]} bg-gradient-to-br from-violet-900/50 to-pink-900/50 flex items-center justify-center ${className}`}>
                <span className="text-4xl opacity-30">🎬</span>
            </div>
        );
    }

    return (
        <div className={`relative ${ASPECT_RATIOS[aspectRatio]} ${className}`}>
            <Image
                src={src}
                alt={alt}
                fill
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                className="object-cover"
                priority={priority}
                unoptimized={src.startsWith('http')}
                onError={() => setHasError(true)}
            />
        </div>
    );
}

export default OptimizedImage;
