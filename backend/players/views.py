from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Sum, Count, Q, F
from django.shortcuts import get_object_or_404

from players.models import Player
from stats.models import PlayerStats, PlayerMonthlyStats
from users.permissions import IsClanAdmin, ClanFilterMixin
from .serializers import PlayerListSerializer, PlayerDetailSerializer


# =====================================================
# VIEW: Lista de jugadores + Ranking
# =====================================================

class PlayerListView(generics.ListAPIView):
    """
    GET /api/players/
    GET /api/players/?status=active
    GET /api/players/?role=leader
    GET /api/players/?order_by=trophies
    GET /api/players/?th=15
    
    Lista todos los jugadores del clan con filtros opcionales.
    Accesible por todos los miembros.
    """
    serializer_class = PlayerListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        clan = self.request.user.profile.clan
        queryset = Player.objects.filter(clan=clan).select_related('stats')

        # ===== Filtros opcionales =====
        status_filter = self.request.query_params.get('status', 'active')
        role_filter   = self.request.query_params.get('role', None)
        th_filter     = self.request.query_params.get('th', None)
        order_by      = self.request.query_params.get('order_by', 'clan_rank')

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if role_filter:
            queryset = queryset.filter(role=role_filter)

        if th_filter:
            queryset = queryset.filter(town_hall_level=int(th_filter))

        # ===== Ordenamiento =====
        order_options = {
            'clan_rank':    'clan_rank',
            'trophies':     '-trophies',
            'donations':    '-donations',
            'th':           '-town_hall_level',
            'name':         'name',
            'stars':        '-stats__avg_stars_per_attack',
            'attacks':      '-stats__total_attacks',
        }
        order_field = order_options.get(order_by, 'clan_rank')
        queryset = queryset.order_by(order_field)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        clan = request.user.profile.clan
        return Response({
            'clan_tag': clan.clan_tag,
            'clan_name': clan.clan_name,
            'total': queryset.count(),
            'players': serializer.data,
        })


# =====================================================
# VIEW: Detalle de un jugador
# =====================================================

class PlayerDetailView(generics.RetrieveAPIView):
    """
    GET /api/players/{id}/
    GET /api/players/tag/{player_tag}/   ← por tag de Clash
    
    Detalle completo de un jugador incluyendo sus stats.
    """
    serializer_class = PlayerDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        clan = self.request.user.profile.clan
        return Player.objects.filter(clan=clan).select_related('stats')


class PlayerDetailByTagView(APIView):
    """
    GET /api/players/tag/{player_tag}/
    
    Busca un jugador por su tag de Clash (ej: %2328L8RL8QG → #28L8RL8QG)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_tag):
        clan = request.user.profile.clan

        # Normalizar tag (puede venir con o sin #)
        tag = player_tag.upper()
        if not tag.startswith('#'):
            tag = f'#{tag}'

        try:
            player = Player.objects.select_related('stats').get(
                clan=clan,
                player_tag=tag
            )
        except Player.DoesNotExist:
            return Response(
                {'error': f'Jugador con tag {tag} no encontrado en tu clan.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PlayerDetailSerializer(player)
        return Response(serializer.data)


# =====================================================
# VIEW: Ranking del clan
# =====================================================

class PlayerRankingView(APIView):
    """
    GET /api/players/ranking/
    GET /api/players/ranking/?by=stars     (por estrellas)
    GET /api/players/ranking/?by=attacks   (por ataques)
    GET /api/players/ranking/?by=donations (por donaciones)
    GET /api/players/ranking/?by=trophies  (por trofeos)
    GET /api/players/ranking/?by=defense   (por defensas)
    
    Ranking de jugadores según criterio.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clan = request.user.profile.clan
        rank_by = request.query_params.get('by', 'stars')
        limit = int(request.query_params.get('limit', 10))

        players = Player.objects.filter(
            clan=clan,
            status='active'
        ).select_related('stats')

        if rank_by == 'stars':
            players = players.filter(
                stats__total_attacks__gt=0
            ).order_by('-stats__avg_stars_per_attack', '-stats__total_attacks')
            metric_label = 'Promedio de Estrellas'

        elif rank_by == 'attacks':
            players = players.filter(
                stats__total_attacks__gt=0
            ).order_by('-stats__total_attacks', '-stats__avg_stars_per_attack')
            metric_label = 'Total de Ataques'

        elif rank_by == 'donations':
            players = players.order_by('-donations')
            metric_label = 'Donaciones'

        elif rank_by == 'trophies':
            players = players.order_by('-trophies')
            metric_label = 'Trofeos'

        elif rank_by == 'defense':
            players = players.filter(
                stats__total_defenses__gt=0
            ).order_by('-stats__defensive_efficiency')
            metric_label = 'Eficiencia Defensiva'

        elif rank_by == 'participation':
            players = players.filter(
                stats__total_wars__gt=0
            ).order_by('-stats__war_participation_rate')
            metric_label = 'Participación en Guerras'

        else:
            players = players.order_by('clan_rank')
            metric_label = 'Ranking del Clan'

        players = players[:limit]

        # Construir ranking
        ranking = []
        for position, player in enumerate(players, start=1):
            entry = {
                'position': position,
                'player_tag': player.player_tag,
                'name': player.name,
                'town_hall_level': player.town_hall_level,
                'role': player.role,
                'clan_rank': player.clan_rank,
            }

            # Agregar métrica según criterio
            try:
                s = player.stats
                if rank_by == 'stars':
                    entry['metric'] = round(s.avg_stars_per_attack, 2)
                    entry['total_attacks'] = s.total_attacks
                    entry['perfect_attacks'] = s.perfect_attacks
                elif rank_by == 'attacks':
                    entry['metric'] = s.total_attacks
                    entry['avg_stars'] = round(s.avg_stars_per_attack, 2)
                elif rank_by == 'defense':
                    entry['metric'] = round(s.defensive_efficiency, 1)
                    entry['total_defenses'] = s.total_defenses
                elif rank_by == 'participation':
                    entry['metric'] = round(s.war_participation_rate, 1)
                    entry['wars_participated'] = s.wars_participated
            except Exception:
                pass

            if rank_by == 'donations':
                entry['metric'] = player.donations
                entry['received'] = player.donations_received
                entry['balance'] = player.donations - player.donations_received

            if rank_by == 'trophies':
                entry['metric'] = player.trophies
                entry['league'] = player.get_league_name()

            ranking.append(entry)

        return Response({
            'clan_tag': clan.clan_tag,
            'ranking_by': rank_by,
            'metric_label': metric_label,
            'total': len(ranking),
            'ranking': ranking,
        })


# =====================================================
# VIEW: Stats individuales de un jugador
# =====================================================

class PlayerStatsView(APIView):
    """
    GET /api/players/{id}/stats/
    
    Estadísticas completas y detalladas de un jugador.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        clan = request.user.profile.clan

        try:
            player = Player.objects.select_related('stats').get(
                pk=pk,
                clan=clan
            )
        except Player.DoesNotExist:
            return Response(
                {'error': 'Jugador no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Info básica
        data = {
            'player_tag': player.player_tag,
            'name': player.name,
            'town_hall_level': player.town_hall_level,
            'role': player.role,
            'clan_rank': player.clan_rank,
            'status': player.status,
        }

        # Stats de guerra
        try:
            s = player.stats
            data['war_stats'] = {
                'total_wars': s.total_wars,
                'wars_participated': s.wars_participated,
                'war_participation_rate': round(s.war_participation_rate, 1),
                'total_attacks': s.total_attacks,
                'avg_stars_per_attack': round(s.avg_stars_per_attack, 2),
                'avg_destruction_per_attack': round(s.avg_destruction_per_attack, 1),
                'perfect_attacks': s.perfect_attacks,
                'perfect_attack_rate': round(
                    (s.perfect_attacks / s.total_attacks * 100), 1
                ) if s.total_attacks > 0 else 0,
            }
            data['defense_stats'] = {
                'total_defenses': s.total_defenses,
                'avg_stars_lost': round(s.avg_stars_lost, 2),
                'avg_destruction_suffered': round(s.avg_destruction_suffered, 1),
                'defensive_efficiency': round(s.defensive_efficiency, 1),
                'successful_defenses': s.successful_defenses,
            }
            data['donation_stats'] = {
                'total_donations': s.total_donations,
                'total_received': s.total_donations_received,
                'donation_balance': s.donation_balance,
            }
            data['overall_rating'] = s.get_overall_rating()
            data['current_rank'] = s.current_rank
            data['calculated_at'] = s.calculated_at

        except PlayerStats.DoesNotExist:
            data['war_stats'] = None
            data['defense_stats'] = None
            data['overall_rating'] = 'Sin datos'

        # Donaciones actuales (en tiempo real desde Player)
        data['current_donations'] = {
            'donations': player.donations,
            'donations_received': player.donations_received,
            'balance': player.donations - player.donations_received,
        }

        return Response(data)


# =====================================================
# VIEW: Historial mensual de un jugador
# =====================================================

class PlayerMonthlyStatsView(APIView):
    """
    GET /api/players/{id}/monthly/
    GET /api/players/{id}/monthly/?year=2026
    
    Historial mensual de estadísticas de un jugador.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        clan = request.user.profile.clan

        try:
            player = Player.objects.get(pk=pk, clan=clan)
        except Player.DoesNotExist:
            return Response(
                {'error': 'Jugador no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        year_filter = request.query_params.get('year', None)

        monthly = PlayerMonthlyStats.objects.filter(
            player=player,
            clan=clan
        )

        if year_filter:
            monthly = monthly.filter(year=int(year_filter))

        monthly = monthly.order_by('-year', '-month')

        data = [{
            'year': m.year,
            'month': m.month,
            'total_attacks': m.total_attacks,
            'total_stars': m.total_stars,
            'avg_destruction': round(m.avg_destruction, 1),
            'perfect_attacks': m.perfect_attacks,
            'total_donations': m.total_donations,
            'total_donations_received': m.total_donations_received,
            'trophy_change': m.trophy_change,
            'town_hall_change': m.town_hall_change,
        } for m in monthly]

        return Response({
            'player_tag': player.player_tag,
            'name': player.name,
            'total_months': len(data),
            'monthly_stats': data,
        })


# =====================================================
# VIEW: Comparación entre jugadores
# =====================================================

class PlayerCompareView(APIView):
    """
    GET /api/players/compare/?tags=#TAG1,#TAG2,#TAG3
    
    Compara estadísticas de hasta 5 jugadores.
    Útil para decidir quién ataca en guerra.
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

        players = Player.objects.filter(
            clan=clan,
            player_tag__in=tags
        ).select_related('stats')

        comparison = []
        for player in players:
            entry = {
                'player_tag': player.player_tag,
                'name': player.name,
                'town_hall_level': player.town_hall_level,
                'role': player.role,
                'trophies': player.trophies,
                'donations': player.donations,
            }
            try:
                s = player.stats
                entry['stats'] = {
                    'total_attacks': s.total_attacks,
                    'avg_stars': round(s.avg_stars_per_attack, 2),
                    'avg_destruction': round(s.avg_destruction_per_attack, 1),
                    'perfect_attacks': s.perfect_attacks,
                    'war_participation_rate': round(s.war_participation_rate, 1),
                    'defensive_efficiency': round(s.defensive_efficiency, 1),
                    'overall_rating': s.get_overall_rating(),
                }
            except Exception:
                entry['stats'] = None

            comparison.append(entry)

        return Response({
            'compared_players': len(comparison),
            'comparison': comparison,
        })