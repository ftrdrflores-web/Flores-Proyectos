import logging
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

logger = logging.getLogger(__name__)

# =====================================================
# TAREAS DE SINCRONIZACIÓN
# =====================================================

def sync_all_clans():
    """
    Tarea principal que sincroniza TODOS los clanes registrados.
    Se ejecuta automáticamente según el intervalo configurado por clan.
    """
    # Importar aquí para evitar problemas de importación circular
    from users.models import Clan
    from core_data.services.sync_members import sync_clan_members
    from core_data.services.sync_wars import sync_clan_wars
    from core_data.services.sync_current_war import sync_current_war

    logger.info("=== Iniciando sincronización automática de todos los clanes ===")

    clans = Clan.objects.all()

    if not clans.exists():
        logger.info("No hay clanes registrados para sincronizar")
        return

    for clan in clans:
        try:
            # Verificar si es momento de sincronizar este clan
            if not _should_sync(clan):
                logger.info(f"Clan {clan.clan_name}: no es momento de sincronizar todavía")
                continue

            logger.info(f"Sincronizando clan: {clan.clan_name}")

            # ===== Paso 1: Sync de miembros =====
            result_members = sync_clan_members(clan.id)
            if result_members['success']:
                logger.info(
                    f"[{clan.clan_name}] Miembros: "
                    f"+{result_members['created']} nuevos, "
                    f"{result_members['updated']} actualizados, "
                    f"{result_members['deactivated']} inactivos"
                )
            else:
                logger.error(f"[{clan.clan_name}] Error en sync miembros: {result_members['error']}")

            # ===== Paso 2: Sync de guerras históricas =====
            result_wars = sync_clan_wars(clan.id, limit=10)
            if result_wars['success']:
                logger.info(
                    f"[{clan.clan_name}] Guerras: "
                    f"+{result_wars['created']} nuevas, "
                    f"{result_wars['skipped']} omitidas"
                )
            else:
                logger.error(f"[{clan.clan_name}] Error en sync guerras: {result_wars['error']}")

            # ===== Paso 3: Sync de guerra actual =====
            result_current = sync_current_war(clan.id)
            if result_current['success']:
                state = result_current.get('war_state', 'unknown')
                logger.info(
                    f"[{clan.clan_name}] Guerra actual: estado={state}, "
                    f"participantes={result_current.get('participants_created', 0)}, "
                    f"ataques={result_current.get('attacks_created', 0)}"
                )
            else:
                logger.error(
                    f"[{clan.clan_name}] Error en sync guerra actual: {result_current['error']}"
                )

            # ===== Actualizar próxima sincronización =====
            _update_next_sync(clan)

        except Exception as e:
            logger.error(f"Error inesperado sincronizando {clan.clan_name}: {str(e)}")

    logger.info("=== Sincronización automática completada ===")


def sync_active_wars():
    """
    Tarea específica para sincronizar SOLO la guerra actual.
    Se ejecuta cada hora para capturar ataques en tiempo real.
    """
    from users.models import Clan
    from core_data.services.sync_current_war import sync_current_war

    logger.info("=== Sincronizando guerras activas ===")

    clans = Clan.objects.all()

    for clan in clans:
        try:
            result = sync_current_war(clan.id)

            if result['success']:
                state = result.get('war_state', 'unknown')

                # Solo loguear si hay actividad relevante
                if state == 'inWar':
                    logger.info(
                        f"[{clan.clan_name}] Guerra activa: "
                        f"+{result.get('attacks_created', 0)} ataques nuevos"
                    )
                elif state == 'notInWar':
                    logger.debug(f"[{clan.clan_name}] Sin guerra activa")

        except Exception as e:
            logger.error(f"Error sincronizando guerra activa de {clan.clan_name}: {str(e)}")


# =====================================================
# FUNCIONES HELPER
# =====================================================

def _should_sync(clan) -> bool:
    """
    Verifica si es momento de sincronizar un clan
    basándose en su intervalo configurado.

    Args:
        clan: Objeto Clan

    Returns:
        True si debe sincronizar, False si no
    """
    if not clan.last_sync:
        return True  # Nunca se ha sincronizado

    hours_since_last_sync = (
        timezone.now() - clan.last_sync
    ).total_seconds() / 3600

    return hours_since_last_sync >= clan.sync_interval


def _update_next_sync(clan):
    """
    Actualiza la próxima sincronización programada del clan.

    Args:
        clan: Objeto Clan
    """
    from datetime import timedelta

    clan.last_sync = timezone.now()
    clan.next_sync_scheduled = timezone.now() + timedelta(hours=clan.sync_interval)
    clan.save(update_fields=['last_sync', 'next_sync_scheduled'])


# =====================================================
# CONFIGURACIÓN DEL SCHEDULER
# =====================================================

def start_scheduler():
    """
    Inicializa y arranca el scheduler con todas las tareas programadas.
    Se llama una sola vez al iniciar Django.
    """
    scheduler = BackgroundScheduler(timezone='UTC')
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    # ===== TAREA 1: Sync completo cada hora =====
    # Verifica internamente si cada clan necesita sincronizarse
    scheduler.add_job(
        sync_all_clans,
        trigger=IntervalTrigger(hours=1),
        id='sync_all_clans',
        name='Sincronización completa de todos los clanes',
        replace_existing=True,
        max_instances=1,
    )

    # ===== TAREA 2: Sync de guerra activa cada 30 minutos =====
    # Captura ataques en tiempo real durante guerras
    scheduler.add_job(
        sync_active_wars,
        trigger=IntervalTrigger(minutes=30),
        id='sync_active_wars',
        name='Sincronización de guerras activas',
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("✅ Scheduler iniciado correctamente")
    logger.info("   - Sync completo: cada 1 hora")
    logger.info("   - Sync guerras activas: cada 30 minutos")

    return scheduler