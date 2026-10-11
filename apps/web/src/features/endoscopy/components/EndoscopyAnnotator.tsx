"use client";

import { useEffect, useId, useRef, useState, type PointerEvent } from "react";
import { useTranslations } from "next-intl";

import { readDraftSnapshot, writeDraftSnapshot } from "@/lib/forms/autosave";
import { testIdProps, testIds } from "@/lib/test/test-id";
import { cn } from "@/lib/utils/cn";

type Tool = "arrow" | "circle" | "label";

type AnnotationShape =
  | {
      id: string;
      kind: "arrow";
      x1: number;
      y1: number;
      x2: number;
      y2: number;
    }
  | {
      id: string;
      kind: "circle";
      cx: number;
      cy: number;
      rx: number;
      ry: number;
    }
  | { id: string; kind: "label"; x: number; y: number; text: string };

type EndoscopyAnnotatorProps = {
  imageUrl: string;
  storageKey: string;
  readOnly: boolean;
  onClose: () => void;
};

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `mark-${Date.now()}`;
}

export function EndoscopyAnnotator({
  imageUrl,
  storageKey,
  readOnly,
  onClose,
}: EndoscopyAnnotatorProps) {
  const t = useTranslations("endoscopy");
  const labelId = useId();
  const markerId = useId().replaceAll(":", "");
  const surfaceRef = useRef<SVGSVGElement>(null);
  const [tool, setTool] = useState<Tool>("arrow");
  const [label, setLabel] = useState("");
  const [shapes, setShapes] = useState<AnnotationShape[]>([]);
  const draftRef = useRef<AnnotationShape | null>(null);

  useEffect(() => {
    let cancelled = false;
    void readDraftSnapshot<AnnotationShape[]>(storageKey).then((stored) => {
      if (!cancelled && stored) {
        setShapes(stored);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [storageKey]);

  useEffect(() => {
    void writeDraftSnapshot(storageKey, shapes);
  }, [shapes, storageKey]);

  function point(event: PointerEvent<SVGSVGElement>) {
    const host = surfaceRef.current;
    if (!host) {
      return null;
    }
    const box = host.getBoundingClientRect();
    if (box.width <= 0 || box.height <= 0) {
      return null;
    }
    if (!Number.isFinite(event.clientX) || !Number.isFinite(event.clientY)) {
      return null;
    }
    return {
      x: ((event.clientX - box.left) / box.width) * 100,
      y: ((event.clientY - box.top) / box.height) * 100,
    };
  }

  function handlePointerDown(event: PointerEvent<SVGSVGElement>) {
    if (readOnly) {
      return;
    }
    const start = point(event);
    if (!start) {
      return;
    }
    event.currentTarget.setPointerCapture?.(event.pointerId);
    if (tool === "label") {
      const text = label.trim();
      if (!text) {
        return;
      }
      setShapes((current) => [
        ...current,
        { id: newId(), kind: "label", x: start.x, y: start.y, text },
      ]);
      return;
    }
    if (tool === "circle") {
      draftRef.current = {
        id: newId(),
        kind: "circle",
        cx: start.x,
        cy: start.y,
        rx: 0,
        ry: 0,
      };
      return;
    }
    draftRef.current = {
      id: newId(),
      kind: "arrow",
      x1: start.x,
      y1: start.y,
      x2: start.x,
      y2: start.y,
    };
  }

  function handlePointerMove(event: PointerEvent<SVGSVGElement>) {
    const draft = draftRef.current;
    const next = point(event);
    if (!draft || !next) {
      return;
    }
    if (draft.kind === "arrow") {
      draftRef.current = { ...draft, x2: next.x, y2: next.y };
    } else if (draft.kind === "circle") {
      draftRef.current = {
        ...draft,
        rx: Math.abs(next.x - draft.cx),
        ry: Math.abs(next.y - draft.cy),
      };
    }
    setShapes((current) => {
      const without = current.filter((shape) => shape.id !== draft.id);
      return draftRef.current ? [...without, draftRef.current] : without;
    });
  }

  function handlePointerUp() {
    draftRef.current = null;
  }

  const visible = shapes.filter((shape) => {
    if (shape.kind === "circle") {
      return shape.rx > 0 || shape.ry > 0;
    }
    if (shape.kind === "arrow") {
      return shape.x1 !== shape.x2 || shape.y1 !== shape.y2;
    }
    return true;
  });

  return (
    <div className="space-y-3" {...testIdProps(testIds.endoscopy.annotate)}>
      <p className="text-sm text-muted-foreground">{t("images.overlayNote")}</p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={cn(
            "rounded-md border px-3 py-1.5 text-sm",
            tool === "arrow" ? "border-primary bg-primary/10" : "border-border",
          )}
          disabled={readOnly}
          onClick={() => setTool("arrow")}
          {...testIdProps(testIds.endoscopy.toolArrow)}
        >
          {t("images.tools.arrow")}
        </button>
        <button
          type="button"
          className={cn(
            "rounded-md border px-3 py-1.5 text-sm",
            tool === "circle"
              ? "border-primary bg-primary/10"
              : "border-border",
          )}
          disabled={readOnly}
          onClick={() => setTool("circle")}
          {...testIdProps(testIds.endoscopy.toolCircle)}
        >
          {t("images.tools.circle")}
        </button>
        <button
          type="button"
          className={cn(
            "rounded-md border px-3 py-1.5 text-sm",
            tool === "label" ? "border-primary bg-primary/10" : "border-border",
          )}
          disabled={readOnly}
          onClick={() => setTool("label")}
          {...testIdProps(testIds.endoscopy.toolLabel)}
        >
          {t("images.tools.label")}
        </button>
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1.5 text-sm"
          disabled={readOnly}
          onClick={() => setShapes([])}
          {...testIdProps(testIds.endoscopy.toolClear)}
        >
          {t("images.tools.clear")}
        </button>
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1.5 text-sm"
          onClick={onClose}
          {...testIdProps(testIds.endoscopy.annotateClose)}
        >
          {t("images.close")}
        </button>
      </div>
      {tool === "label" ? (
        <label className="block space-y-1 text-sm" htmlFor={labelId}>
          {t("images.labelText")}
          <input
            id={labelId}
            className="flex h-10 w-full rounded-lg border border-input bg-card px-3 text-sm"
            value={label}
            maxLength={120}
            disabled={readOnly}
            onChange={(event) => setLabel(event.target.value)}
            {...testIdProps(testIds.endoscopy.labelInput)}
          />
        </label>
      ) : null}
      <div className="relative max-w-xl overflow-hidden rounded-xl border border-border bg-card">
        {/* Signed download URLs must render the original bytes, not a rewritten optimizer URL. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt=""
          className="block h-auto w-full"
          {...testIdProps(testIds.endoscopy.annotateImage)}
        />
        <svg
          ref={surfaceRef}
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full touch-none"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          {...testIdProps(testIds.endoscopy.annotateSurface)}
        >
          {visible.map((shape) => {
            if (shape.kind === "arrow") {
              return (
                <line
                  key={shape.id}
                  x1={shape.x1}
                  y1={shape.y1}
                  x2={shape.x2}
                  y2={shape.y2}
                  stroke="currentColor"
                  strokeWidth="1.2"
                  className="text-destructive"
                  markerEnd={`url(#${markerId})`}
                />
              );
            }
            if (shape.kind === "circle") {
              return (
                <ellipse
                  key={shape.id}
                  cx={shape.cx}
                  cy={shape.cy}
                  rx={shape.rx}
                  ry={shape.ry}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  className="text-primary"
                />
              );
            }
            return (
              <text
                key={shape.id}
                x={shape.x}
                y={shape.y}
                fontSize="4"
                fill="currentColor"
                className="text-foreground"
              >
                {shape.text}
              </text>
            );
          })}
          <defs>
            <marker
              id={markerId}
              markerWidth="6"
              markerHeight="6"
              refX="5"
              refY="3"
              orient="auto"
            >
              <path d="M0 0 L6 3 L0 6 z" fill="currentColor" />
            </marker>
          </defs>
        </svg>
      </div>
    </div>
  );
}
