"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";

/**
 * The page's only two client islands. Everything else renders on the server.
 */

/**
 * Fade-and-lift a section as it enters the viewport.
 *
 * Progressive enhancement, deliberately: the server renders the content
 * *visible*, and the hidden state is only applied once JS confirms it can
 * observe and un-hide again. Without JS, without IntersectionObserver, or with
 * reduced motion requested, the content is simply there — an element must never
 * be left invisible, which is the usual failure mode of scroll reveals.
 *
 * The class toggle goes through the DOM node rather than React state because
 * this is presentation, not application state — nothing else needs to know.
 */
const HIDDEN = ["opacity-0", "translate-y-3"] as const;

export function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || !("IntersectionObserver" in window)) return;

    node.classList.add(...HIDDEN);

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            node.classList.remove(...HIDDEN);
            observer.disconnect();
          }
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.05 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{ transitionDelay: delay ? `${delay}ms` : undefined }}
      className={`transition-[opacity,transform] duration-700 ease-out motion-reduce:transition-none ${className}`}
    >
      {children}
    </div>
  );
}

/**
 * Copy a shell command. The label states what happened rather than apologising
 * for what did not — and it reverts, so the control is never left lying.
 */
export function CopyCommand({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timer);
  }, [copied]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Button
      type="button"
      onClick={copy}
      variant="ghost"
      className="label h-auto cursor-pointer rounded-none border border-rule px-3 py-1.5 text-ink-muted hover:border-oxblood hover:bg-transparent hover:text-oxblood"
    >
      <span aria-live="polite">{copied ? "Copied" : "Copy"}</span>
    </Button>
  );
}
