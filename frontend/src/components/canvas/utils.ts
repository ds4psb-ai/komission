/**
 * Canvas Node Utilities
 * Shared constants and helper functions for Canvas nodes
 */

// ============================================================
// Handle Style Constants
// ============================================================

/**
 * React Flow Handle의 공통 색상 테마
 */
export const HANDLE_COLORS = {
    emerald: '!bg-emerald-500',
    violet: '!bg-violet-500',
    cyan: '!bg-cyan-500',
    blue: '!bg-blue-500',
    amber: '!bg-amber-500',
    rose: '!bg-rose-400',
    sky: '!bg-sky-500',
} as const;

/**
 * Handle 기본 스타일 클래스
 */
export const HANDLE_BASE_STYLE = '!w-3 !h-3 !border-2 !border-black';

/**
 * 색상별 Handle 스타일 생성
 */
export function getHandleStyle(color: keyof typeof HANDLE_COLORS): string {
    return `${HANDLE_COLORS[color]} ${HANDLE_BASE_STYLE}`;
}

// Pre-built handle styles for common colors
export const HANDLE_STYLES = {
    emerald: getHandleStyle('emerald'),
    violet: getHandleStyle('violet'),
    cyan: getHandleStyle('cyan'),
    blue: getHandleStyle('blue'),
    amber: getHandleStyle('amber'),
    rose: getHandleStyle('rose'),
    sky: getHandleStyle('sky'),
} as const;

// ============================================================
// CSV Download Utilities
// ============================================================

interface CsvDownloadOptions {
    filename: string;
    data: string;
    mimeType?: string;
}

/**
 * CSV 또는 텍스트 파일 다운로드 트리거
 */
export function downloadFile({ filename, data, mimeType = 'text/csv' }: CsvDownloadOptions): void {
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Blob 객체 다운로드 트리거
 */
export function downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * 객체 배열을 CSV 문자열로 변환
 */
export function arrayToCsv<T extends Record<string, unknown>>(
    data: T[],
    columns?: (keyof T)[]
): string {
    if (data.length === 0) return '';

    const cols = columns || (Object.keys(data[0]) as (keyof T)[]);
    const header = cols.join(',');
    const rows = data.map(row =>
        cols.map(col => {
            const value = row[col];
            // Handle strings with commas or quotes
            if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                return `"${value.replace(/"/g, '""')}"`;
            }
            return String(value ?? '');
        }).join(',')
    );

    return [header, ...rows].join('\n');
}

// ============================================================
// Number Formatting Utilities
// ============================================================

/**
 * 큰 숫자를 K/M 형식으로 포맷
 * @example formatViewCount(1500000) => "1.5M"
 */
export function formatViewCount(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}
