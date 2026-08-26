import { useRef } from "react"
import { ArrowDown, ArrowUp, Check, GripVertical, Link2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { AnswerValue, EvaluationResult, Question } from "@/domain/types"

type RendererProps = {
  question: Question
  value: AnswerValue
  onChange: (value: AnswerValue) => void
  disabled?: boolean
  feedback?: EvaluationResult | null
}

const letters = ["A", "B", "C", "D", "E", "F"]

export function QuestionRenderer({
  question,
  value,
  onChange,
  disabled = false,
  feedback = null,
}: RendererProps) {
  if (question.answerMode === "canonical_text")
    return (
      <CanonicalTextQuestion
        question={question}
        value={value}
        onChange={onChange}
        disabled={disabled}
        feedback={feedback}
      />
    )
  if (question.type === "matching")
    return (
      <MatchingQuestion
        question={question}
        value={value}
        onChange={onChange}
        disabled={disabled}
        feedback={feedback}
      />
    )
  if (question.type === "ordering")
    return (
      <OrderingQuestion
        question={question}
        value={value}
        onChange={onChange}
        disabled={disabled}
        feedback={feedback}
      />
    )
  if (question.type === "multi_select")
    return (
      <MultiSelectQuestion
        question={question}
        value={value}
        onChange={onChange}
        disabled={disabled}
        feedback={feedback}
      />
    )
  return (
    <ChoiceQuestion
      question={question}
      value={value}
      onChange={onChange}
      disabled={disabled}
      feedback={feedback}
    />
  )
}

function CanonicalTextQuestion({
  question,
  value,
  onChange,
  disabled,
}: RendererProps) {
  return (
    <fieldset className="min-w-0">
      <legend className="sr-only">{question.question}</legend>
      <label className="flex flex-col gap-2 text-sm font-medium">
        Escribe la respuesta
        <Textarea
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
          placeholder="Respuesta canónica"
          autoComplete="off"
        />
      </label>
    </fieldset>
  )
}

function ChoiceQuestion({
  question,
  value,
  onChange,
  disabled,
  feedback,
}: RendererProps) {
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([])
  const selected =
    typeof value === "string"
      ? value
      : Array.isArray(value)
        ? value[0]
        : undefined
  return (
    <div
      className="grid gap-3"
      role="radiogroup"
      aria-label={question.question}
    >
      {question.options.map((option, index) => {
        const active = option.id === selected
        const isCorrectOption = question.correctAnswer.includes(option.id)
        const showsIncorrectSelection = Boolean(
          feedback && active && !feedback.isCorrect
        )
        const showsCorrectSelection = Boolean(
          feedback && active && feedback.isCorrect
        )
        return (
          <button
            key={option.id}
            ref={(element) => {
              buttonRefs.current[index] = element
            }}
            type="button"
            role="radio"
            disabled={disabled}
            aria-checked={active}
            tabIndex={active || (!selected && index === 0) ? 0 : -1}
            className={`group flex min-h-16 items-center gap-4 rounded-xl border px-4 py-3 text-left transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring motion-reduce:transition-none sm:px-5 ${showsIncorrectSelection ? "border-destructive bg-destructive/5 ring-1 ring-destructive" : isCorrectOption && feedback ? "border-chart-2 bg-chart-2/10 ring-1 ring-chart-2" : active ? "border-primary bg-primary/5 ring-1 ring-primary" : "bg-card hover:bg-muted/50"}`}
            onClick={() => onChange(option.id)}
            onKeyDown={(event) => {
              if (
                !["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(
                  event.key
                )
              )
                return
              event.preventDefault()
              const direction =
                event.key === "ArrowRight" || event.key === "ArrowDown" ? 1 : -1
              const nextIndex =
                (index + direction + question.options.length) %
                question.options.length
              onChange(question.options[nextIndex].id)
              buttonRefs.current[nextIndex]?.focus()
            }}
          >
            <span
              className={`flex size-9 shrink-0 items-center justify-center rounded-lg border text-sm font-semibold ${active ? "border-primary bg-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground"}`}
            >
              {letters[index] ?? option.id}
            </span>
            <span className="flex-1 text-sm leading-6 sm:text-base">
              {option.text}
            </span>
            {active ? (
              <Check
                className="shrink-0 text-primary"
                aria-label="Seleccionada"
              />
            ) : null}
            {feedback && isCorrectOption ? (
              <span className="sr-only">Respuesta correcta</span>
            ) : null}
            {showsIncorrectSelection ? (
              <span className="sr-only">Tu selección fue incorrecta.</span>
            ) : null}
            {showsCorrectSelection ? (
              <span className="sr-only">Tu selección es correcta.</span>
            ) : null}
          </button>
        )
      })}
      {feedback ? (
        <p className="text-sm font-medium" role="status">
          {feedback.isCorrect
            ? "Tu selección es correcta."
            : "Tu selección fue incorrecta."}
        </p>
      ) : null}
    </div>
  )
}

function MultiSelectQuestion({
  question,
  value,
  onChange,
  disabled,
}: RendererProps) {
  const selected = Array.isArray(value) ? value : []
  const toggle = (id: string) =>
    onChange(
      selected.includes(id)
        ? selected.filter((item) => item !== id)
        : [...selected, id]
    )
  return (
    <fieldset className="grid gap-3">
      <legend className="sr-only">{question.question}</legend>
      {question.options.map((option, index) => {
        const active = selected.includes(option.id)
        return (
          <label
            key={option.id}
            className={`flex min-h-16 cursor-pointer items-center gap-4 rounded-xl border px-4 py-3 transition-colors motion-reduce:transition-none sm:px-5 ${active ? "border-primary bg-primary/5" : "bg-card hover:bg-muted/50"}`}
          >
            <Checkbox
              checked={active}
              disabled={disabled}
              onCheckedChange={() => toggle(option.id)}
            />
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted/50 text-xs font-semibold text-muted-foreground">
              {letters[index] ?? option.id}
            </span>
            <span className="text-sm leading-6 sm:text-base">
              {option.text}
            </span>
          </label>
        )
      })}
    </fieldset>
  )
}

function OrderingQuestion({
  question,
  value,
  onChange,
  disabled,
}: RendererProps) {
  const order =
    Array.isArray(value) && value.length
      ? value
      : question.options.map((option) => option.id)
  const move = (index: number, direction: -1 | 1) => {
    const next = [...order]
    const target = index + direction
    if (target < 0 || target >= next.length) return
    ;[next[index], next[target]] = [next[target], next[index]]
    onChange(next)
  }
  return (
    <section aria-label={question.question}>
      <ol className="flex flex-col gap-3">
        {order.map((id, index) => {
          const option = question.options.find((item) => item.id === id)
          if (!option) return null
          return (
            <li
              key={id}
              className="flex items-center gap-2 rounded-xl border bg-card p-3"
            >
              <GripVertical
                className="shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
              <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted text-xs font-semibold">
                {index + 1}
              </span>
              <span className="min-w-0 flex-1 text-sm leading-5">
                {option.text}
              </span>
              <div className="flex gap-1">
                <Button
                  aria-label={`Mover ${option.text} arriba`}
                  disabled={disabled || index === 0}
                  size="icon"
                  variant="ghost"
                  className="min-h-11 min-w-11"
                  onClick={() => move(index, -1)}
                >
                  <ArrowUp data-icon="inline-start" />
                </Button>
                <Button
                  aria-label={`Mover ${option.text} abajo`}
                  disabled={disabled || index === order.length - 1}
                  size="icon"
                  variant="ghost"
                  className="min-h-11 min-w-11"
                  onClick={() => move(index, 1)}
                >
                  <ArrowDown data-icon="inline-start" />
                </Button>
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}

function MatchingQuestion({
  question,
  value,
  onChange,
  disabled,
}: RendererProps) {
  const matches =
    value && !Array.isArray(value) && typeof value === "object"
      ? (value as Record<string, string>)
      : {}
  const setMatch = (left: string, right: string) => {
    const next = { ...matches }
    if (right === "__none") delete next[left]
    else next[left] = right
    onChange(next)
  }
  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="sr-only">{question.question}</legend>
      {(question.leftItems ?? []).map((left) => (
        <div
          key={left.id}
          className="grid items-center gap-3 rounded-xl border bg-card p-3 sm:grid-cols-[1fr_28px_1fr]"
        >
          <span className="text-sm leading-5">{left.text}</span>
          <Link2
            className="hidden text-muted-foreground sm:block"
            aria-hidden="true"
          />
          <Select
            value={matches[left.id] ?? "__none"}
            onValueChange={(right) => setMatch(left.id, right)}
            disabled={disabled}
          >
            <SelectTrigger
              className="min-h-11 w-full"
              aria-label={`Relacionar ${left.text}`}
            >
              <SelectValue placeholder="Selecciona" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="__none">Sin relación</SelectItem>
                {(question.rightItems ?? []).map((right) => (
                  <SelectItem key={right.id} value={right.id}>
                    {right.text}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      ))}
    </fieldset>
  )
}
