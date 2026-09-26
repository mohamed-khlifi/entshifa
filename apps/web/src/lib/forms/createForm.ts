"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  useForm,
  type DefaultValues,
  type FieldValues,
  type UseFormReturn,
} from "react-hook-form";
import type { z } from "zod";

import { ApiError } from "@/lib/api/errors";
import {
  AUTOSAVE_DEFAULT_DELAY_MS,
  AUTOSAVE_DEFAULT_MAX_WAIT_MS,
  clearDraftSnapshot,
  pickDirtyValues,
  readDraftSnapshot,
  writeDraftSnapshot,
  type AutosaveConfig,
  type AutosaveStatus,
} from "@/lib/forms/autosave";
import { applyServerFieldErrors } from "@/lib/forms/apply-server-field-errors";

export type CreateClinicalFormConfig<S extends z.ZodTypeAny> = {
  schema: S;
  defaultValues: DefaultValues<z.infer<S>>;
  autosave?: AutosaveConfig<z.infer<S> & Record<string, unknown>>;
  onSubmit: (values: z.infer<S>) => Promise<void>;
  translateFieldError?: (code: string, field: string) => string;
};

export type ClinicalFormApi<T extends FieldValues> = {
  form: UseFormReturn<T>;
  autosaveStatus: AutosaveStatus;
  handleSubmit: (event?: React.BaseSyntheticEvent) => Promise<void>;
  applyApiError: (error: ApiError) => boolean;
};

export function useClinicalForm<S extends z.ZodTypeAny>(
  config: CreateClinicalFormConfig<S>,
): ClinicalFormApi<z.infer<S>> {
  type Values = z.infer<S>;

  const form = useForm<Values>({
    resolver: zodResolver(config.schema),
    defaultValues: config.defaultValues,
    mode: "onBlur",
  });

  const [autosaveStatus, setAutosaveStatus] = useState<AutosaveStatus>("idle");
  const versionRef = useRef(config.autosave?.version ?? 0);
  const firstDirtyAtRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const autosaveRef = useRef(config.autosave);
  autosaveRef.current = config.autosave;
  const onSubmitRef = useRef(config.onSubmit);
  onSubmitRef.current = config.onSubmit;
  const translateRef = useRef(config.translateFieldError);
  translateRef.current = config.translateFieldError;
  const defaultValuesRef = useRef(config.defaultValues);
  defaultValuesRef.current = config.defaultValues;
  const hydratedKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const autosave = autosaveRef.current;
    if (!autosave || hydratedKeyRef.current === autosave.key) {
      return;
    }
    hydratedKeyRef.current = autosave.key;
    let cancelled = false;
    void (async () => {
      const draft = await readDraftSnapshot<Values>(autosave.key);
      if (!cancelled && draft !== null) {
        form.reset({
          ...defaultValuesRef.current,
          ...draft,
        } as DefaultValues<Values>);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [form]);

  const flushAutosave = useCallback(async () => {
    const autosave = autosaveRef.current;
    if (!autosave) {
      return;
    }
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setAutosaveStatus("offline");
      return;
    }

    const values = form.getValues();
    const dirty = pickDirtyValues(
      values as Values & Record<string, unknown>,
      form.formState.dirtyFields as Partial<
        Record<keyof (Values & Record<string, unknown>), unknown>
      >,
    );
    if (Object.keys(dirty).length === 0) {
      setAutosaveStatus("idle");
      return;
    }

    setAutosaveStatus("saving");
    try {
      await writeDraftSnapshot(autosave.key, values);
      const result = await autosave.onSave({
        values: dirty,
        version: versionRef.current,
      });
      versionRef.current = result.version;
      form.reset(form.getValues(), { keepValues: true });
      await clearDraftSnapshot(autosave.key);
      setAutosaveStatus("saved");
      firstDirtyAtRef.current = null;
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setAutosaveStatus("conflict");
        autosave.onConflict?.({
          local: dirty,
          serverVersion: Number(error.context.version ?? versionRef.current),
        });
        return;
      }
      setAutosaveStatus("error");
    }
  }, [form]);

  useEffect(() => {
    if (!autosaveRef.current) {
      return;
    }
    const subscription = form.watch(() => {
      if (!form.formState.isDirty) {
        return;
      }
      const now = Date.now();
      if (firstDirtyAtRef.current === null) {
        firstDirtyAtRef.current = now;
      }
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      const autosave = autosaveRef.current;
      const delay = autosave?.delayMs ?? AUTOSAVE_DEFAULT_DELAY_MS;
      const maxWait = autosave?.maxWaitMs ?? AUTOSAVE_DEFAULT_MAX_WAIT_MS;
      const elapsed = firstDirtyAtRef.current
        ? now - firstDirtyAtRef.current
        : 0;
      const wait = Math.min(delay, Math.max(0, maxWait - elapsed));
      timerRef.current = setTimeout(() => {
        void flushAutosave();
      }, wait);
    });
    return () => {
      subscription.unsubscribe();
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [flushAutosave, form]);

  useEffect(() => {
    if (!autosaveRef.current) {
      return;
    }
    const onOnline = () => {
      void flushAutosave();
    };
    const onOffline = () => setAutosaveStatus("offline");
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, [flushAutosave]);

  const applyApiError = useCallback(
    (error: ApiError) => {
      const translate = translateRef.current ?? ((code: string) => code);
      return applyServerFieldErrors(form, error, translate);
    },
    [form],
  );

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      await onSubmitRef.current(values);
      if (autosaveRef.current) {
        await clearDraftSnapshot(autosaveRef.current.key);
      }
      setAutosaveStatus("idle");
    } catch (error) {
      if (error instanceof ApiError) {
        applyApiError(error);
      }
      throw error;
    }
  });

  return {
    form,
    autosaveStatus,
    handleSubmit,
    applyApiError,
  };
}

/**
 * Typed form factory (architecture §13.3). Prefer module-level config;
 * in components use `useClinicalForm(config)` for stable hooks.
 */
export function createClinicalForm<S extends z.ZodTypeAny>(
  config: CreateClinicalFormConfig<S>,
) {
  return {
    useClinicalForm: () => useClinicalForm(config),
    schema: config.schema,
    defaultValues: config.defaultValues,
  };
}
