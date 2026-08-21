import { ArrowDown, ArrowUp, Check, GripVertical, Link2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { AnswerValue, Question } from "@/domain/types"

type RendererProps = {
  question: Question
  value: AnswerValue
  onChange: (value: AnswerValue) => void
  disabled?: boolean
}

const letters = ["A", "B", "C", "D", "E", "F"]

export function QuestionRenderer({ question, value, onChange, disabled = false }: RendererProps) {
  if (question.answerMode === "canonical_text") return <CanonicalTextQuestion question={question} value={value} onChange={onChange} disabled={disabled} />
  if (question.type === "matching") return <MatchingQuestion question={question} value={value} onChange={onChange} disabled={disabled} />
  if (question.type === "ordering") return <OrderingQuestion question={question} value={value} onChange={onChange} disabled={disabled} />
  if (question.type === "multi_select") return <MultiSelectQuestion question={question} value={value} onChange={onChange} disabled={disabled} />
  return <ChoiceQuestion question={question} value={value} onChange={onChange} disabled={disabled} />
}

function CanonicalTextQuestion({ value, onChange, disabled }: RendererProps) {
  return <label className="flex flex-col gap-2 text-sm font-medium">Escribe la respuesta
    <Textarea
      value={typeof value === "string" ? value : ""}
      onChange={(event) => onChange(event.target.value)}
      disabled={disabled}
      placeholder="Respuesta canónica"
      autoComplete="off"
    />
  </label>
}

function ChoiceQuestion({ question, value, onChange, disabled }: RendererProps) {
  const selected = typeof value === "string" ? value : Array.isArray(value) ? value[0] : undefined
  return <div className="grid gap-3">{question.options.map((option, index) => { const active = option.id === selected; return <button key={option.id} type="button" disabled={disabled} aria-pressed={active} className={`group flex min-h-16 items-center gap-4 rounded-xl border px-4 py-3 text-left transition-colors sm:px-5 ${active ? "border-primary bg-primary/5 ring-1 ring-primary" : "bg-card hover:bg-muted/50"}`} onClick={() => onChange(option.id)}><span className={`flex size-9 shrink-0 items-center justify-center rounded-lg border text-sm font-semibold ${active ? "border-primary bg-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground"}`}>{letters[index] ?? option.id}</span><span className="flex-1 text-sm leading-6 sm:text-base">{option.text}</span>{active ? <Check className="shrink-0 text-primary" aria-label="Seleccionada" /> : null}</button> })}</div>
}

function MultiSelectQuestion({ question, value, onChange, disabled }: RendererProps) {
  const selected = Array.isArray(value) ? value : []
  const toggle = (id: string) => onChange(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id])
  return <div className="grid gap-3">{question.options.map((option, index) => { const active = selected.includes(option.id); return <label key={option.id} className={`flex min-h-16 cursor-pointer items-center gap-4 rounded-xl border px-4 py-3 transition-colors sm:px-5 ${active ? "border-primary bg-primary/5" : "bg-card hover:bg-muted/50"}`}><Checkbox checked={active} disabled={disabled} onCheckedChange={() => toggle(option.id)} /><span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted/50 text-xs font-semibold text-muted-foreground">{letters[index] ?? option.id}</span><span className="text-sm leading-6 sm:text-base">{option.text}</span></label> })}</div>
}

function OrderingQuestion({ question, value, onChange, disabled }: RendererProps) {
  const order = Array.isArray(value) && value.length ? value : question.options.map((option) => option.id)
  const move = (index: number, direction: -1 | 1) => { const next = [...order]; const target = index + direction; if (target < 0 || target >= next.length) return; [next[index], next[target]] = [next[target], next[index]]; onChange(next) }
  return <div className="flex flex-col gap-3" aria-label="Elementos para ordenar">{order.map((id, index) => { const option = question.options.find((item) => item.id === id); if (!option) return null; return <div key={id} className="flex items-center gap-2 rounded-xl border bg-card p-3"><GripVertical className="shrink-0 text-muted-foreground" aria-hidden="true" /><span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted text-xs font-semibold">{index + 1}</span><span className="min-w-0 flex-1 text-sm leading-5">{option.text}</span><div className="flex gap-1"><Button aria-label={`Mover ${index + 1} arriba`} disabled={disabled || index === 0} size="icon" variant="ghost" onClick={() => move(index, -1)}><ArrowUp data-icon="inline-start" /></Button><Button aria-label={`Mover ${index + 1} abajo`} disabled={disabled || index === order.length - 1} size="icon" variant="ghost" onClick={() => move(index, 1)}><ArrowDown data-icon="inline-start" /></Button></div></div> })}</div>
}

function MatchingQuestion({ question, value, onChange, disabled }: RendererProps) {
  const matches = value && !Array.isArray(value) && typeof value === "object" ? value as Record<string, string> : {}
  const setMatch = (left: string, right: string) => { const next = { ...matches }; if (right === "__none") delete next[left]; else next[left] = right; onChange(next) }
  return <div className="flex flex-col gap-3">{(question.leftItems ?? []).map((left) => <div key={left.id} className="grid items-center gap-3 rounded-xl border bg-card p-3 sm:grid-cols-[1fr_28px_1fr]"><span className="text-sm leading-5">{left.text}</span><Link2 className="hidden text-muted-foreground sm:block" aria-hidden="true" /><Select value={matches[left.id] ?? "__none"} onValueChange={(right) => setMatch(left.id, right)} disabled={disabled}><SelectTrigger aria-label={`Relacionar ${left.text}`}><SelectValue placeholder="Selecciona" /></SelectTrigger><SelectContent><SelectGroup><SelectItem value="__none">Sin relación</SelectItem>{(question.rightItems ?? []).map((right) => <SelectItem key={right.id} value={right.id}>{right.text}</SelectItem>)}</SelectGroup></SelectContent></Select></div>)}</div>
}
