import { Share2 } from 'lucide-react'
import instagramLogo from '@/assets/social/instagram.png'
import facebookLogo from '@/assets/social/facebook.png'

// lucide-react 1.x ya no incluye logos de marcas: se usan los mismos de la app Android.
const LOGOS = { instagram: instagramLogo, facebook: facebookLogo }

export default function RedIcon({ red, className = 'h-4 w-4' }) {
  const logo = LOGOS[red]
  if (!logo) return <Share2 className={className} aria-hidden="true" />
  return <img src={logo} alt="" aria-hidden="true" className={`${className} rounded-full object-cover`} />
}
