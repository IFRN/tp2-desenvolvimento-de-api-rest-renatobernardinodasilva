from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Eleitor,Eleicao,Candidato,AptidaoEleitor, RegistroVotacao, Voto
from .serializers import EleitorSerializer, EleicaoSerializer, CandidatoSerializer, AptidaoEleitorSerializer, RegistroVotacaoSerializer, VotoSerializer


class EleitorViewSet(viewsets.ModelViewSet):
    queryset = Eleitor.objects.all()
    serializer_class = EleitorSerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nome", "email", "cpf"]
    filterset_fields = ["ativo"]

class EleicaoViewSet(viewsets.ModelViewSet):
    queryset = Eleicao.objects.all().order_by("data_inicio")
    serializer_class = EleicaoSerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["titulo"]
    filterset_fields = ["status", "tipo", "criada_por"]

class CandidatoViewSet(viewsets.ModelViewSet):
    queryset = Candidato.objects.select_related("eleicao").all()
    serializer_class = CandidatoSerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nome", "nome_urna", "partido_ou_chapa"]
    filterset_fields = ["eleicao"]

class AptidaoEleitorViewSet(viewsets.ModelViewSet):
    queryset = AptidaoEleitor.objects.select_related("eleitor", "eleicao").all()
    serializer_class = AptidaoEleitorSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["eleitor", "eleicao"]

class RegistroVotacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistroVotacao.objects.all().order_by("-data_hora")
    serializer_class = RegistroVotacaoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["eleicao"]

class VotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Voto.objects.all()
    serializer_class = VotoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["eleicao"]