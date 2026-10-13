import PlatformIcon from './campaign/PlatformIcon'

/** A platform row inside the shared social-connections card. */
export default function SocialConnectionSection({ platform, name, children }) {
  return (
    <section aria-label={`Conexión con ${name}`} className="py-6 first:pt-0 last:pb-0">
      <h3 className="flex items-center gap-3 text-lg font-semibold text-on-surface">
        <PlatformIcon platform={platform} className="h-6 w-6" />
        {name}
      </h3>
      {children}
    </section>
  )
}
