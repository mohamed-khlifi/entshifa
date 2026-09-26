"use client";

import type { ReactNode } from "react";
import {
  FormProvider,
  type FieldValues,
  type UseFormReturn,
} from "react-hook-form";

import { cn } from "@/lib/utils/cn";

type FormProps<T extends FieldValues> = {
  form: UseFormReturn<T>;
  onSubmit: (event?: React.BaseSyntheticEvent) => unknown;
  children: ReactNode;
  className?: string;
};

export function Form<T extends FieldValues>({
  form,
  onSubmit,
  children,
  className,
}: FormProps<T>) {
  return (
    <FormProvider {...form}>
      <form
        className={cn("space-y-5", className)}
        onSubmit={(event) => {
          event.preventDefault();
          void onSubmit(event);
        }}
        noValidate
      >
        {children}
      </form>
    </FormProvider>
  );
}
