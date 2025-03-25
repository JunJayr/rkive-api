from rest_framework import serializers
from users.models import ApplicationDefense, PanelDefense, Faculty

class ApplicationDefenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDefense
        fields = '__all__'

class PanelDefenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanelDefense
        fields = '__all__'
