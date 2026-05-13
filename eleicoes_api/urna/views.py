from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Eleitor,Eleicao,Candidato,AptidaoEleitor, RegistroVotacao, Voto
from .serializers import EleitorSerializer, EleicaoSerializer, CandidatoSerializer, AptidaoEleitorSerializer, RegistroVotacaoSerializer, VotoSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count

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

    class EleicaoViewSet(viewsets.ModelViewSet):
    queryset = Eleicao.objects.all().order_by("data_inicio")
    serializer_class = EleicaoSerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["titulo"]
    filterset_fields = ["status", "tipo", "criada_por"]

    @action(detail=True, methods=["post"])
    def abrir(self, request, pk=None):
        eleicao = self.get_object()

        if eleicao.status != "rascunho":
            return Response({"error": "Só rascunho pode abrir"}, status=400)

        if eleicao.candidatos.count() < 2:
            return Response({"error": "Precisa 2 candidatos"}, status=400)

        if eleicao.aptos.count() < 1:
            return Response({"error": "Precisa eleitores aptos"}, status=400)

        eleicao.status = "aberta"
        eleicao.save()

        return Response(self.get_serializer(eleicao).data)

    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        eleicao = self.get_object()

        if eleicao.status != "aberta":
            return Response({"error": "Não está aberta"}, status=400)

        eleicao.status = "encerrada"
        eleicao.save()

        return Response(self.get_serializer(eleicao).data)

    @action(detail=True, methods=["get"])
    def apuracao(self, request, pk=None):
        eleicao = self.get_object()

        if eleicao.status not in ["encerrada", "apurada"]:
            return Response({"error": "Não pode apurar ainda"}, status=403)

        votos = eleicao.votos.all()
        candidatos = eleicao.candidatos.all()

        total_aptos = eleicao.aptos.count()
        total_votantes = eleicao.registros_votacao.count()
        total_abstencoes = total_aptos - total_votantes

        votos_brancos = votos.filter(em_branco=True).count()
        votos_validos = votos.filter(em_branco=False).count()

        resultado = []
        total_validos = votos_validos if votos_validos > 0 else 1

        for c in candidatos:
            qtd = votos.filter(candidato=c).count()
            resultado.append({
                "candidato": c.nome_urna,
                "numero": c.numero,
                "votos": qtd,
                "percentual": round((qtd / total_validos) * 100, 2),
            })

        resultado.sort(key=lambda x: x["votos"], reverse=True)

        maior = max([r["votos"] for r in resultado], default=0)
        vencedores = [r["candidato"] for r in resultado if r["votos"] == maior]

        houve_empate = len(vencedores) > 1

        if eleicao.status == "encerrada":
            eleicao.status = "apurada"
            eleicao.save()

        return Response({
            "eleicao": eleicao.titulo,
            "total_aptos": total_aptos,
            "total_votantes": total_votantes,
            "total_abstencoes": total_abstencoes,
            "votos_validos": votos_validos,
            "votos_brancos": votos_brancos,
            "comparecimento_pct": round((total_votantes / total_aptos) * 100, 2) if total_aptos else 0,
            "resultado": resultado,
            "vencedores": vencedores,
            "houve_empate": houve_empate
        })

    @action(detail=True, methods=["get"])
    def votantes(self, request, pk=None):
        eleicao = self.get_object()

        compareceu = request.query_params.get("compareceu")

        registros = eleicao.registros_votacao.select_related("eleitor")
        votaram_ids = registros.values_list("eleitor_id", flat=True)

        if compareceu == "false":
            aptos = eleicao.aptos.select_related("eleitor").exclude(
                eleitor_id__in=votaram_ids
            )

            return Response([
                {
                    "nome": a.eleitor.nome,
                    "cpf": a.eleitor.cpf[:3] + ".***.***-" + a.eleitor.cpf[-2:],
                    "status": "absteve"
                }
                for a in aptos
            ])

        return Response([
            {
                "nome": r.eleitor.nome,
                "cpf": r.eleitor.cpf[:3] + ".***.***-" + r.eleitor.cpf[-2:],
                "data_hora": r.data_hora
            }
            for r in registros
        ])

    @action(detail=True, methods=["post"])
    def cadastrar_aptos(self, request, pk=None):
        eleicao = self.get_object()

        if eleicao.status != "rascunho":
            return Response({"error": "Só em rascunho"}, status=400)

        ids = request.data.get("eleitores_ids", [])

        criados = 0

        for eid in ids:
            _, created = AptidaoEleitor.objects.get_or_create(
                eleitor_id=eid,
                eleicao=eleicao
            )
            if created:
                criados += 1

        return Response({"total_cadastrados": criados})

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