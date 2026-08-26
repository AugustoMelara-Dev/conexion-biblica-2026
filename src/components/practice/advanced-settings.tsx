import { useId, type ReactNode } from "react"
import { ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export function AdvancedSettings({
  open,
  onOpenChange,
  children,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: ReactNode
}) {
  const panelId = useId()

  return (
    <Card className="shadow-none">
      <CardHeader className="gap-4 sm:grid-cols-[minmax(0,1fr)_auto]">
        <div>
          <CardTitle>Personaliza tu ronda</CardTitle>
          <CardDescription className="mt-2">
            Dificultad, tipos, estado, orden y tiempo.
          </CardDescription>
        </div>
        <Button
          type="button"
          variant="outline"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => onOpenChange(!open)}
        >
          Configuración avanzada
          <ChevronDown
            className={`transition-transform motion-reduce:transition-none ${open ? "rotate-180" : ""}`}
            aria-hidden="true"
          />
        </Button>
      </CardHeader>
      {open ? (
        <CardContent id={panelId} className="grid gap-6">
          {children}
        </CardContent>
      ) : null}
    </Card>
  )
}
