from datetime import datetime
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from random import randint
from .models import Sensor, Location, User, SensorData


class DashboardView(TemplateView):
    template_name = 'index.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']            if action == 'get_graph_online':
                login = request.POST['login']
                locationName = request.POST['location']
                user = get_or_create_user(login)
                location = get_or_create_location(locationName)
                sensor = get_or_create_sensor('temperatura', user, location)
                last = SensorData.objects.filter(sensor=sensor).order_by('-dateTime').first()
                data = {'y': last.value if last else 0}

                print(data)
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

def get_or_create_user(login):
    try:
        user = User.objects.get(login=login)
    except User.DoesNotExist:
        user = User(login=login)
        user.save()
    return(user)

def get_or_create_location(name):
    try:
        location = Location.objects.get(name=name)
    except Location.DoesNotExist:
        location = Location(name=name)
        location.save()
    return(location)

def get_or_create_sensor(variable, user, location):
    try:
        sensor = Sensor.objects.get(variable=variable, user=user, location=location)
    except Sensor.DoesNotExist:
        sensor = Sensor(variable=variable, user=user, location=location)
        sensor.save()
    return(sensor)

def get_sensor(variable, user, location):
    sensor = Sensor.objects.get(variable=variable, user=user, location=location)
    return(sensor)

def create_sensorData(sensor, value):
    sensorData = SensorData(sensor=sensor, value=value)
    sensorData.save()
    return()

def get_last_measure(sensor):
    last_measure = SensorData.objects.filter(sensor=sensor).latest('dateTime')
    print(last_measure.dateTime)
    print(datetime.now())
    return(last_measure.value)


class HistoricalView(TemplateView):
    template_name = 'historical.html'
