import { Check, Clock3, X } from "lucide-react"

import type { AnswerValue, Question } from "@/domain/types"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

function selectedText(question: Question, answer: AnswerValue) {
  if (typeof answer !== "string") return "Sin respuesta"
  return question.options.find((option) => option.id === answer)?.text ?? answer
}

export function AnswerLearningFeedback({
  question,
  selectedAnswer,
  isCorrect,
  onUnderstood,
  onConfused,
  onDoubted,
}: {
  question: Question
  selectedAnswer: AnswerValue
  isCorrect: boolean
  onUnderstood: () => void
  onConfused: () => void
  onDoubted?: () => void
}) {
  const selected = selectedText(question, selectedAnswer)
  const correct = question.correctAnswerText ?? question.correctAnswer
    .map((id) => question.options.find((option) => option.id === id)?.text ?? id)
    .join(", ")
  const contrast = !isCorrect
    ? question.whyDistractorsFail?.[selected] ?? `«${selected}» no completa el contexto exacto pedido.`
    : question.explanation
  return (
    <Alert variant={isCorrect ? "default" : "destructive"}>
      <AlertTitle className="flex items-center gap-2">
        {isCorrect ? <Check /> : <X />}
        {isCorrect ? "Respuesta correcta" : "Corrige este contraste"}
      </AlertTitle>
      <AlertDescription className="grid gap-3">
        <p>Respuesta correcta: <strong>{correct}</strong></p>
        {!isCorrect && contrast ? <p>{contrast}</p> : null}
        <div className="rounded-lg border bg-background/75 p-3 text-sm">
          <strong className="text-foreground">{question.source.reference}</strong>
          {question.sourceQuote ? <p className="mt-1 leading-6">{question.sourceQuote}</p> : null}
        </div>
        <p className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock3 className="size-4" aria-hidden="true" />
          {isCorrect
            ? "Próxima recuperación espaciada: 3 horas o mañana."
            : "Reparación programada: vuelve en 20–40 preguntas y al día siguiente."}
        </p>
        {!isCorrect ? (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={onUnderstood}>Entendido</Button>
            <Button size="sm" variant="secondary" onClick={onConfused}>Todavía lo confundo</Button>
          </div>
        ) : onDoubted ? (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={onDoubted}>Dudé entre dos</Button>
          </div>
        ) : null}
      </AlertDescription>
    </Alert>
  )
}
