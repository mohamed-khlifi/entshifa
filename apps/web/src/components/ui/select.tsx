import * as React from "react";

import { formControlClass } from "@/components/ui/form-control";
import { cn } from "@/lib/utils/cn";

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(formControlClass, "appearance-none", className)}
      {...props}
    >
      {children}
    </select>
  ),
);
Select.displayName = "Select";
