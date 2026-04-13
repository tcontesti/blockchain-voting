import type { HTMLAttributes } from 'react';

export function Card({ className = '', ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...rest}
      className={`rounded-2xl border border-border bg-surface p-6 shadow-md backdrop-blur-sm ${className}`}
    />
  );
}
