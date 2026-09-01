#!/usr/bin/env python3
"""
Updates progress.json and progress.md for competitive-v16 increment.
"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def update_progress():
    work_dir = ROOT / ".work" / "competitive-v16"
    manifest = json.loads((ROOT / "public" / "banks" / "final-2026" / "manifest.json").read_text(encoding="utf-8"))

    progress_data = {
        "contract": "CB2026_COMPETITIVE_V16_PROGRESS_V1",
        "branch": "antigravity/r2-completion-r3-calibrated-v16",
        "public_questions": manifest["gold_questions"], # 3,692
        "total_canonical_facts": manifest["unique_facts"], # 2,217
        "shards_count": len(manifest["shards"]),
        "r2_unique_facts_covered": 1210,
        "r2_unique_facts_remaining": 1007,
        "r3_candidates_generated": 60,
        "r3_competitive_accept": 0,
        "r3_downgraded_to_coverage": 139, # 80 from Wave 2 + 59 from Pilot R3
        "r3_rewrite": 0,
        "r3_reject": 1,
        "translation_noise_competitive_accept": 0,
        "deployments": [
            {
                "deployment_id": "dpl_ELgNw4QG8r6c8tHFvNQojQCjWByb",
                "public_questions": 3692,
                "shards": 18,
                "failures": 0,
                "url": "https://conexion-biblica-2026.vercel.app",
                "build_id": manifest["build_id"]
            }
        ],
        "current_status": "WAVE_3_R2_PROMOTED_PILOT_R3_AUDITED"
    }

    (work_dir / "progress.json").write_text(json.dumps(progress_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_content = f"""# Estado de Ejecución y Progreso (V16)

**Rama de Trabajo:** `antigravity/r2-completion-r3-calibrated-v16`  
**Producción:** [https://conexion-biblica-2026.vercel.app](https://conexion-biblica-2026.vercel.app)  
**Deployment Actual:** `dpl_ELgNw4QG8r6c8tHFvNQojQCjWByb`  
**Build ID:** `{manifest['build_id']}`

---

## 1. Contadores Canónicos Principales

| Métrica | Estado Previo | Wave 3 Increment | Total Actual |
| :--- | :---: | :---: | :---: |
| **Preguntas Públicas** | 3,452 | +240 | **3,692** |
| **Hechos Canónicos Cubiertos** | 2,217 | — | **2,217** |
| **Hechos con Variante R2 Aprobada** | 970 | +240 | **1,210** |
| **Hechos R2 Pendientes** | 1,247 | -240 | **1,007** |
| **R3 Candidatas Generadas** | 0 | +60 (Piloto) | **60** |
| **R3 COMPETITIVE_ACCEPT** | 0 | 0 | **0** (de 1,315) |
| **R3 Degradadas a Cobertura** | 80 | +59 | **139** |
| **R3 Rechazadas / En Revisión** | 0 | +1 | **1** |
| **Shards Públicos** | 18 | 18 | **18 shards** |

---

## 2. Hallazgos del Piloto R3 (60 Candidatas)
- **Evaluación Dual Ciega (A1 y A2):**
  - Competidor A1: 39 EASY, 21 MEDIUM, 0 HARD, 0 EXPERT.
  - Competidor A2: 43 EASY, 17 MEDIUM, 0 HARD, 0 EXPERT.
  - Auditor B: 60/60 respaldo textual y 0 segundas opciones defendibles.
- **Dictamen de Puerta de Calibración:**
  - Al obtener 0 HARD/EXPERT en doble revisión ciega, se clasifica honestamente el lote como **59 R3_DOWNGRADED_TO_COVERAGE** y **0 R3_COMPETITIVE_ACCEPT**.
  - No se escala R3 ciegamente hasta ajustar la complejidad combinatoria en el siguiente lote piloto.

---

## 3. Promoción de Wave 3 R2 (240 Preguntas)
- **Ciclos Promovidos:** Ciclos 36 a 43 en `content/competitive-v13/release2/applied/` (acumulado: 1,224 ítems aprobados).
- **Compilación de Shards:** 3,692 preguntas distribuidas en los 18 shards en `public/banks/final-2026/questions/`.
- **Índice de Revisión:** Enriquecido con procedencia individual para los 240 ítems (3,692 registros en `review-index.json`).
- **Pruebas y Auditoría:**
  - Vitest: 62 archivos de prueba, 434 tests (100% PASSED).
  - Auditoría Remota (`audit-live-final-bank.mjs`): 0 fallos (`"failures": []`).

---

## 4. Siguiente Acción Inmediata
- **Carril A:** Preparar e iniciar **Wave 4 R2 Cobertura** (240 hechos de los 1,007 restantes: Dan 7–12 remanente, PR 39–44, Dan 1–6).
- **Carril B:** Segundo piloto R3 enfocado en relaciones cronológicas cruzadas y atribución exegética de alta complejidad.
"""
    (work_dir / "progress.md").write_text(md_content, encoding="utf-8")
    print("Updated progress.json and progress.md successfully.")

if __name__ == "__main__":
    update_progress()
