import { useRef } from "react"
import { Check } from "lucide-react"

import type { AnswerValue, EvaluationResult, Question } from "@/domain/types"

type RendererProps = {
  question: Question
  value: AnswerValue
  onChange: (value: AnswerValue) => void
  disabled?: boolean
  feedback?: EvaluationResult | null
}

const letters = ["A", "B", "C", "D"]

export function QuestionRenderer({
  question,
  value,
  onChange,
  disabled = false,
  feedback = null,
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
      className="grid gap-3 sm:gap-4"
      role="radiogroup"
      aria-label={question.question}
    >
      {question.options.map((option, index) => {
        const active = option.id === selected
        const isCorrectOption = question.correctAnswer.includes(option.id)
        const showsIncorrectSelection = Boolean(
          feedback && active && !feedback.isCorrect,
        )
        const showsCorrectSelection = Boolean(
          feedback && active && feedback.isCorrect,
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
            className={`group flex min-h-16 items-center gap-4 rounded-xl border px-4 py-3.5 text-left transition-[transform,background-color,border-color,box-shadow] duration-200 outline-none active:scale-[0.99] focus-visible:ring-2 focus-visible:ring-ring motion-reduce:transition-none sm:min-h-18 sm:px-5 ${showsIncorrectSelection ? "border-destructive bg-destructive/5 ring-1 ring-destructive" : isCorrectOption && feedback ? "border-chart-2 bg-chart-2/10 ring-1 ring-chart-2" : active ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary" : "bg-card hover:-translate-y-0.5 hover:bg-muted/55"}`}
            onClick={() => onChange(option.id)}
            onKeyDown={(event) => {
              if (
                !["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(
                  event.key,
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
              className={`flex size-9 shrink-0 items-center justify-center rounded-lg border text-sm font-semibold tabular-nums ${active ? "border-primary bg-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground"}`}
            >
              {question.type === "true_false"
                ? option.text.slice(0, 1).toUpperCase()
                : letters[index] ?? option.id}
            </span>
            <span className="flex-1 text-sm leading-6 text-pretty sm:text-base">
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
