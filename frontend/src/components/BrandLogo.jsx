export default function BrandLogo({ compact = false, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`} aria-label="NexoMark IA">
      <img src="/nexomark-mark.svg" alt="" className="h-9 w-9 shrink-0" />
      {!compact && (
        <span className="inline-flex items-center gap-1.5 font-extrabold tracking-tight">
          <span className="bg-gradient-to-r from-primary to-cyan-400 bg-clip-text text-transparent">
            NexoMark
          </span>
          <span className="rounded-md bg-primary/12 px-1.5 py-0.5 text-[0.62em] font-extrabold text-primary">
            IA
          </span>
        </span>
      )}
    </span>
  )
}
