from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Sum, Count, Q

from wars.models import War, WarParticipant, Attack, Defense
from users.permissions import IsClanAdmin
from .serializers import (
    WarListSerializer,
    WarDetailSerializer,
    CurrentWarSerializer,
    AttackSerializer,
    DefenseSerializer,
)


# =====================================================
# VIEW: Historial de guerras
# =====================================================

class WarListView(generics.ListAPIView):
    """
    GET /api/wars/
    GET /api/wars/?result=win
    GET /api/wars/?result=loss
    GET /api/wars/?is_league=true
    GET /api/wars/?limit=10
    
    Historial de guerras terminadas del clan.
    """
    serializer_class = WarListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        clan = self.request.user.profile.clan
        queryset = War.objects.filter(
            clan=clan,
            state='warEnded'
        ).order_by('-end_time')

        # Filtros opcionales
        result = self.request.query_params.get('result', None)
        is_league = self.request.query_params.get('is_league', None)

        if result in ['win', 'loss', 'tie']:
            queryset = queryset.filter(result=result)

        if is_league is not None:
            queryset = queryset.filter(is_league_war=is_league.lower() == 'true')

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        clan = request.user.profile.clan

        # Resumen general
        total = queryset.count()
        wins = queryset.filter(result='win').count()
        losses = queryset.filter(result='loss').count()
        ties = queryset.filter(result='tie').count()
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'clan_tag': clan.clan_tag,
            'summary': {
                'total': total,
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'win_rate': win_rate,
            },
            'wars': serializer.data,
        })


# =====================================================
# VIEW: Detalle de una guerra
# =====================================================

class WarDetailView(generics.RetrieveAPIView):
    """
    GET /api/wars/{id}/
    
    Detalle completo de una guerra con participantes y ataques.
    """
    serializer_class = WarDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        clan = self.request.user.profile.clan
        return War.objects.filter(clan=clan).prefetch_related(
            'participants',
            'participants__attacks',
            'participants__player',
        )


# =====================================================
# VIEW: Guerra actual
# =====================================================

class CurrentWarView(APIView):
    """
    GET /api/wars/current/
    
    Retorna la guerra actual (en preparación o en progreso).
    Incluye lista de jugadores que no han atacado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clan = request.user.profile.clan

        war = War.objects.filter(
            clan=clan,
            state__in=['preparation', 'inWar']
        ).prefetch_related(
            'participants',
            'participants__attacks',
            'participants__player',
        ).order_by('-start_time').first()

        if not war:
            return Response(
                {'message': 'No hay guerra activa en este momento.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CurrentWarSerializer(war)
        return Response(serializer.data)


# =====================================================
# VIEW: Ataques de una guerra
# =====================================================

class WarAttacksView(APIView):
    """
    GET /api/wars/{id}/attacks/
    GET /api/wars/{id}/attacks/?stars=3
    GET /api/wars/{id}/attacks/?player_tag=28L8RL8QG
    
    Lista de ataques de una guerra específica.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        clan = request.user.profile.clan

        try:
            war = War.objects.get(pk=pk, clan=clan)
        except War.DoesNotExist:
            return Response(
                {'error': 'Guerra no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        attacks = Attack.objects.filter(war=war).order_by('order')

        # Filtros opcionales
        stars = request.query_params.get('stars', None)
        player_tag = request.query_params.get('player_tag', None)

        if stars is not None:
            attacks = attacks.filter(stars=int(stars))

        if player_tag:
            tag = player_tag.upper()
            if not tag.startswith('#'):
                tag = f'#{tag}'
            attacks = attacks.filter(attacker_tag=tag)

        # Resumen
        total = attacks.count()
        perfect = attacks.filter(stars=3, destruction_percentage=100).count()
        three_stars = attacks.filter(stars=3).count()
        avg_stars = attacks.aggregate(avg=Avg('stars'))['avg'] or 0
        avg_destruction = attacks.aggregate(avg=Avg('destruction_percentage'))['avg'] or 0

        serializer = AttackSerializer(attacks, many=True)

        return Response({
            'war_id': war.id,
            'opponent': war.opponent_name,
            'summary': {
                'total_attacks': total,
                'perfect_attacks': perfect,
                'three_star_attacks': three_stars,
                'avg_stars': round(avg_stars, 2),
                'avg_destruction': round(avg_destruction, 1),
            },
            'attacks': serializer.data,
        })


# =====================================================
# VIEW: Defensas de una guerra
# =====================================================

class WarDefensesView(APIView):
    """
    GET /api/wars/{id}/defenses/
    
    Lista de defensas sufridas en una guerra.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        clan = request.user.profile.clan

        try:
            war = War.objects.get(pk=pk, clan=clan)
        except War.DoesNotExist:
            return Response(
                {'error': 'Guerra no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        defenses = Defense.objects.filter(
            war=war
        ).select_related('player').order_by('-stars_received')

        serializer = DefenseSerializer(defenses, many=True)

        return Response({
            'war_id': war.id,
            'opponent': war.opponent_name,
            'total_defenders': defenses.count(),
            'defenses': serializer.data,
        })


# =====================================================
# VIEW: Resumen de rendimiento por guerra
# =====================================================

class WarPerformanceView(APIView):
    """
    GET /api/wars/{id}/performance/
    
    Resumen de rendimiento individual de cada jugador en una guerra.
    Top atacantes, top defensores, quién no atacó.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        clan = request.user.profile.clan

        try:
            war = War.objects.get(pk=pk, clan=clan)
        except War.DoesNotExist:
            return Response(
                {'error': 'Guerra no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        participants = WarParticipant.objects.filter(
            war=war
        ).select_related('player').prefetch_related('attacks').order_by('map_position')

        # Clasificar jugadores
        top_attackers = []
        no_attacks = []
        incomplete_attacks = []

        for p in participants:
            attacks = p.attacks.all()
            player_data = {
                'player_tag': p.player.player_tag,
                'name': p.player.name,
                'map_position': p.map_position,
                'town_hall_level': p.town_hall_level,
                'attacks_used': p.attacks_used,
                'total_stars': p.total_stars,
                'total_destruction': round(p.total_destruction_percentage, 1),
            }

            if p.attacks_used == 0:
                no_attacks.append(player_data)
            elif p.attacks_used < war.attacks_per_member:
                incomplete_attacks.append(player_data)

            if p.attacks_used > 0:
                player_data['avg_stars'] = round(
                    p.total_stars / p.attacks_used, 2
                )
                top_attackers.append(player_data)

        # Ordenar top atacantes por estrellas
        top_attackers.sort(key=lambda x: (x['total_stars'], x['total_destruction']), reverse=True)

        return Response({
            'war_id': war.id,
            'opponent': war.opponent_name,
            'result': war.result,
            'state': war.state,
            'summary': {
                'total_participants': participants.count(),
                'did_not_attack': len(no_attacks),
                'incomplete_attacks': len(incomplete_attacks),
                'full_participation': len(no_attacks) == 0,
            },
            'top_attackers': top_attackers[:10],
            'did_not_attack': no_attacks,
            'incomplete_attacks': incomplete_attacks,
        })


# =====================================================
# VIEW: Historial de ataques de un jugador en todas las guerras
# =====================================================

class PlayerWarHistoryView(APIView):
    """
    GET /api/wars/player/{player_tag}/history/
    
    Historial de participación de un jugador en todas las guerras.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_tag):
        from players.models import Player

        clan = request.user.profile.clan

        tag = player_tag.upper()
        if not tag.startswith('#'):
            tag = f'#{tag}'

        try:
            player = Player.objects.get(clan=clan, player_tag=tag)
        except Player.DoesNotExist:
            return Response(
                {'error': f'Jugador {tag} no encontrado en tu clan.'},
                status=status.HTTP_404_NOT_FOUND
            )

        participations = WarParticipant.objects.filter(
            player=player
        ).select_related('war').prefetch_related('attacks').order_by('-war__end_time')

        history = []
        for p in participations:
            war = p.war
            attacks = list(p.attacks.all().values(
                'stars', 'destruction_percentage', 'defender_name',
                'defender_position', 'order', 'duration'
            ))

            history.append({
                'war_id': war.id,
                'opponent': war.opponent_name,
                'war_result': war.result,
                'war_end_time': war.end_time,
                'map_position': p.map_position,
                'town_hall_level': p.town_hall_level,
                'attacks_used': p.attacks_used,
                'total_stars': p.total_stars,
                'total_destruction': round(p.total_destruction_percentage, 1),
                'attacks': attacks,
            })

        # Resumen global
        total_attacks = sum(h['attacks_used'] for h in history)
        total_stars = sum(h['total_stars'] for h in history)
        avg_stars = round(total_stars / total_attacks, 2) if total_attacks > 0 else 0

        return Response({
            'player_tag': player.player_tag,
            'name': player.name,
            'summary': {
                'total_wars': len(history),
                'total_attacks': total_attacks,
                'total_stars': total_stars,
                'avg_stars_per_attack': avg_stars,
            },
            'history': history,
        })