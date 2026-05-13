from rest_framework import serializers
from django.utils import timezone
import re

from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, RegistroVotacao, Voto


class EleitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eleitor
        fields = "__all__"

    def validate_cpf(self, value):
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", value):
            raise serializers.ValidationError("CPF inválido")
        return value


class EleicaoSerializer(serializers.ModelSerializer):
    total_candidatos = serializers.SerializerMethodField()
    total_aptos = serializers.SerializerMethodField()

    class Meta:
        model = Eleicao
        fields = "__all__"

    def get_total_candidatos(self, obj):
        return obj.candidatos.count()

    def get_total_aptos(self, obj):
        return obj.aptos.count()


class CandidatoSerializer(serializers.ModelSerializer):
    eleicao_titulo = serializers.CharField(source="eleicao.titulo", read_only=True)

    class Meta:
        model = Candidato
        fields = "__all__"

    def validate_numero(self, value):
        if value == 0:
            raise serializers.ValidationError("Número 0 não permitido")
        return value


class AptidaoEleitorSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.CharField(source="eleitor.nome", read_only=True)
    eleicao_titulo = serializers.CharField(source="eleicao.titulo", read_only=True)

    class Meta:
        model = AptidaoEleitor
        fields = "__all__"


class RegistroVotacaoSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.CharField(source="eleitor.nome", read_only=True)
    eleicao_titulo = serializers.CharField(source="eleicao.titulo", read_only=True)

    class Meta:
        model = RegistroVotacao
        fields = "__all__"
        read_only_fields = fields


class VotoSerializer(serializers.ModelSerializer):
    candidato_nome_urna = serializers.CharField(
        source="candidato.nome_urna",
        read_only=True
    )

    class Meta:
        model = Voto
        fields = [
            "id",
            "eleicao",
            "candidato",
            "em_branco",
            "data_hora",
            "candidato_nome_urna",
        ]
        extra_kwargs = {
            "comprovante_hash": {"write_only": True},
        }


class VotacaoInputSerializer(serializers.Serializer):
    eleitor_id = serializers.IntegerField()
    eleicao_id = serializers.IntegerField()
    candidato_id = serializers.IntegerField(required=False)
    em_branco = serializers.BooleanField(default=False)

    def validate(self, data):
        eleicao = Eleicao.objects.filter(id=data["eleicao_id"]).first()
        if not eleicao:
            raise serializers.ValidationError("Eleição não existe")

        if eleicao.status != "aberta":
            raise serializers.ValidationError("Eleição fechada")

        now = timezone.now()
        if not (eleicao.data_inicio <= now <= eleicao.data_fim):
            raise serializers.ValidationError("Fora do período")

        apto = AptidaoEleitor.objects.filter(
            eleitor_id=data["eleitor_id"],
            eleicao_id=data["eleicao_id"]
        ).exists()

        if not apto:
            raise serializers.ValidationError("Eleitor não apto")

        ja_votou = Voto.objects.filter(
            eleitor_id=data["eleitor_id"],
            eleicao_id=data["eleicao_id"]
        ).exists()

        if ja_votou:
            raise serializers.ValidationError("Já votou")

        if data.get("candidato_id"):
            if not Candidato.objects.filter(
                id=data["candidato_id"],
                eleicao_id=data["eleicao_id"]
            ).exists():
                raise serializers.ValidationError("Candidato inválido")

        return data