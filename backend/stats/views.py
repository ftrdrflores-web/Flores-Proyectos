from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Avg, Sum, Count, Max, Min, Q, F
from django.utils import timezone
from datetime import timedelta

from stats.models import PlayerStats, ClanStats, WarLog, PlayerMonthlyStats
from wars.models import War, Attack, WarParticipant
from players.models import Player
from users.permissions import IsClanAdmin
from .serializers import (
    ClanStatsSerializer,
    PlayerStatsSerializer,
    WarLogSerializer,
    PlayerMonthlyStatsSerializer,
)


# =====================================================
# VIEW: Dashboard de estadísticas del clan
# =====================================================

class StatsDashboardView(APIView):
    """
    GET /api/stats/dashboard/

    KPIs principales para el dashboard del clan.
    Combina datos de guerras, jugadores y stats calculadas.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clan = request.user.profile.clan

        # ===== KPIs de Guerra =====
        wars = War.objects.filter(clan=clan, state='warEnded')
        total_wars = wars.count()
        wins = wars.filter(result='win').count()
        losses = wars.filter(result='loss').count()
        ties = wars.filter(result='tie').count()
        win_rate = round((wins / total_wars) * 100, 1) if total_wars > 0 else 0

        # Promedio de estrellas y destrucción
        war_avgs = wars.aggregate(
            avg_stars=Avg('clan_stars'),
            avg_destruction=Avg('clan_destruction_percentage'),
            total_stars=Sum('clan_stars'),
        )

        # ===== KPIs de Ataques =====
        attacks = Attack.objects.filter(war__clan=clan)
        total_attacks = attacks.count()
        perfect_attacks = attacks.filter(stars=3, destruction_percentage=100).count()
        attack_avgs = attacks.aggregate(
            avg_stars=Avg('stars'),
            avg_destruction=Avg('destruction_percentage'),
        )

        # ===== KPIs de Jugadores =====
        active_players = Player.objects.filter(clan=clan, status='active').count()
        total_players = Player.objects.filter(clan=clan).count()

        # Top donador
        top_donator = Player.objects.filter(
            clan=clan, status='active'
        ).order_by('-donations').first()

        # ===== Últimos 30 días =====
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_wars = wars.filter(end_time__gte=thirty_days_ago)
        recent_wins = recent_wars.filter(result='win').count()
        recent_total = recent_wars.count()
        recent_win_rate = round((recent_wins / recent_total) * 100, 1) if recent_total > 0 else 0

        return Response({
            'clan': {
                'tag': clan.clan_tag,
                'name': clan.clan_name,
                'level': clan.clan_level,
                'members': active_players,
                'total_members': total_players,
            },
            'war_kpis': {
                'total_wars': total_wars,
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'win_rate': win_rate,
                'win_streak': clan.war_win_streak,
                'avg_stars_per_war': round(war_avgs['avg_stars'] or 0, 1),
                'avg_destruction_per_war': round(war_avgs['avg_destruction'] or 0, 1),
                'total_stars_earned': war_avgs['total_stars'] or 0,
            },
            'attack_kpis': {
                'total_attacks': total_attacks,
                'perfect_attacks': perfect_attacks,
                'perfect_rate': round((perfect_attacks / total_attacks) * 100, 1) if total_attacks > 0 else 0,
                'avg_stars_per_attack': round(attack_avgs['avg_stars'] or 0, 2),
                'avg_destruction_per_attack': round(attack_avgs['avg_destruction'] or 0, 1),
            },
            'last_30_days': {
                'total_wars': recent_total,
                'wins': recent_wins,
                'win_rate': recent_win_rate,
            },
            'top_donator': {
                'name': top_donator.name if top_donator else None,
                'player_tag': top_donator.player_tag if top_donator else None,
                'donations': top_donator.donations if top_donator else 0,
            } if top_donator else None,
        })


# =====================================================
# VIEW: Ranking global de jugadores por stats
# =====================================================

class StatsLeaderboardView(APIView):
    """
    GET /api/stats/leaderboard/
    GET /api/stats/leaderboard/?by=stars&limit=10

    Leaderboard completo de jugadores con todas sus métricas.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clan = request.user.profile.clan
        limit = int(request.query_params.get('limit', 10))

        players_with_stats = PlayerStats.objects.filter(
            clan=clan,
            total_attacks__gt=0
        ).select_related('player').order_by('-avg_stars_per_attack')[:limit]

        leaderboard = []
        for rank, s in enumerate(players_with_stats, start=1):
            leaderboard.append({
                'rank': rank,
                'player_tag': s.player.player_tag,
                'name': s.player.name,
                'town_hall_level': s.player.town_hall_level,
                'role': s.player.role,
                'avg_stars': round(s.avg_stars_per_attack, 2),
                'avg_destruction': round(s.avg_destruction_per_attack, 1),
                'total_attacks': s.total_attacks,
                'perfect_attacks': s.perfect_attacks,
                'war_participation_rate': round(s.war_participation_rate, 1),
                'overall_rating': s.get_overall_rating(),
            })

        return Response({
            'clan_tag': clan.clan_tag,
            'total_with_stats': len(leaderboard),
            'leaderboard': leaderboard,
        })


# =====================================================
# VIEW: Tendencias del clan (últimas N guerras)
# =====================================================

class StatsTrendsView(APIView):
    """
    GET /api/stats/trends/
    GET /api/stats/trends/?last=10

    Tendencias de rendimiento en las últimas N guerras.
    Útil para gráficas de línea en el frontend.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clan = request.user.profile.clan
        last_n = int(request.query_params.get('last', 10))

        wars = War.objects.filter(
            clan=clan,
            state='warEnded',
            result__isnull=False
        ).order_by('-end_time')[:last_n]

        # Invertir para orden cronológico (más antiguo → más reciente)
        wars = list(reversed(list(wars)))

        trends = []
        accumulated_wins = 0
        accumulated_total = 0

        for war in wars:
            accumulated_total += 1
            if war.result == 'win':
                accumulated_wins += 1

            # Ataques de esta guerra
            war_attacks = Attack.objects.filter(war=war)
            avg_stars = war_attacks.aggregate(avg=Avg('stars'))['avg'] or 0
            avg_dest = war_attacks.aggregate(avg=Avg('destruction_percentage'))['avg'] or 0
            perfect = war_attacks.filter(stars=3, destruction_percentage=100).count()
            total_att = war_attacks.count()

            trends.append({
                'war_id': war.id,
                'opponent': war.opponent_name,
                'date': war.end_time,
                'result': war.result,
                'clan_stars': war.clan_stars,
                'opponent_stars': war.opponent_stars,
                'stars_difference': war.clan_stars - war.opponent_stars,
                'clan_destruction': round(war.clan_destruction_percentage, 1),
                'team_size': war.team_size,
                'attacks_used': war.clan_attacks,
                'attacks_available': war.team_size * war.attacks_per_member,
                'attack_efficiency': round(
                    (war.clan_attacks / (war.team_size * war.attacks_per_member)) * 100, 1
                ) if war.team_size > 0 else 0,
                'avg_stars_per_attack': round(avg_stars, 2),
                'avg_destruction_per_attack': round(avg_dest, 1),
                'perfect_attacks': perfect,
                'accumulated_win_rate': round(
                    (accumulated_wins / accumulated_total) * 100, 1
                ),
                'is_league_war': war.is_league_war,
            })

        # Calcular tendencia general (¿estamos mejorando?)
        if len(trends) >= 4:
            first_half = trends[:len(trends)//2]
            second_half = trends[len(trends)//2:]
            first_avg = sum(t['avg_stars_per_attack'] for t in first_half) / len(first_half)
            second_avg = sum(t['avg_stars_per_attack'] for t in second_half) / len(second_half)
            trend_direction = 'mejorando' if second_avg > first_avg else 'bajando' if second_avg < first_avg else 'estable'
        else:
            trend_direction = 'insuficientes datos'

        return Response({
            'clan_tag': clan.clan_tag,
            'wars_analyzed': len(trends),
            'trend_direction': trend_direction,
            'trends': trends,
        })


# =====================================================
# VIEW: Comparativa de jugadores (stats avanzadas)
# =====================================================

class StatsPlayerCompareView(APIView):
    """
    GET /api/stats/compare/?tags=#TAG1,#TAG2

    Comparativa detallada entre jugadores usando PlayerStats.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clan = request.user.profile.clan
        tags_param = request.query_params.get('tags', '')

        if not tags_param:
            return Response(
                {'error': 'Proporciona los tags separados por coma. Ej: ?tags=#TAG1,#TAG2'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tags = [t.strip().upper() for t in tags_param.split(',')]
        tags = [t if t.startswith('#') else f'#{t}' for t in tags]

        if len(tags) > 5:
            return Response(
                {'error': 'Máximo 5 jugadores para comparar.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stats = PlayerStats.objects.filter(
            clan=clan,
            player__player_tag__in=tags
        ).select_related('player')

        comparison = []
        for s in stats:
            comparison.append({
                'player_tag': s.player.player_tag,
                'name': s.player.name,
                'town_hall_level': s.player.town_hall_level,
                'role': s.player.role,
                'attack': {
                    'total_attacks': s.total_attacks,
                    'avg_stars': round(s.avg_stars_per_attack, 2),
                    'avg_destruction': round(s.avg_destruction_per_attack, 1),
                    'perfect_attacks': s.perfect_attacks,
                    'perfect_rate': round(
                        (s.perfect_attacks / s.total_attacks * 100), 1
                    ) if s.total_attacks > 0 else 0,
                },
                'defense': {
                    'total_defenses': s.total_defenses,
                    'avg_stars_lost': round(s.avg_stars_lost, 2),
                    'defensive_efficiency': round(s.defensive_efficiency, 1),
                    'successful_defenses': s.successful_defenses,
                },
                'participation': {
                    'total_wars': s.total_wars,
                    'wars_participated': s.wars_participated,
                    'participation_rate': round(s.war_participation_rate, 1),
                },
                'donations': {
                    'total': s.total_donations,
                    'received': s.total_donations_received,
                    'balance': s.donation_balance,
                },
                'overall_rating': s.get_overall_rating(),
                'current_rank': s.current_rank,
            })

        return Response({
            'compared': len(comparison),
            'comparison': comparison,
        })


# =====================================================
# VIEW: War Log (histórico mensual de guerras)
# =====================================================

class StatsWarLogView(APIView):
    """
    GET /api/stats/war-log/

    Histórico de guerras agrupado por período.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clan = request.user.profile.clan

        war_logs = WarLog.objects.filter(
            clan=clan
        ).order_by('-war_date')

        serializer = WarLogSerializer(war_logs, many=True)

        return Response({
            'clan_tag': clan.clan_tag,
            'total_periods': war_logs.count(),
            'war_log': serializer.data,
        })


# =====================================================
# VIEW: Stats de un jugador específico
# =====================================================

class StatsPlayerView(APIView):
    """
    GET /api/stats/player/{player_tag}/

    Estadísticas completas de un jugador específico.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_tag):
        clan = request.user.profile.clan

        tag = player_tag.upper()
        if not tag.startswith('#'):
            tag = f'#{tag}'

        try:
            player = Player.objects.get(clan=clan, player_tag=tag)
        except Player.DoesNotExist:
            return Response(
                {'error': f'Jugador {tag} no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Stats calculadas
        try:
            player_stats = PlayerStats.objects.get(player=player)
            stats_data = PlayerStatsSerializer(player_stats).data
        except PlayerStats.DoesNotExist:
            stats_data = None

        # Stats en tiempo real desde ataques
        attacks = Attack.objects.filter(
            war__clan=clan,
            attacker_tag=tag
        )
        total_attacks = attacks.count()
        attack_live = None
        if total_attacks > 0:
            attack_live = {
                'total_attacks': total_attacks,
                'total_stars': attacks.aggregate(s=Sum('stars'))['s'] or 0,
                'avg_stars': round(attacks.aggregate(a=Avg('stars'))['a'] or 0, 2),
                'avg_destruction': round(attacks.aggregate(a=Avg('destruction_percentage'))['a'] or 0, 1),
                'perfect_attacks': attacks.filter(stars=3, destruction_percentage=100).count(),
                'three_star_attacks': attacks.filter(stars=3).count(),
            }

        # Historial mensual
        monthly = PlayerMonthlyStats.objects.filter(
            player=player
        ).order_by('-year', '-month')[:6]
        monthly_data = PlayerMonthlyStatsSerializer(monthly, many=True).data

        return Response({
            'player': {
                'tag': player.player_tag,
                'name': player.name,
                'town_hall_level': player.town_hall_level,
                'role': player.role,
                'clan_rank': player.clan_rank,
                'trophies': player.trophies,
                'donations': player.donations,
                'donations_received': player.donations_received,
                'status': player.status,
            },
            'calculated_stats': stats_data,
            'live_attack_stats': attack_live,
            'monthly_stats': monthly_data,
        })