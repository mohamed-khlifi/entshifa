/** Fixed-height window over a long patient history. No virtualization library. */

export const TIMELINE_ROW_HEIGHT = 76;

export function timelineWindow(
  scrollTop: number,
  viewportHeight: number,
  itemCount: number,
  rowHeight: number = TIMELINE_ROW_HEIGHT,
  overscan = 4,
): { start: number; end: number; paddingTop: number; paddingBottom: number } {
  if (itemCount <= 0 || rowHeight <= 0 || viewportHeight <= 0) {
    return { start: 0, end: 0, paddingTop: 0, paddingBottom: 0 };
  }
  const rawStart = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const visible = Math.max(1, Math.ceil(viewportHeight / rowHeight));
  const lastStart = Math.max(0, itemCount - visible);
  const start = Math.min(rawStart, lastStart);
  const end = Math.min(itemCount, start + visible + overscan * 2);
  return {
    start,
    end,
    paddingTop: start * rowHeight,
    paddingBottom: Math.max(0, itemCount - end) * rowHeight,
  };
}
