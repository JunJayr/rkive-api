from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from users.models import ApplicationDefense, PanelApplication, Faculty, SubmissionReview

class ApplicationDefenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDefense
        fields = '__all__'

class PanelApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanelApplication
        fields = '__all__'

class SubmissionReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionReview
        fields = '__all__'

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']