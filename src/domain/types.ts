export const SUPPORTED_QUESTION_TYPES = [
  "single_choice",
  "true_false",
  "fill_blank",
  "multi_select",
  "ordering",
  "matching",
  "who_said_it",
  "to_whom",
  "reference_detail",
  "negative_choice",
  "sequence_choice",
  "precision",
] as const

export type QuestionType = (typeof SUPPORTED_QUESTION_TYPES)[number]
export type FinalQuestionFamily =
  | "single_choice_direct"
  | "fill_choice"
  | "true_false"
  | "single_choice_contextual"
export type SourceWork = "Daniel" | "Profetas y Reyes"

export type QuestionOption = { id: string; text: string }
export type BankProfileId =
  | "legacy-v1"
  | "master-v2"
  | "prep-v3"
  | "curated-v4"
  | "massive-v5"
  | "consolidation-v5"
export type BankSelection = BankProfileId | "mixed"
export type DifficultyBand = "BASIC" | "MEDIUM" | "HARD" | "EXPERT" | "UNRATED"
export type AnswerMode = "option_id" | "canonical_text"
export type SelectionStrategy = "coverage-cycle" | "random-balanced" | "sequential-blocks" | "adaptive"
export type MatchItem = { id: string; text: string }
export type CorrectMatch = { left: string; right: string }

export type QuestionSource = {
  work: SourceWork
  version: string
  chapter: number
  reference: string
}

export type Question = {
  id: string
  bankId?: string
  type: QuestionType
  family?: FinalQuestionFamily
  difficulty: 1 | 2 | 3 | 4 | 5
  source: QuestionSource
  tags: string[]
  factKey: string
  question: string
  options: QuestionOption[]
  correctAnswer: string[]
  bankProfileId?: BankProfileId
  originalDifficulty?: number | string
  difficultyBand?: DifficultyBand
  answerMode?: AnswerMode
  correctAnswerText?: string
  factKeys?: string[]
  metadata?: Record<string, unknown>
  explanation?: string
  trapReason?: string
  memoryCue?: string
  integrative?: boolean
  verified?: boolean
  factId?: string
  variantId?: string
  templateId?: string
  verseOrPage?: string
  sourceSpan?: string
  contextAnchor?: string
  acceptedAnswers?: string[]
  whyDistractorsFail?: Record<string, string>
  sourceQuote?: string
  trapType?: string | null
  blindFinalPool?: boolean
  blindPool?: "A" | "B" | "emergency" | null
  editorialStatus?: "gold" | "silver" | "quarantine"
  qualityScore?: number
  semanticSkill?: string
  leftItems?: MatchItem[]
  rightItems?: MatchItem[]
  correctMatches?: CorrectMatch[]
}

export type QuestionExposure = {
  exposureKey: string
  factId: string
  variantId: string
  questionKey: string
  exposures: number
  correct: number
  incorrect: number
  totalResponseTimeMs: number
  averageResponseTimeMs: number
  lastSeenAt: number
  lastSelectedAnswer: string | null
  lastErrorType: string | null
  evidence?: Record<"practice" | "cold" | "deferred" | "blind", { attempts: number; correct: number }>
}

export type ExposureAttempt = {
  factId: string
  variantId: string
  questionKey: string
  timestamp: number
  isCorrect: boolean
  responseTimeMs: number
  selectedAnswer: string | null
  errorType: string | null
  exposureKind?: "practice" | "cold" | "deferred" | "blind"
}

export type QuestionSessionQuery = {
  bankId?: string
  chapters?: number[]
  difficultyBands?: DifficultyBand[]
  types?: QuestionType[]
  includeBlind?: boolean
  limit: number
}

export type Bank = {
  bankId: string
  bankProfileId?: BankProfileId
  name: string
  sourceWork: SourceWork
  sourceVersion: string
  schemaVersion: "1.0" | "2.0"
  importedAt: number
  fingerprint: string
  sourceFileName?: string
  raw?: Record<string, unknown>
  questions: Question[]
}

export type AttemptReason = "correct" | "incorrect" | "timeout" | "unanswered"
export type AttemptContext = "practice" | "simulation"
export type AttemptRecord = {
  timestamp: number
  isCorrect: boolean
  wasAnswered: boolean
  responseTimeMs: number
  reason: AttemptReason
  context?: AttemptContext
}

export type QuestionProgress = {
  questionKey: string
  timesSeen: number
  timesCorrect: number
  timesIncorrect: number
  timesUnanswered: number
  currentCorrectStreak: number
  averageResponseTimeMs: number
  bestResponseTimeMs: number | null
  lastResponseTimeMs: number | null
  lastSeenAt: number | null
  masteryScore: number
  favorite: boolean
  markedDifficult: boolean
  reported: boolean
  history: AttemptRecord[]
}

export type AnswerValue = string | string[] | Record<string, string> | null | undefined

export type EvaluationResult = {
  isCorrect: boolean
  wasAnswered: boolean
  responseTimeMs: number
  reason: AttemptReason
}

export type SessionMode =
  | "learn"
  | "smart-review"
  | "simulation"
  | "final"
  | "training"
  | "errors"
  | "difficult"
  | "speed"
  | "new"
  | "mixed"
  | "chapter"
  | "championship"

export type QuestionStatus = "all" | "new" | "failed" | "difficult" | "mastered" | "favorite"

export type SessionConfig = {
  mode: SessionMode
  count: number | "all"
  sourceWorks: SourceWork[]
  chapters: number[]
  difficulties: number[]
  types: QuestionType[]
  statuses: QuestionStatus[]
  shuffleQuestions: boolean
  shuffleOptions: boolean
  perQuestionSeconds: number | null
  totalSeconds: number | null
  bankSelection?: BankSelection
  strategy?: SelectionStrategy
  difficultyBands?: DifficultyBand[]
  sequentialBlock?: number
  trainingPresetId?: string
  includeBlind?: boolean
  massive?: boolean
}

export type CoverageCycle = {
  poolKey: string
  cycleId: string
  remainingQuestionKeys: string[]
  seenQuestionKeys: string[]
  totalPoolSize: number
  createdAt: number
  updatedAt: number
}

export type ActiveRound = {
  id: "active"
  startedAt: number
  updatedAt: number
  currentIndex: number
  questionKeys: string[]
  questionSnapshots?: Question[]
  answers: SessionAnswer[]
  config: SessionConfig
  selectionSummary?: SelectionSummary
}

export type SessionAnswer = {
  questionKey: string
  answer: AnswerValue
  result: EvaluationResult
  responseTimeMs: number
  favorite?: boolean
  markedDifficult?: boolean
  reported?: boolean
  reportReason?: string
}

export type Session = {
  id: string
  startedAt: number
  completedAt: number
  mode: SessionMode
  context?: AttemptContext
  config: SessionConfig
  questionKeys: string[]
  answers: SessionAnswer[]
  score: number
  durationMs: number
  selectionSummary?: SelectionSummary
}

export type SelectionSummary = {
  strategy: SelectionStrategy
  poolKey?: string
  cycleId?: string
  seen?: number
  remaining?: number
  total?: number
}

export type ValidationError = {
  code: string
  path: string
  message: string
  questionId?: string
}

export type ValidationResult = {
  valid: boolean
  errors: ValidationError[]
  questionCount: number
  sourceName: string
  raw?: Record<string, unknown>
}

export type BackupPayload = {
  backupVersion: "2.0"
  exportedAt: number
  banks: Bank[]
  progress: QuestionProgress[]
  sessions: Session[]
  reports: QuestionReport[]
  preferences: Preferences
  coverageCycles: CoverageCycle[]
  activeRound: ActiveRound | null
  factMastery?: import("@/domain/fact-mastery").FactMastery[]
  legacyEvents?: LegacyHistoryEvent[]
}

export type LegacyHistoryEvent = {
  id: string
  sourceQuestionKey: string
  reason: "no_match" | "ambiguous_match" | "missing_question"
  progress: QuestionProgress
  preservedAt: number
}

export type MigrationBackup = {
  id: string
  createdAt: number
  progress: QuestionProgress[]
  sessions: Session[]
  reports: QuestionReport[]
}

export type BlindUsage = {
  factId: string
  pool: "A" | "B" | "emergency"
  consumedAt: number
  sessionId: string
}

export type QuestionReport = {
  id: string
  questionKey: string
  bankId?: string
  questionId?: string
  question: Question
  reportedAt: number
  answer: AnswerValue
  response: EvaluationResult | null
  reason: string
}

export type Preferences = {
  theme: "light" | "dark" | "system"
  lastMode: SessionMode
  reducedMotion: boolean
  lastBankSelection: BankSelection
}
