import type { Question, SourceWork } from "@/domain/types"

export type StudyDay = 1 | 2 | 3 | 4

export type StudyDayChapterGroup = {
  work: SourceWork
  chapters: number[]
}

export type StudyDayPlan = {
  day: StudyDay
  title: string
  objective: string
  method: string
  chapters: StudyDayChapterGroup[]
}

export const FOUR_DAY_STUDY_PLAN: Record<StudyDay, StudyDayPlan> = {
  1: {
    day: 1,
    title: "Fundamentos y decisiones",
    objective: "Fijar los escenarios, personajes y decisiones de fidelidad que abren ambos materiales.",
    method: "Recuerdo activo + anclas numéricas",
    chapters: [
      { work: "Daniel", chapters: [1, 2, 3] },
      { work: "Profetas y Reyes", chapters: [39] },
    ],
  },
  2: {
    day: 2,
    title: "Humildad, juicio y liberación",
    objective: "Conectar los sueños de Nabucodonosor con el horno y el gobierno de Dios.",
    method: "Intercalado Daniel / Profetas y Reyes",
    chapters: [
      { work: "Daniel", chapters: [4, 5, 6] },
      { work: "Profetas y Reyes", chapters: [40, 41] },
    ],
  },
  3: {
    day: 3,
    title: "Visiones y grandeza verdadera",
    objective: "Distinguir símbolos, reinos y la lección de la verdadera grandeza.",
    method: "Comparación de símbolos + repaso de errores",
    chapters: [
      { work: "Daniel", chapters: [7, 8, 9] },
      { work: "Profetas y Reyes", chapters: [42, 43] },
    ],
  },
  4: {
    day: 4,
    title: "Conflicto final y simulacro",
    objective: "Cerrar Daniel 10–12, conectar la fidelidad con la esperanza y medir velocidad.",
    method: "Recuerdo activo + simulacro final",
    chapters: [
      { work: "Daniel", chapters: [10, 11, 12] },
      { work: "Profetas y Reyes", chapters: [44] },
    ],
  },
}

export function getStudyDay(day: StudyDay): StudyDayPlan {
  const plan = FOUR_DAY_STUDY_PLAN[day]
  return {
    ...plan,
    chapters: plan.chapters.map((group) => ({
      ...group,
      chapters: [...group.chapters],
    })),
  }
}

export function studyDayMatchesQuestion(question: Question, day: StudyDay) {
  return getStudyDay(day).chapters.some(
    (group) => group.work === question.source.work && group.chapters.includes(question.source.chapter),
  )
}

export function chaptersForStudyDay(day: StudyDay) {
  return getStudyDay(day).chapters.flatMap((group) => group.chapters)
}
