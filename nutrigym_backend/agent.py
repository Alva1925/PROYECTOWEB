# ============================================================
# agent.py
# Motor de lógica agéntica de NutriGym.
#
# ODS 3 — Salud y Bienestar:
#   Promueve hábitos alimenticios equilibrados, la recuperación
#   muscular y el bienestar integral a través de retroalimentación
#   personalizada y accionable.
# ============================================================

from datetime import date
from typing import Tuple


# ---------------------------------------------------------------------------
# Umbrales de tolerancia porcentual para evitar alertas por diferencias
# mínimas. Un 5 % de margen se considera rango "óptimo".
# ---------------------------------------------------------------------------
TOLERANCIA_PORCENTAJE = 0.05   # ±5 %


def _evaluar_valor(actual: float, meta: float) -> Tuple[str, float]:
    """
    Compara un valor actual contra su meta y devuelve:
      - estado: "déficit" | "exceso" | "óptimo"
      - diferencia: valor absoluto de la brecha (positivo = exceso, negativo = déficit)
    """
    diferencia = actual - meta
    porcentaje_desviacion = abs(diferencia) / meta if meta > 0 else 0

    if porcentaje_desviacion <= TOLERANCIA_PORCENTAJE:
        estado = "óptimo"
    elif diferencia < 0:
        estado = "déficit"
    else:
        estado = "exceso"

    return estado, diferencia


def _mensaje_calorias(estado: str, diferencia: float, meta: int) -> str:
    """Genera el fragmento narrativo sobre el balance calórico."""
    if estado == "óptimo":
        return (
            f"Tu ingesta calórica de hoy está en zona óptima (meta: {meta} kcal). "
            "Mantener este equilibrio energético es clave para el rendimiento y la recuperación."
        )
    elif estado == "déficit":
        faltante = abs(round(diferencia))
        return (
            f"Llevas un déficit de {faltante} kcal respecto a tu meta de {meta} kcal. "
            "Un déficit prolongado puede comprometer tu energía y la síntesis muscular. "
            "Considera añadir una comida o snack nutritivo, como frutas con frutos secos o un batido de proteínas."
        )
    else:  # exceso
        exceso = round(diferencia)
        return (
            f"Has superado tu meta calórica en {exceso} kcal (meta: {meta} kcal). "
            "Si no fue un día de carga intencional, prioriza vegetales, proteínas magras "
            "y reduce ultraprocesados en la próxima comida para reequilibrar."
        )


def _mensaje_proteina(estado: str, diferencia: float, meta: int) -> str:
    """Genera el fragmento narrativo sobre el balance proteico."""
    if estado == "óptimo":
        return (
            f"Tu consumo de proteínas está en rango óptimo (meta: {meta} g). "
            "Esto favorece la reparación muscular y la saciedad sostenida."
        )
    elif estado == "déficit":
        faltante = abs(round(diferencia, 1))
        return (
            f"Te faltan {faltante} g de proteína para alcanzar tu meta de {meta} g. "
            "La proteína es esencial para la recuperación muscular post-entrenamiento. "
            "Puedes completarla con huevo, pollo, legumbres, yogur griego o un suplemento de proteína de suero."
        )
    else:  # exceso
        exceso = round(diferencia, 1)
        return (
            f"Has superado tu meta proteica en {exceso} g (meta: {meta} g). "
            "Aunque no es perjudicial en atletas activos, asegúrate de mantener buena hidratación "
            "y de complementar con carbohidratos para optimizar la síntesis muscular."
        )


def _consejo_ods3(estado_calorias: str, estado_proteina: str) -> str:
    """
    Agrega un consejo holístico alineado al ODS 3 basado en la combinación
    de estados para reforzar hábitos integrales de salud y bienestar.
    """
    if estado_calorias == "óptimo" and estado_proteina == "óptimo":
        return (
            "🌱 ODS 3 | Excelente trabajo hoy. Mantener un balance nutricional consistente "
            "reduce el riesgo de enfermedades crónicas y mejora la calidad de vida a largo plazo. "
            "Recuerda descansar al menos 7-8 horas para maximizar la recuperación."
        )
    elif estado_calorias == "déficit" and estado_proteina == "déficit":
        return (
            "⚠️ ODS 3 | Un bajo aporte tanto calórico como proteico puede afectar tu sistema "
            "inmune y tu salud musculoesquelética. Planifica tus comidas con anticipación "
            "para garantizar un aporte nutricional completo y sostenible."
        )
    elif estado_calorias == "exceso" and estado_proteina == "exceso":
        return (
            "📊 ODS 3 | Revisa la densidad nutricional de tus alimentos. Prioriza alimentos "
            "integrales, frutas, vegetales y proteínas de calidad sobre alimentos procesados "
            "para mantener un peso saludable y prevenir enfermedades metabólicas."
        )
    else:
        return (
            "💡 ODS 3 | Pequeños ajustes diarios generan grandes cambios en tu salud. "
            "Planificar tus comidas con antelación y llevar este registro es en sí mismo "
            "un acto de autocuidado alineado al bienestar sostenible."
        )


# ---------------------------------------------------------------------------
# Función principal del agente
# ---------------------------------------------------------------------------
def evaluar_registro_diario_agente(usuario, registro_diario) -> dict:
    """
    Motor agéntico principal.

    Parámetros:
        usuario         (models.Usuario):       perfil y metas del atleta.
        registro_diario (models.RegistroDiario): consumo acumulado del día.

    Retorna:
        dict compatible con el esquema AgenteResponse.
    """
    # 1. Evaluar balance calórico y proteico
    estado_cal,  diff_cal  = _evaluar_valor(registro_diario.total_calorias,  usuario.meta_calorias)
    estado_prot, diff_prot = _evaluar_valor(registro_diario.total_proteinas, usuario.meta_proteina)

    # 2. Construir mensajes individuales
    msg_calorias = _mensaje_calorias(estado_cal,  diff_cal,  usuario.meta_calorias)
    msg_proteina = _mensaje_proteina(estado_prot, diff_prot, usuario.meta_proteina)

    # 3. Consejo holístico ODS 3
    consejo = _consejo_ods3(estado_cal, estado_prot)

    # 4. Ensamblar retroalimentación completa en lenguaje natural
    retroalimentacion = (
        f"📋 Análisis del día {registro_diario.fecha.strftime('%d/%m/%Y')} "
        f"para {usuario.nombre}:\n\n"
        f"🔥 Calorías — {msg_calorias}\n\n"
        f"💪 Proteínas — {msg_proteina}\n\n"
        f"{consejo}"
    )

    return {
        "usuario":           usuario.nombre,
        "fecha":             registro_diario.fecha,
        "total_calorias":    registro_diario.total_calorias,
        "meta_calorias":     usuario.meta_calorias,
        "total_proteinas":   registro_diario.total_proteinas,
        "meta_proteina":     usuario.meta_proteina,
        "estado_calorias":   estado_cal,
        "estado_proteina":   estado_prot,
        "retroalimentacion": retroalimentacion,
    }
