/**
 * A terminal window. Chrome only — the caller supplies the lines.
 *
 * Extracted because the same frame is wanted anywhere a command is shown, and
 * because the window dressing was drowning the hero's markup.
 */
export function Terminal({
  title = "omega",
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-rule bg-term font-mono text-[13px] leading-relaxed">
      <div className="flex items-center gap-1.5 border-b border-rule px-4 py-2.5">
        <span className="h-2 w-2 rounded-full bg-oxblood/40" />
        <span className="h-2 w-2 rounded-full bg-forest/40" />
        <span className="h-2 w-2 rounded-full bg-ink-muted/30" />
        <span className="label ml-2 text-ink-muted">{title}</span>
      </div>
      <div className="overflow-x-auto px-4 py-4">{children}</div>
    </div>
  );
}

/** One `$ command` with its explanatory line beneath. */
export function TerminalCommand({ cmd, note }: { cmd: string; note?: string }) {
  return (
    <div className="whitespace-pre pb-2.5 last:pb-0">
      <span className="text-oxblood">$ </span>
      <span>{cmd}</span>
      {note && (
        <>
          {"\n"}
          <span className="text-ink-muted">
            {"  "}
            {note}
          </span>
        </>
      )}
    </div>
  );
}
