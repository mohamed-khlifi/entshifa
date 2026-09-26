import { cn } from '@/lib/utils/cn';

/**
 * Directional icons (back, next, chevrons) flip in RTL.
 * Anatomical icons, charts, audiograms and maps must NOT use this.
 */
export function directionalIconClass(...classes: Array<string | undefined | false>): string {
  return cn(...classes, 'rtl:-scale-x-100');
}
