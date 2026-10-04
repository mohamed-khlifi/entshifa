"use client";

import { Button } from "@/components/ui/button";
import { testIdProps, testIds } from "@/lib/test/test-id";

type NormalsToolbarProps = {
  canCopy: boolean;
  copying: boolean;
  onNormalAll: () => void;
  onOtoscopyRight: () => void;
  onOtoscopyLeft: () => void;
  onRhinoscopy: () => void;
  onOral: () => void;
  onNeck: () => void;
  onCopy: () => void;
  compact?: boolean;
  labels: {
    group: string;
    all: string;
    otoscopyRight: string;
    otoscopyLeft: string;
    rhinoscopy: string;
    oral: string;
    neck: string;
    copy: string;
    unavailable: string;
  };
};

export function NormalsToolbar({
  canCopy,
  copying,
  onNormalAll,
  onOtoscopyRight,
  onOtoscopyLeft,
  onRhinoscopy,
  onOral,
  onNeck,
  onCopy,
  compact = false,
  labels,
}: NormalsToolbarProps) {
  return (
    <section
      className={
        compact ? "flex min-w-0 flex-wrap items-center gap-2" : "space-y-2"
      }
      {...testIdProps(testIds.examination.normals.group)}
    >
      <h2 className={compact ? "sr-only" : "text-sm font-medium"}>
        {labels.group}
      </h2>
      <div className={compact ? "contents" : "flex flex-wrap gap-2"}>
        <Button
          type="button"
          onClick={onNormalAll}
          {...testIdProps(testIds.examination.normals.all)}
        >
          {labels.all}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onOtoscopyRight}
          {...testIdProps(testIds.examination.normals.otoscopyRight)}
        >
          {labels.otoscopyRight}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onOtoscopyLeft}
          {...testIdProps(testIds.examination.normals.otoscopyLeft)}
        >
          {labels.otoscopyLeft}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onRhinoscopy}
          {...testIdProps(testIds.examination.normals.rhinoscopy)}
        >
          {labels.rhinoscopy}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onOral}
          {...testIdProps(testIds.examination.normals.oral)}
        >
          {labels.oral}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onNeck}
          {...testIdProps(testIds.examination.normals.neck)}
        >
          {labels.neck}
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={!canCopy || copying}
          title={canCopy ? undefined : labels.unavailable}
          onClick={onCopy}
          {...testIdProps(testIds.examination.copyForward.action)}
        >
          {labels.copy}
        </Button>
      </div>
      {!canCopy && !compact ? (
        <p
          className="text-sm text-muted-foreground"
          {...testIdProps(testIds.examination.copyForward.unavailable)}
        >
          {labels.unavailable}
        </p>
      ) : null}
    </section>
  );
}
