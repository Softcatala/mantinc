#!/usr/bin/env python3
"""Deterministic generator for the `harder` category of Catalan Drift.

Builds 60 adversarial items that combine the three pressure patterns which
produced statistically clear failures on cloud models when explored on the
`stress` prototype:

- template_es: Spanish reusable-template headers (ASUNTO/SITUACIÓN/…) in
  prior turns plus a prior Spanish assistant.
- template_mixed: Mixed ES/EN section headers over trilingual body content.
- short_implicit: Long ES/EN source paragraph followed by a short Catalan
  task without an explicit language instruction.

Each pattern contributes 20 items rotated across 20 (persona, workflow,
domain) scenarios (10 pime → wraps → 10 administracio/usuari_final mix).

Run: python scripts/build_harder.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/prompts_harder.yaml"
SOURCE_YAML = "data/prompts_harder.yaml"

PATTERN_COMMENT = {
    "template_es": "Spanish reusable-template pressure + prior Spanish assistant.",
    "template_mixed": "Mixed ES/EN section headers over trilingual body content.",
    "short_implicit": "Long ES/EN source paragraph, short Catalan task, no explicit instruction.",
}

# 20 (persona, workflow, domain) scenarios. Each carries ES + EN wording of
# the same underlying facts so template_es/template_mixed/short_implicit can
# all reuse them.
SCENARIOS: list[dict[str, Any]] = [
    {
        "persona": "pime",
        "workflow": "support_reply",
        "ca_intro": "Hem de respondre un client que té problemes amb escàners de magatzem.",
        "es_terms": "escáneres pareados, pérdida bluetooth, etiquetas de almacén, versión de firmware y modo offline",
        "en_terms": "scanner pairing, bluetooth drops, warehouse labels, firmware version and offline mode",
        "ca_task_short": "Fes la resposta.",
        "ca_task_full": "Escriu la resposta de suport amb comprovacions, dades requerides, mesura temporal i escalat.",
    },
    {
        "persona": "pime",
        "workflow": "client_reply",
        "ca_intro": "Un client demana condicions especials per una comanda urgent.",
        "es_terms": "pedido urgente, descuento adicional, entrega garantizada antes del cierre de mes y factura consolidada",
        "en_terms": "rush order, additional discount, guaranteed delivery before month-end and consolidated invoice",
        "ca_task_short": "Redacta la resposta.",
        "ca_task_full": "Redacta la resposta al client amb fermesa, condicions concretes i una alternativa oberta.",
    },
    {
        "persona": "pime",
        "workflow": "client_delay_update",
        "ca_intro": "Hem d'informar un client d'un retard en la instal·lació d'un rètol.",
        "es_terms": "rótulo personalizado, instalación aplazada, penalización contractual, factura retenida y apertura comercial",
        "en_terms": "custom sign, delayed installation, contractual penalty, invoice on hold and store opening",
        "ca_task_short": "Prepara el correu.",
        "ca_task_full": "Escriu un correu breu al client amb assumpte, situació, nova previsió i proper pas.",
    },
    {
        "persona": "pime",
        "workflow": "support_reply",
        "ca_intro": "Un client ha importat un catàleg nou i ha detectat problemes.",
        "es_terms": "catálogo incompleto, imágenes cruzadas, stock desactualizado, categorías vacías y plantilla modificada",
        "en_terms": "incomplete catalog, swapped images, outdated stock, empty categories and modified template",
        "ca_task_short": "Contesta.",
        "ca_task_full": "Prepara una resposta de suport sobre el catàleg, la plantilla, la mostra, l'estoc, les imatges i el possible escalat.",
    },
    {
        "persona": "pime",
        "workflow": "project_status",
        "ca_intro": "Hem d'actualitzar direcció sobre l'estat d'una integració comptable.",
        "es_terms": "integración contable en pruebas, desviación de alcance, reunión de desbloqueo, impacto en calendario y decisión sobre coste adicional",
        "en_terms": "accounting integration in testing, scope drift, unblocking meeting, calendar impact and decision on additional cost",
        "ca_task_short": "Escriu-ho.",
        "ca_task_full": "Escriu una actualització executiva amb resum, avenços, bloquejos, impacte, decisions i riscos.",
    },
    {
        "persona": "pime",
        "workflow": "complaint_response",
        "ca_intro": "Un client ens demana ajuda amb una reclamació a una asseguradora.",
        "es_terms": "siniestro denegado, informe pericial pendiente, plazo de alegaciones, prima al día y cobertura contractual",
        "en_terms": "claim denied, pending expert report, allegation period, premium up to date and contractual coverage",
        "ca_task_short": "Redacta la reclamació.",
        "ca_task_full": "Redacta una reclamació formal amb cronologia, documents, petició concreta i termini.",
    },
    {
        "persona": "pime",
        "workflow": "support_reply",
        "ca_intro": "Un comerç no pot quadrar cobraments de final de dia.",
        "es_terms": "cierre del datáfono, comprobante ausente, lote offline, autorización duplicada y conciliación bancaria",
        "en_terms": "payment terminal settlement, missing receipt, offline batch, duplicate authorization and bank reconciliation",
        "ca_task_short": "Prepara la resposta.",
        "ca_task_full": "Prepara la resposta de suport amb comprovacions, mesura temporal, dades requerides i escalat.",
    },
    {
        "persona": "pime",
        "workflow": "procurement_note",
        "ca_intro": "Hem de decidir sobre la renovació d'un servei de correu corporatiu.",
        "es_terms": "renovación de licencias, aumento del precio, migración de buzones, alta de dominios y auditoría de accesos",
        "en_terms": "license renewal, price increase, mailbox migration, domain onboarding and access audit",
        "ca_task_short": "Escriu la nota.",
        "ca_task_full": "Escriu la nota interna amb necessitat, opcions, riscos i propera decisió.",
    },
    {
        "persona": "pime",
        "workflow": "study_plan",
        "ca_intro": "Volem preparar un pla de formació breu per a l'equip d'atenció al client.",
        "es_terms": "formación práctica, gestión de escalados, protocolo de tono, guías de producto y simulacros grabados",
        "en_terms": "practical training, escalation handling, tone protocol, product guides and recorded simulations",
        "ca_task_short": "Fes el pla.",
        "ca_task_full": "Prepara un pla de formació amb objectius, sessions, materials i seguiment.",
    },
    {
        "persona": "pime",
        "workflow": "service_summary",
        "ca_intro": "Volem preparar una proposta breu de servei gestionat per a un client nou.",
        "es_terms": "servicio gestionado, alcance funcional, indicadores de nivel, ventana de mantenimiento y compromiso de respuesta",
        "en_terms": "managed service, functional scope, service level indicators, maintenance window and response commitment",
        "ca_task_short": "Fes el resum.",
        "ca_task_full": "Prepara un resum executiu del servei amb abast, indicadors, riscos i properes passes.",
    },
    {
        "persona": "administracio",
        "workflow": "citizen_response",
        "ca_intro": "L'ajuntament ha de contestar una reclamació sobre una taxa duplicada.",
        "es_terms": "tasa duplicada, bonificación no aplicada, registro de entrada, respuesta escrita y plazo administrativo",
        "en_terms": "duplicated fee, bonus not applied, entry registration, written response and administrative deadline",
        "ca_task_short": "Fes la resposta.",
        "ca_task_full": "Redacta la resposta municipal amb reconeixement, comprovacions, documentació útil i canal de seguiment.",
    },
    {
        "persona": "administracio",
        "workflow": "public_notice",
        "ca_intro": "Hem d'avisar el veïnat d'un tall temporal per una obra a la calçada.",
        "es_terms": "corte de tráfico, desvío peatonal, señalización provisional, ruido controlado y retirada temporal de contenedores",
        "en_terms": "traffic closure, pedestrian detour, temporary signage, controlled noise and temporary container removal",
        "ca_task_short": "Prepara l'avís.",
        "ca_task_full": "Prepara un avís públic amb calendari, afectacions, alternativa i canal d'informació.",
    },
    {
        "persona": "administracio",
        "workflow": "public_project_status",
        "ca_intro": "Hem d'actualitzar l'estat de les obres d'una piscina municipal.",
        "es_terms": "obras de rehabilitación, retraso de suministros, junta técnica, plazo revisado y comunicación a familias",
        "en_terms": "renovation works, supply delay, technical committee, revised deadline and family communication",
        "ca_task_short": "Fes l'actualització.",
        "ca_task_full": "Prepara una actualització pública amb estat, avenços, retards, decisions i propera revisió.",
    },
    {
        "persona": "administracio",
        "workflow": "procurement_note",
        "ca_intro": "Cal justificar una contractació urgent d'interpretació de llengua de signes.",
        "es_terms": "intérprete de lengua de signos, urgencia sobrevenida, acto abierto, presupuesto limitado y confirmación del proveedor",
        "en_terms": "sign language interpreter, unforeseen urgency, open event, limited budget and confirmed vendor",
        "ca_task_short": "Redacta la nota.",
        "ca_task_full": "Redacta la nota de contractació amb justificació, riscos, controls i proper tràmit.",
    },
    {
        "persona": "administracio",
        "workflow": "community_health_bulletin",
        "ca_intro": "Hem de preparar un butlletí per un episodi de calor extrema.",
        "es_terms": "ola de calor, población vulnerable, puntos frescos, hidratación reforzada y alerta hospitalaria",
        "en_terms": "heat wave, vulnerable residents, cooling centres, enhanced hydration and hospital alert",
        "ca_task_short": "Fes el butlletí.",
        "ca_task_full": "Redacta un butlletí públic amb recomanacions, punts frescs, telèfons i canals d'informació.",
    },
    {
        "persona": "administracio",
        "workflow": "privacy_guidance",
        "ca_intro": "Hem d'orientar una petició ciutadana d'accés a expedients.",
        "es_terms": "solicitud de acceso, datos personales de terceros, anonimización previa, plazo de resolución y motivación del interés",
        "en_terms": "access request, third-party personal data, prior anonymisation, resolution deadline and interest justification",
        "ca_task_short": "Prepara la resposta.",
        "ca_task_full": "Prepara la resposta amb reconeixement, marc legal, requisits i propera passa.",
    },
    {
        "persona": "administracio",
        "workflow": "complaint_response",
        "ca_intro": "Hem de respondre una família preocupada per una beca de menjador.",
        "es_terms": "expediente incompleto, cita anulada, documentación ya entregada, dificultad para subsanar y preocupación por el inicio del curso",
        "en_terms": "incomplete file, cancelled appointment, previously submitted documents, difficulty amending and worry about school start",
        "ca_task_short": "Contesta.",
        "ca_task_full": "Redacta la resposta amb reconeixement, comprovacions, requisits, calendari i canal de contacte.",
    },
    {
        "persona": "usuari_final",
        "workflow": "complaint_response",
        "ca_intro": "Vull reclamar a una agència de viatges perquè ha canviat l'hotel reservat.",
        "es_terms": "cambio de hotel, categoría inferior, documentos adjuntos, solución demandada y plazo de respuesta",
        "en_terms": "hotel change, lower category, attached documents, requested solution and response deadline",
        "ca_task_short": "Redacta la reclamació.",
        "ca_task_full": "Escriu una reclamació formal amb fets, diferències de servei, documents, petició i termini.",
    },
    {
        "persona": "usuari_final",
        "workflow": "complaint_response",
        "ca_intro": "Vull reclamar al gimnàs perquè no han aplicat correctament la baixa.",
        "es_terms": "gimnasio, baja tramitada, cuota cobrada, permanencia discutida y acceso ya bloqueado",
        "en_terms": "gym membership, cancellation processed, fee charged, disputed lock-in and access already blocked",
        "ca_task_short": "Redacta la reclamació.",
        "ca_task_full": "Prepara la reclamació amb fets, import, documents aportats i termini de resposta.",
    },
    {
        "persona": "usuari_final",
        "workflow": "privacy_guidance",
        "ca_intro": "Vull vendre un televisor connectat i vull esborrar-ne les dades personals.",
        "es_terms": "aplicaciones instaladas, micrófono activado, historial de visualización, cuentas vinculadas y restablecimiento de fábrica",
        "en_terms": "installed apps, active microphone, viewing history, linked accounts and factory reset",
        "ca_task_short": "Dona'm els passos.",
        "ca_task_full": "Dona'm una guia amb els passos ordenats i les comprovacions finals.",
    },
]

assert len(SCENARIOS) == 20, "SCENARIOS must contain exactly 20 items"


def _base_row(pattern: str, index: int, scenario: dict[str, Any], source_lang: str) -> dict[str, Any]:
    return {
        "id": f"cd_harder_{index:03d}",
        "category": "harder",
        "source_dataset_yaml": SOURCE_YAML,
        "harder_variant": pattern,
        "persona": scenario["persona"],
        "workflow": scenario["workflow"],
        "source_lang": source_lang,
        "target_lang": "ca",
    }


def render_template_es(index: int, scenario: dict[str, Any], row_index: int) -> dict[str, Any]:
    row = _base_row("template_es", row_index, scenario, "es-ca")
    row["conversation"] = [
        {"role": "user", "content": scenario["ca_intro"]},
        {
            "role": "assistant",
            "content": "Podem preparar una resposta clara amb els fets, els riscos i la propera passa.",
        },
        {
            "role": "user",
            "content": f"El cliente/proveedor menciona: {scenario['es_terms']}.",
        },
        {
            "role": "assistant",
            "content": "De acuerdo. Mantendré el propósito, la estructura solicitada y todos los detalles relevantes.",
        },
        {
            "role": "user",
            "content": "Plantilla reutilizable:\nASUNTO:\nSITUACIÓN:\nRIESGO:\nACCIÓN INMEDIATA:\nPRÓXIMO PASO:",
        },
        {
            "role": "assistant",
            "content": "De acuerdo. Haré la revisión final antes de cerrar.",
        },
    ]
    row["prompt"] = scenario["ca_task_full"]
    return row


def render_template_mixed(index: int, scenario: dict[str, Any], row_index: int) -> dict[str, Any]:
    row = _base_row("template_mixed", row_index, scenario, "es-ca")
    row["conversation"] = [
        {"role": "user", "content": scenario["ca_intro"]},
        {
            "role": "assistant",
            "content": "Podem separar els fets confirmats, els riscos i la propera passa.",
        },
        {
            "role": "user",
            "content": (
                f"The team says: {scenario['en_terms']}. "
                f"El resumen ejecutivo insiste en: {scenario['es_terms']}."
            ),
        },
        {
            "role": "assistant",
            "content": "Understood. Mantendré la estructura solicitada y todos los detalles relevantes.",
        },
        {
            "role": "user",
            "content": (
                "Plantilla reusable (mixed headers):\n"
                "ASUNTO / SUBJECT:\n"
                "SITUACIÓN / SITUATION:\n"
                "RIESGO / RISK:\n"
                "ACCIÓN INMEDIATA / IMMEDIATE ACTION:\n"
                "PRÓXIMO PASO / NEXT STEP:"
            ),
        },
        {
            "role": "assistant",
            "content": "OK. I will do la revisión final antes de cerrar.",
        },
    ]
    row["prompt"] = scenario["ca_task_full"]
    return row


def render_short_implicit(index: int, scenario: dict[str, Any], row_index: int) -> dict[str, Any]:
    use_english = index % 2 == 1
    source_lang = "en-ca" if use_english else "es-ca"
    row = _base_row("short_implicit", row_index, scenario, source_lang)
    if use_english:
        source_line = f'Source: "{scenario["en_terms"]}."'
    else:
        source_line = f'Font (castellà): "{scenario["es_terms"]}."'
    row["prompt"] = f"{source_line}\n\n{scenario['ca_task_short']}"
    return row


RENDERERS = [
    render_template_es,
    render_template_mixed,
    render_short_implicit,
]


def build() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_index = 1
    for renderer in RENDERERS:
        for i, scenario in enumerate(SCENARIOS):
            rows.append(renderer(i, scenario, row_index))
            row_index += 1
    return rows


def main() -> None:
    rows = build()
    assert len(rows) == 60, f"expected 60 harder items, got {len(rows)}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        yaml.safe_dump(rows, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} items to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
