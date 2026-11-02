import type { ReactNode } from "react";

import type { SymbolDescriptor } from "../../utils/audiogram.utils";
import { earColor } from "../../utils/audiogram.utils";

type SymbolProps = {
  x: number;
  y: number;
  descriptor: SymbolDescriptor;
  opacity?: number;
  testId?: string;
};

export function AudiogramSymbol({
  x,
  y,
  descriptor,
  opacity = 1,
  testId,
}: SymbolProps) {
  const color = earColor(descriptor.ear);
  const size = 7;
  return (
    <g
      opacity={opacity}
      data-testid={testId}
      transform={`translate(${x}, ${y})`}
    >
      {renderCore(descriptor, color, size)}
      {descriptor.isNoResponse ? (
        <line
          x1={-size}
          y1={size + 2}
          x2={descriptor.ear === "right" ? size + 4 : -size - 4}
          y2={size + 10}
          stroke={color}
          strokeWidth={1.5}
        />
      ) : null}
    </g>
  );
}

function renderCore(
  descriptor: SymbolDescriptor,
  color: string,
  size: number,
): ReactNode {
  const { ear, conduction, isMasked } = descriptor;
  if (conduction === "air") {
    if (ear === "right") {
      if (isMasked) {
        return (
          <polygon
            points={`0,${-size} ${size},${size} ${-size},${size}`}
            fill="none"
            stroke={color}
            strokeWidth={1.5}
          />
        );
      }
      return <circle r={size} fill="none" stroke={color} strokeWidth={1.5} />;
    }
    if (isMasked) {
      return (
        <rect
          x={-size}
          y={-size}
          width={size * 2}
          height={size * 2}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
        />
      );
    }
    return (
      <g stroke={color} strokeWidth={1.5}>
        <line x1={-size} y1={-size} x2={size} y2={size} />
        <line x1={-size} y1={size} x2={size} y2={-size} />
      </g>
    );
  }
  if (ear === "right") {
    if (isMasked) {
      return (
        <g stroke={color} strokeWidth={1.5} fill="none">
          <line x1={-size - 2} y1={-size} x2={-size - 2} y2={size} />
          <line x1={size + 2} y1={-size} x2={size + 2} y2={size} />
        </g>
      );
    }
    return (
      <g stroke={color} strokeWidth={1.5}>
        <line x1={-size - 2} y1={-size} x2={-size - 2} y2={size} />
        <line x1={size} y1={-size} x2={-size} y2={0} />
      </g>
    );
  }
  if (isMasked) {
    return (
      <g stroke={color} strokeWidth={1.5} fill="none">
        <line x1={-size - 2} y1={-size} x2={-size - 2} y2={size} />
        <line x1={size + 2} y1={-size} x2={size + 2} y2={size} />
      </g>
    );
  }
  return (
    <g stroke={color} strokeWidth={1.5}>
      <line x1={size + 2} y1={-size} x2={size + 2} y2={size} />
      <line x1={-size} y1={-size} x2={size} y2={0} />
    </g>
  );
}
