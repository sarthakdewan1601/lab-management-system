from email.headerregistry import Group
import django_filters
from django_filters import CharFilter
from .models import *

class filterRoom(django_filters.FilterSet):
    name=CharFilter(field_name='name',lookup_expr='icontains')
    class Meta:
        model=Room
        fields = ['floor','is_lab']

class filterCourse(django_filters.FilterSet):
    course_id=CharFilter(field_name='course_id',lookup_expr='icontains')
    course_name=CharFilter(field_name='course_name',lookup_expr='icontains')
    class Meta:
        model=Course
        fields = ['course_year','semester_type']

class filterGroup(django_filters.FilterSet):
    group_id=CharFilter(field_name='group_id',lookup_expr='icontains')
    class Meta:
        model=Groups
        fields = ['branch','group_year','semester_type']


