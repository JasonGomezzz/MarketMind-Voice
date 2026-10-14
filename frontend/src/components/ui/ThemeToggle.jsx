import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { Button } from '@/components/ui/button'

export default function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme()
  const Icon = isDark ? Sun : Moon
  return (
    <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0"
      onClick={toggleTheme} aria-label={isDark ? 'Activar tema claro' : 'Activar tema oscuro'}>
      <Icon className="h-4 w-4" aria-hidden="true" />
    </Button>
  )
}
