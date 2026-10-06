import { Link } from 'react-router-dom'
import instagramLogo from '@/assets/social/instagram.png'
import facebookLogo from '@/assets/social/facebook.png'
import { etiquetaRed, formatoMetrica, haceCuanto, metricasDeRed, serieMensual } from '../../services/social'

const LOGOS = { instagram: instagramLogo, facebook: facebookLogo }

/**
 * Tarjeta del dashboard por red: logo grande, totales de la última lectura de cada
 * publicación y publicaciones por mes. Lo que Meta no informó se muestra "sin dato".
 */
export default function NetworkPanel({ red, datos, porMes, puedeConectar }) {
  const nombre = etiquetaRed(red)
  const { principales, secundarias } = metricasDeRed(red)
  const total = datos?.publicaciones ?? 0

  return (
    <article className="flex flex-col rounded-3xl border border-outline-variant bg-white p-6 shadow-sm sm:p-8">
      <header className="flex items-center gap-4">
        <img src={LOGOS[red]} alt="" aria-hidden="true" className="h-14 w-14 rounded-2xl shadow-md" />
        <div className="min-w-0">
          <h2 className="text-2xl font-semibold text-on-surface">{nombre}</h2>
          <p className="text-sm text-on-surface-variant">
            {total === 1 ? '1 publicación' : `${total} publicaciones`}
            {total > 0 && ` · ${datos.publicaciones_mes} este mes`}
          </p>
        </div>
      </header>

      {total === 0 ? (
        <div className="mt-6 flex flex-1 flex-col justify-center rounded-2xl bg-surface-container-low px-6 py-8">
          <p className="font-semibold text-on-surface">Aún no hay publicaciones en {nombre}</p>
          <p className="mt-1 max-w-sm text-sm text-on-surface-variant">
            Aparecen aquí cuando el cliente aprueba una campaña que tiene {nombre} como destino.
          </p>
          {puedeConectar && (
            <Link to="/settings" className="mt-3 text-sm font-semibold text-primary hover:underline">
              Revisar redes conectadas
            </Link>
          )}
        </div>
      ) : (
        <>
          <dl className="mt-8 grid grid-cols-[repeat(auto-fit,minmax(7.5rem,1fr))] gap-4">
            {principales.map(([campo, etiqueta]) => (
              <Cifra key={campo} etiqueta={etiqueta} valor={datos[campo]} grande />
            ))}
          </dl>
          <dl className="mt-6 flex flex-wrap gap-x-8 gap-y-3 border-t border-outline-variant/60 pt-5">
            {secundarias.map(([campo, etiqueta]) => (
              <Cifra key={campo} etiqueta={etiqueta} valor={datos[campo]} />
            ))}
          </dl>
          <BarrasPorMes serie={serieMensual(porMes, red)} nombre={nombre} />
          <p className="mt-5 text-xs text-on-surface-variant">
            {datos.con_metricas === 0
              ? 'Meta todavía no entregó métricas de estas publicaciones.'
              : `Totales de ${datos.con_metricas} de ${total} ${total === 1 ? 'publicación' : 'publicaciones'}` +
                ` · leídos de Meta ${haceCuanto(datos.metricas_al)}`}
          </p>
        </>
      )}
    </article>
  )
}

function Cifra({ etiqueta, valor, grande = false }) {
  const sinDato = valor === null || valor === undefined
  return (
    <div className="min-w-0">
      <dt className="text-sm text-on-surface-variant">{etiqueta}</dt>
      <dd
        className={
          sinDato
            ? `mt-1 font-medium text-on-surface-variant ${grande ? 'text-base leading-10' : 'text-sm'}`
            : `mt-1 font-bold tabular-nums text-on-surface ${grande ? 'text-4xl tracking-tight' : 'text-base'}`
        }
      >
        {formatoMetrica(valor)}
      </dd>
    </div>
  )
}

function BarrasPorMes({ serie, nombre }) {
  const maximo = Math.max(1, ...serie.map((m) => m.total))
  const resumen = serie.map((m) => `${m.etiqueta}: ${m.total}`).join(', ')
  return (
    <figure className="mt-8">
      <figcaption className="text-sm font-medium text-on-surface">Publicaciones por mes</figcaption>
      <div className="mt-3 flex h-28 items-end gap-3" role="img" aria-label={`Publicaciones en ${nombre} por mes: ${resumen}`}>
        {serie.map((m, i) => {
          const actual = i === serie.length - 1
          return (
            <div key={m.mes} className="flex h-full flex-1 flex-col items-center gap-1.5">
              <div className="flex w-full flex-1 flex-col items-center justify-end gap-1">
                {m.total > 0 && (
                  <span className="text-xs font-semibold tabular-nums text-on-surface-variant">{m.total}</span>
                )}
                <div
                  className={`w-full max-w-10 rounded-t-md ${
                    m.total === 0 ? 'bg-surface-container-high' : actual ? 'bg-primary' : 'bg-primary/45'
                  }`}
                  style={{ height: m.total === 0 ? 3 : `${Math.max(10, (m.total / maximo) * 78)}%` }}
                />
              </div>
              <span className={`text-xs ${actual ? 'font-semibold text-on-surface' : 'text-on-surface-variant'}`}>
                {m.etiqueta}
              </span>
            </div>
          )
        })}
      </div>
    </figure>
  )
}
