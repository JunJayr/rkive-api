from rest_framework import serializers
from .models import ApplicationDefense, PanelDefense, Faculty

class ApplicationDefenseSerializer(serializers.ModelSerializer):
    adviser = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel_chair = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel1 = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel2 = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel3 = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())

    class Meta:
        model = ApplicationDefense
        fields = '__all__'

class PanelDefenseSerializer(serializers.ModelSerializer):
    adviser = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel_chair = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel1 = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel2 = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())
    panel3 = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all())

    class Meta:
        model = PanelDefense
        fields = '__all__'