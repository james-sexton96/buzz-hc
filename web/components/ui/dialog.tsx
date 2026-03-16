"use client";

import * as React from "react";
import { Dialog as BaseDialog } from "@base-ui/react/dialog";

export function Dialog({ children, open, onOpenChange }: {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}) {
  return (
    <BaseDialog.Root open={open} onOpenChange={onOpenChange}>
      {children}
    </BaseDialog.Root>
  );
}

export function DialogTrigger({ children }: { children: React.ReactNode }) {
  return <BaseDialog.Trigger render={<>{children}</>} />;
}

export function DialogContent({ children }: { children: React.ReactNode }) {
  return (
    <BaseDialog.Portal>
      <BaseDialog.Backdrop className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50" />
      <BaseDialog.Popup className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-card rounded-2xl shadow-xl border border-border/60 p-6 w-full max-w-md z-50">
        {children}
      </BaseDialog.Popup>
    </BaseDialog.Portal>
  );
}

export function DialogHeader({ children }: { children: React.ReactNode }) {
  return <div className="space-y-1.5 mb-4">{children}</div>;
}

export function DialogTitle({ children }: { children: React.ReactNode }) {
  return (
    <BaseDialog.Title className="text-base font-semibold leading-none tracking-tight">
      {children}
    </BaseDialog.Title>
  );
}

export function DialogDescription({ children }: { children: React.ReactNode }) {
  return (
    <BaseDialog.Description className="text-sm text-muted-foreground">
      {children}
    </BaseDialog.Description>
  );
}

export function DialogFooter({ children }: { children: React.ReactNode }) {
  return <div className="flex justify-end gap-2 mt-6">{children}</div>;
}

export function DialogClose({ children }: { children: React.ReactNode }) {
  return <BaseDialog.Close render={<>{children}</>} />;
}
