from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Clan, UserProfile
from .permissions import IsClanAdmin, IsAdminOrReadOnly
from .serializers_clan import ClanSerializer, ClanPublicSerializer, ClanUpdateSerializer


# =====================================================
# VIEW: Detalle del clan del usuario autenticado
# =====================================================

class MyClanView(APIView):
    """
    GET   /api/clan/         → Ver datos del clan
    PATCH /api/clan/         → Actualizar configuración (solo admin)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            clan = request.user.profile.clan
            role = request.user.profile.role

            # Admins ven más información
            if role == 'admin':
                serializer = ClanSerializer(clan)
            else:
                serializer = ClanPublicSerializer(clan)

            return Response(serializer.data)

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'No tienes un perfil asociado a ningún clan.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        # Solo admins pueden actualizar
        try:
            profile = request.user.profile
            if profile.role != 'admin':
                return Response(
                    {'error': 'Solo los administradores pueden modificar la configuración del clan.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            clan = profile.clan
            serializer = ClanUpdateSerializer(clan, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                'message': 'Configuración del clan actualizada.',
                'clan': ClanSerializer(clan).data,
            })

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'No tienes un perfil asociado a ningún clan.'},
                status=status.HTTP_404_NOT_FOUND
            )


# =====================================================
# VIEW: Estadísticas generales del clan
# =====================================================

class ClanStatsView(APIView):
    """
    GET /api/clan/stats/
    
    Retorna KPIs y estadísticas generales del clan.
    Accesible por todos los miembros.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            clan = request.user.profile.clan

            # Intentar obtener stats precalculadas
            try:
                clan_stats = clan.clan_stats
                stats_data = {
                    'total_wars': clan_stats.total_wars,
                    'total_wins': clan_stats.total_wins,
                    'total_losses': clan_stats.total_losses,
                    'total_ties': clan_stats.total_ties,
                    'win_rate': clan_stats.win_rate,
                    'avg_stars_per_war': clan_stats.avg_stars_per_war,
                    'avg_destruction_per_war': clan_stats.avg_destruction_per_war,
                    'active_players_this_war': clan_stats.active_players_this_war,
                    'avg_participation_rate': clan_stats.avg_participation_rate,
                    'best_attacker': {
                        'tag': clan_stats.best_attacker_tag,
                        'name': clan_stats.best_attacker_name,
                        'stars': clan_stats.best_attacker_stars,
                    } if clan_stats.best_attacker_tag else None,
                    'calculated_at': clan_stats.calculated_at,
                }
            except Exception:
                # Si no hay stats calculadas, retornar datos básicos del clan
                total = clan.war_wins + clan.war_losses + clan.war_ties
                stats_data = {
                    'total_wars': total,
                    'total_wins': clan.war_wins,
                    'total_losses': clan.war_losses,
                    'total_ties': clan.war_ties,
                    'win_rate': round((clan.war_wins / total) * 100, 1) if total > 0 else 0,
                    'war_win_streak': clan.war_win_streak,
                    'calculated_at': clan.updated_at,
                }

            return Response({
                'clan_tag': clan.clan_tag,
                'clan_name': clan.clan_name,
                'stats': stats_data,
            })

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'No tienes perfil asociado a ningún clan.'},
                status=status.HTTP_404_NOT_FOUND
            )


# =====================================================
# VIEW: Lista de miembros del clan
# =====================================================

class ClanMembersView(APIView):
    """
    GET /api/clan/members/
    
    Lista todos los jugadores activos del clan.
    Accesible por todos los miembros.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from players.models import Player
        from players.serializers import PlayerListSerializer

        try:
            clan = request.user.profile.clan

            # Filtros opcionales por query params
            status_filter = request.query_params.get('status', 'active')
            role_filter = request.query_params.get('role', None)

            players = Player.objects.filter(clan=clan)

            if status_filter:
                players = players.filter(status=status_filter)

            if role_filter:
                players = players.filter(role=role_filter)

            players = players.order_by('clan_rank')

            serializer = PlayerListSerializer(players, many=True)
            return Response({
                'clan_tag': clan.clan_tag,
                'clan_name': clan.clan_name,
                'total_members': players.count(),
                'members': serializer.data,
            })

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'No tienes perfil asociado a ningún clan.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =====================================================
# VIEW: Resumen del dashboard del clan
# =====================================================

class ClanDashboardView(APIView):
    """
    GET /api/clan/dashboard/
    
    Datos consolidados para el dashboard principal.
    Combina info del clan + stats + guerra actual.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from wars.models import War

        try:
            clan = request.user.profile.clan

            # Info básica del clan
            total_wars = clan.war_wins + clan.war_losses + clan.war_ties
            win_rate = round((clan.war_wins / total_wars) * 100, 1) if total_wars > 0 else 0

            # Guerra actual
            current_war = None
            try:
                war = War.objects.filter(
                    clan=clan,
                    state__in=['preparation', 'inWar']
                ).order_by('-start_time').first()

                if war:
                    # Estado legible en español
                    state_labels = {
                        'preparation': 'En Preparación',
                        'inWar': 'Guerra en Progreso',
                        'warEnded': 'Guerra Terminada',
                    }
                    current_war = {
                        'id': war.id,
                        'state': war.state,
                        'state_label': state_labels.get(war.state, war.state),
                        'is_active': war.state == 'inWar',
                        'is_preparation': war.state == 'preparation',
                        'opponent_name': war.opponent_name,
                        'opponent_tag': war.opponent_tag,
                        'opponent_clan_level': war.opponent_clan_level,
                        'team_size': war.team_size,
                        'attacks_per_member': war.attacks_per_member,
                        'clan_stars': war.clan_stars,
                        'opponent_stars': war.opponent_stars,
                        'clan_destruction': war.clan_destruction_percentage,
                        'opponent_destruction': war.opponent_destruction_percentage,
                        'start_time': war.start_time,
                        'end_time': war.end_time,
                        'attacks_used': war.clan_attacks,
                        'attacks_available': war.team_size * war.attacks_per_member,
                        'attacks_remaining': (war.team_size * war.attacks_per_member) - war.clan_attacks,
                        'is_league_war': war.is_league_war,
                    }
            except Exception:
                pass

            # Últimas 5 guerras
            recent_wars = []
            try:
                wars = War.objects.filter(
                    clan=clan,
                    state='warEnded'
                ).order_by('-end_time')[:5]

                recent_wars = [{
                    'id': w.id,
                    'opponent_name': w.opponent_name,
                    'result': w.result,
                    'clan_stars': w.clan_stars,
                    'opponent_stars': w.opponent_stars,
                    'end_time': w.end_time,
                } for w in wars]
            except Exception:
                pass

            return Response({
                'clan': {
                    'tag': clan.clan_tag,
                    'name': clan.clan_name,
                    'level': clan.clan_level,
                    'badge_url': clan.badge_url,
                    'members_count': clan.members_count,
                    'last_sync': clan.last_sync,
                },
                'war_summary': {
                    'total_wars': total_wars,
                    'wins': clan.war_wins,
                    'losses': clan.war_losses,
                    'ties': clan.war_ties,
                    'win_rate': win_rate,
                    'win_streak': clan.war_win_streak,
                },
                'current_war': current_war,
                'recent_wars': recent_wars,
            })

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'No tienes perfil asociado a ningún clan.'},
                status=status.HTTP_404_NOT_FOUND
            )