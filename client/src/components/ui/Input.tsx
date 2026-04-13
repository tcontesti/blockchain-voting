import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react';

const base =
  'w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-fg placeholder:text-muted transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className = '', ...rest }, ref) => <input ref={ref} {...rest} className={`${base} ${className}`} />,
);
Input.displayName = 'Input';

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className = '', rows = 4, ...rest }, ref) => (
    <textarea ref={ref} rows={rows} {...rest} className={`${base} resize-none ${className}`} />
  ),
);
Textarea.displayName = 'Textarea';

interface LabelProps {
  label: string;
  children: React.ReactNode;
  hint?: string;
}

export function Field({ label, children, hint }: LabelProps) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-muted">{hint}</span>}
    </label>
  );
}
