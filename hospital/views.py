from datetime import datetime

import bcrypt as bcrypt
import simplejson as json
from bson import ObjectId
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .connection import connect
from .decorators import authentication_required

salt = bcrypt.gensalt()
client = connect()
db = client['HOSPITAL']
usuaris = db['USUARIS']
metges = db['METGES']
pacients = db['PACIENTS']


# Create your views here.
@authentication_required
def index(request):
    if request.POST.get('login'):
        user = usuaris.find_one({"login": request.POST.get('login')})
        if user:
            if 'contrasenya' in user:
                return redirect('/login')
            else:
                url = "/register/" + request.POST.get('login')
                return redirect(url)
        else:
            error = "Usuari no existeix o incorrecte"
            return render(request, 'index.html', {'error': error})
    else:
        return render(request, 'index.html')


@authentication_required
def register(request, login):
    if request.POST.get('contrasenya') and request.POST.get('contrasenya2'):
        if request.POST.get('contrasenya') == request.POST.get('contrasenya2'):
            contrasenya = bcrypt.hashpw(request.POST.get(
                'contrasenya').encode('utf-8'), salt)
            usuaris.update_one(
                {"login": login}, {"$set": {"contrasenya": contrasenya}})
            return redirect('/login')
        else:
            error = "Les contrasenyes no coincideixen"
            return render(request, 'register.html', {'error': error})
    else:
        return render(request, 'register.html', {'login': login})


@authentication_required
def login(request):
    if request.POST.get('login') and request.POST.get('contrasenya'):
        user = usuaris.find_one({"login": request.POST.get('login')})
        if user:
            if 'contrasenya' in user:
                contrasenya = bcrypt.checkpw(request.POST.get('contrasenya').encode('utf-8'), user['contrasenya'])
                if contrasenya:
                    request.session['login'] = request.POST.get('login')

                    metge = metges.find_one({"_id": user['_id']})
                    pacient = pacients.find_one({"_id": user['_id']})

                    if metge is not None and pacient is not None:
                        return redirect('/rol')
                    elif metge is not None and pacient is None:
                        request.session['metge'] = True
                        return redirect('/metge')
                    elif pacient is not None and metge is None:
                        request.session['pacient'] = True
                        return redirect('/pacient')
                else:
                    error = "Contrasenya incorrecta"
                    return render(request, 'login.html', {'error': error})
            else:
                error = "Aquest usuari no té contrasenya"
                return render(request, 'login.html', {'error': error})
        else:
            error = "Usuari no existeix o incorrecte"
            return render(request, 'login.html', {'error': error})
    else:
        return render(request, 'login.html')


def logout(request):
    login = request.session.get('login')
    if login:
        del request.session['login']
        if request.session.get('pacient') or request.session.get('metge'):
            if request.session.get('pacient'):
                del request.session['pacient']
            if request.session.get('metge'):
                del request.session['metge']
        return redirect('/')
    else:
        return redirect('/')


def rol(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    nom_complet = user['Nom'] + " " + user['Cognoms']

    if request.POST.get('rol'):
        rol = request.POST.get('rol')
        if rol == '1':
            request.session['pacient'] = True
            request.session['metge'] = False
            return redirect('/pacient')
        elif rol == '2':
            request.session['metge'] = True
            request.session['pacient'] = False
            return redirect('/metge')
        else:
            error = "Si us plau, selecciona un rol"
            return render(request, 'rol.html', {'error': error, 'user': nom_complet})
    else:
        if login:
            if request.session.get('pacient'):
                return redirect('/pacient')
            elif request.session.get('metge'):
                return redirect('/metge')
            else:
                return render(request, 'rol.html', {'user': nom_complet})
        else:
            return redirect('/')


def pacient(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    pacient = request.session.get('pacient')

    if login and pacient:
        if 'Nom' in user and 'Cognoms' in user:
            nom_complet = user['Nom'] + " " + user['Cognoms']
            return render(request, 'pacient/pacient.html', {'user': nom_complet})
        else:
            return render(request, 'pacient/pacient.html')
    elif login:
        return redirect('/metge')
    else:
        return redirect('/')


def metge(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    metge = request.session.get('metge')

    if login and metge:
        if 'Nom' in user and 'Cognoms' in user:
            nom_complet = user['Nom'] + " " + user['Cognoms']
            return render(request, 'metge/metge.html', {'user': nom_complet})
        else:
            return render(request, 'metge/metge.html')
    elif login:
        return redirect('/pacient')
    else:
        return redirect('/')


# * Funcionality PACIENT
def visites(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    pacient_id = request.session.get('pacient')
    nom_complet = user['Nom'] + " " + user['Cognoms']
    metges_noms = llista_metges(login)

    if 'cita' in request.POST:
        metge = request.POST.get('metge')
        dates = metges.find_one({"_id": ObjectId(metge)}).get('agenda')
        list_dates = []
        for data in dates:
            list_dates.append(data.get('moment_visita').date())
        list_dates = list(dict.fromkeys(list_dates))

        return render(request, 'pacient/visites.html',
                      {'user': nom_complet, 'metges': metges_noms, 'dies': list_dates, 'metge_id': metge})
    elif 'demanar' in request.POST:
        pacient_id = usuaris.find_one({"_id": ObjectId(user['_id'])})
        mhp = request.POST.get('mhp')
        dia = request.POST.get('dia')
        hora = request.POST.get('hora')
        demanar = demanar_visita(mhp, pacient_id, dia, hora)
        return render(request, 'pacient/visites.html',
                      {'user': nom_complet, 'metges': metges_noms, 'demanada': demanar})

    else:
        if login and pacient_id:
            return render(request, 'pacient/visites.html', {'user': nom_complet, 'metges': metges_noms})
        else:
            return redirect('/')


def llista_metges(login):
    metge_pacient = usuaris.find_one({"login": login})
    list_metges = []
    for metge in metges.find():
        if metge.get('_id') != metge_pacient.get('_id'):
            metge_id = metge.get('_id')
            metge_nom = usuaris.find_one({"_id": metge_id}).get('Nom')
            metge_cognoms = usuaris.find_one({"_id": metge_id}).get('Cognoms')
            metge_nom_complet = metge_nom + " " + metge_cognoms
            dict_metges = {'id': metge_id, 'nom': metge_nom_complet}
            list_metges.append(dict_metges)
        else:
            continue
    return list_metges


def llista_visites(request, metge_dia):
    metge = metge_dia.split("_")[0]
    dia = metge_dia.split("_")[1]
    dia = datetime.strptime(dia, '%Y-%m-%d').date()
    dates = metges.find_one({"_id": ObjectId(metge)}).get('agenda')
    list_dates = []
    for data in dates:
        if data.get('moment_visita').date() == dia:
            if data.get('id_pacient') == 0:
                list_dates.append(data.get('moment_visita').time())
            else:
                print("Hora ocupada")
    return JsonResponse(list_dates, safe=False)


def demanar_visita(mhp, pacient, dia, hora):
    dia = dia.replace('/', '-')
    dia = dia.split('-')
    dia = dia[2] + '-' + dia[1] + '-' + dia[0]
    metge = metges.find_one({"_id": ObjectId(mhp)})
    metge_usuaris = usuaris.find_one({"_id": ObjectId(mhp)})
    dia = datetime.strptime(dia, '%Y-%m-%d').date()
    hora = datetime.strptime(hora, '%H:%M:%S').time()
    moment_visita = datetime.combine(dia, hora)
    if metge['agenda']:
        for cita in metge['agenda']:
            if cita['moment_visita'] == moment_visita:
                cita['id_pacient'] = pacient['_id']
                metges.update_one({'_id': ObjectId(mhp)}, {'$set': {'agenda': metge['agenda']}})

    missatge = "La teva visita amb el/la " + metge_usuaris['Nom'] + " " + metge_usuaris[
        'Cognoms'] + " ha estat demanada correctament Pel dia " + str(dia) + " a les " + str(hora) + "h" + "."
    return missatge


# * Modificar Visites Pacient
def vista_modificar(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    pacient = request.session.get('pacient')
    nom_complet = user['Nom'] + " " + user['Cognoms']
    lista_visites = get_pacient_visites(request, login)

    if 'modificar' in request.POST:
        if request.session['borrar']:
            borrar_visita(request)
        metge_id = get_metge_id(request, request.POST.get('metge'))
        metge = metges.find_one({"_id": ObjectId(metge_id)})
        dia = datetime.strptime(request.POST.get('dia'), '%Y-%m-%d').date()
        hora = datetime.strptime(request.POST.get('hora'), '%H:%M:%S').time()
        moment_visita = datetime.combine(dia, hora)
        pacient_id = usuaris.find_one({"login": login}).get('_id')
        if metge['agenda']:
            for cita in metge['agenda']:
                if cita['moment_visita'] == moment_visita:
                    cita['id_pacient'] = pacient_id
                    metges.update_one({'_id': ObjectId(metge['_id'])}, {'$set': {'agenda': metge['agenda']}})
        new_lista_visites = get_pacient_visites(request, login)
        missatge = "La teva visita amb el/la " + usuaris.find_one({"_id": ObjectId(metge_id)}).get(
            'Nom') + " " + usuaris.find_one({"_id": ObjectId(metge_id)}).get(
            'Cognoms') + " ha estat modificada correctament Pel dia " + str(dia) + " a les " + str(hora) + "h" + "."
        return render(request, 'pacient/modificar.html',
                      {'user': nom_complet, 'visites': new_lista_visites, 'missatge': missatge})
    elif 'eliminar' in request.POST:
        id_post = request.POST.get('id')
        id_post = id_post.split('/')
        dia = id_post[0]
        hora = id_post[1]
        metge = id_post[2]
        metge_id = get_metge_id(request, metge)
        metge = metges.find_one({"_id": ObjectId(metge_id)})
        dia = datetime.strptime(dia, '%Y-%m-%d').date()
        hora = datetime.strptime(hora, '%H:%M:%S').time()
        moment_visita = datetime.combine(dia, hora)
        if metge['agenda']:
            for cita in metge['agenda']:
                if cita['moment_visita'] == moment_visita:
                    cita['id_pacient'] = 0
                    metges.update_one({'_id': ObjectId(metge['_id'])}, {'$set': {'agenda': metge['agenda']}})
        new_lista_visites = get_pacient_visites(request, login)
        missatge = "La teva visita amb el/la " + usuaris.find_one({"_id": ObjectId(metge_id)}).get(
            'Nom') + " " + usuaris.find_one({"_id": ObjectId(metge_id)}).get(
            'Cognoms') + " ha estat eliminada correctament Del dia " + str(dia) + " a les " + str(hora) + "h" + "."
        return render(request, 'pacient/modificar.html',
                      {'user': nom_complet, 'visites': new_lista_visites, 'missatge_red': missatge})
    elif login and pacient:
        return render(request, 'pacient/modificar.html', {'user': nom_complet, 'visites': lista_visites})
    else:
        return redirect('/')


def get_pacient_visites(request, login):
    list_visites = []
    dict_visites = {}
    ids_metges = []
    pacient_id = usuaris.find_one({"login": login}).get('_id')
    for metge in metges.find():
        for cita in metge['agenda']:
            if cita['id_pacient'] == pacient_id:
                ids_metges.append(metge['_id'])
    for id_metge in ids_metges:
        for cita in metges.find_one({"_id": id_metge}).get('agenda'):
            if cita['id_pacient'] == pacient_id and cita['realitzada'] == "n":
                metge_nom = usuaris.find_one({"_id": id_metge}).get('Nom')
                metge_cognoms = usuaris.find_one({"_id": id_metge}).get('Cognoms')
                metge_nom_complet = metge_nom + " " + metge_cognoms
                hora = cita['moment_visita'].time().strftime('%H:%M:%S')
                dia = cita['moment_visita'].date()
                dict_visites = {'metge': metge_nom_complet, 'hora': hora, 'dia': dia}
                list_visites.append(dict_visites)

    for visites in list_visites:
        if list_visites.count(visites) > 1:
            list_visites.remove(visites)

    return list_visites


def get_visita_per_modificar(request, dia, hora, metge):
    nom = ""
    cognoms = ""
    metge = metge.split(" ")
    if len(metge) == 4:
        nom = metge[0] + " " + metge[1]
        cognoms = metge[2] + " " + metge[3]
    elif len(metge) == 3:
        nom = metge[0]
        cognoms = metge[1] + " " + metge[2]
    else:
        nom = metge[0]
        cognoms = metge[1]

    borrar = dia + "_" + hora + "_" + nom + " " + cognoms
    request.session['borrar'] = borrar

    metge = usuaris.find_one({"Nom": nom, "Cognoms": cognoms}).get('_id')
    dia = datetime.strptime(dia, '%Y-%m-%d').date()
    hora = datetime.strptime(hora, '%H:%M:%S').time()
    moment_visita = datetime.combine(dia, hora)
    metge = metges.find_one({"_id": ObjectId(metge)})
    list_dates = []
    for data in metge['agenda']:
        if data.get('moment_visita') == moment_visita or data.get('realitzada') == "s":
            continue
        else:
            if data.get('id_pacient') == 0:
                list_dates.append(data.get('moment_visita'))
            else:
                print("Hora ocupada " + str(data.get('moment_visita')))
    return JsonResponse(list_dates, safe=False)


def borrar_visita(request):
    borrar = request.session['borrar']
    borrar = borrar.split("_")
    dia = borrar[0]
    hora = borrar[1]
    metge_id = get_metge_id(request, borrar[2])
    dia = datetime.strptime(dia, '%Y-%m-%d').date()
    hora = datetime.strptime(hora, '%H:%M:%S').time()
    moment_visita = datetime.combine(dia, hora)
    metge = metges.find_one({"_id": ObjectId(metge_id)})
    for data in metge['agenda']:
        if data.get('moment_visita') == moment_visita:
            data['id_pacient'] = 0
            metges.update_one({'_id': ObjectId(metge['_id'])}, {'$set': {'agenda': metge['agenda']}})
            break


def get_metge_id(request, nom_complet):
    nom = ""
    cognoms = ""
    nom_complet = nom_complet.split(" ")
    if len(nom_complet) == 4:
        nom = nom_complet[0] + " " + nom_complet[1]
        cognoms = nom_complet[2] + " " + nom_complet[3]
    elif len(nom_complet) == 3:
        nom = nom_complet[0]
        cognoms = nom_complet[1] + " " + nom_complet[2]
    else:
        nom = nom_complet[0]
        cognoms = nom_complet[1]

    metge = usuaris.find_one({"Nom": nom, "Cognoms": cognoms}).get('_id')
    return metge


# Visites finalitzades
def vista_finalitzades(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    pacient = request.session.get('pacient')
    nom_complet = user['Nom'] + " " + user['Cognoms']

    if login and pacient:
        lista_realitzades = get_visita_per_finalitzar(request, login)
        return render(request, 'pacient/finalitzades.html', {'user': nom_complet, 'visites': lista_realitzades})
    else:
        return redirect('/')


def get_visita_per_finalitzar(request, login):
    list_visites = []
    dict_visites = {}
    ids_metges = []
    pacient_id = usuaris.find_one({"login": login}).get('_id')
    for metge in metges.find():
        for cita in metge['agenda']:
            if cita['id_pacient'] == pacient_id:
                ids_metges.append(metge['_id'])
    for id_metge in ids_metges:
        for cita in metges.find_one({"_id": id_metge}).get('agenda'):
            if cita['id_pacient'] == pacient_id and cita['realitzada'] == "s":
                metge_nom = usuaris.find_one({"_id": id_metge}).get('Nom')
                metge_cognoms = usuaris.find_one({"_id": id_metge}).get('Cognoms')
                metge_nom_complet = metge_nom + " " + metge_cognoms
                hora = cita['moment_visita'].time().strftime('%H:%M:%S')
                dia = cita['moment_visita'].date()
                informe = cita['informe']
                dict_visites = {'metge': metge_nom_complet, 'hora': hora, 'dia': dia, 'informe': informe}
                list_visites.append(dict_visites)

    for visites in list_visites:
        if list_visites.count(visites) > 1:
            list_visites.remove(visites)

    return list_visites


# ? Funcionalitats metges
def vista_consultar_agenda(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    metge_session = request.session.get('metge')
    nom_complet = user['Nom'] + " " + user['Cognoms']

    if 'pacient' in request.POST:
        if request.POST['realitzada'] == "n":
            missatge = "La visita esta a pendent de ser realitzada"
            agenda = get_agenda(request, login)
            return render(request, 'metge/agenda.html',
                          {'user': nom_complet, 'agenda': json.dumps(agenda, indent=4, sort_keys=True, default=str),
                           'missatge': missatge})
        elif request.POST['realitzada'] == "s" and request.POST['informe'].strip() == "":
            error = "No pots finalitzar una visita sense informe"
            agenda = get_agenda(request, login)
            return render(request, 'metge/agenda.html',
                          {'user': nom_complet, 'agenda': json.dumps(agenda, indent=4, sort_keys=True, default=str),
                           'error': error})
        else:
            dia_hora = request.POST['dia_hora']
            realitzada = request.POST['realitzada']
            informe = request.POST['informe']
            dia_hora = dia_hora.split(", ")
            dia = dia_hora[0]
            hora = dia_hora[1]
            dia = datetime.strptime(dia, '%d/%m/%Y').date()
            hora = datetime.strptime(hora, '%H:%M:%S').time()
            moment_visita = datetime.combine(dia, hora)
            metge_id = get_metge_id(request, nom_complet)
            metge = metges.find_one({"_id": ObjectId(metge_id)})
            for data in metge['agenda']:
                if data.get('moment_visita') == moment_visita:
                    data['realitzada'] = realitzada
                    data['informe'] = informe
                    metges.update_one({'_id': ObjectId(metge['_id'])}, {'$set': {'agenda': metge['agenda']}})
                    break

            missatge = "Visita finalitzada amb èxit"
            agenda = get_agenda(request, login)
            return render(request, 'metge/agenda.html',
                          {'user': nom_complet, 'agenda': json.dumps(agenda, indent=4, sort_keys=True, default=str),
                           'missatge': missatge})
    elif login and metge_session:
        agenda = get_agenda(request, login)
        return render(request, 'metge/agenda.html',
                      {'user': nom_complet, 'agenda': json.dumps(agenda, indent=4, sort_keys=True, default=str)})
    else:
        return redirect('/')


def get_agenda(request, login):
    metge_id = usuaris.find_one({"login": login}).get('_id')
    metge = metges.find_one({"_id": ObjectId(metge_id)})
    list_dates = []
    for data in metge['agenda']:
        if data.get('id_pacient') != 0:
            pacient = usuaris.find_one({"_id": ObjectId(data.get('id_pacient'))})
            nom_complet = pacient.get('Nom') + " " + pacient.get('Cognoms')
            list_dates.append(
                {'hora': data.get('moment_visita').time().strftime('%H:%M:%S'), 'dia': data.get('moment_visita').date(),
                 'pacient': nom_complet, 'realitzada': data.get('realitzada')})
        else:
            list_dates.append(
                {'hora': data.get('moment_visita').time().strftime('%H:%M:%S'), 'dia': data.get('moment_visita').date(),
                 'pacient': "Lliure", 'realitzada': data.get('realitzada')})
    return list_dates


def consultar_pacients(request):
    login = request.session.get('login')
    user = usuaris.find_one({"login": login})
    metge_session = request.session.get('metge')
    nom_complet = user['Nom'] + " " + user['Cognoms']

    if 'pacient' in request.POST:
        pacient_id = request.POST['pacient']
        visites = get_visites_x_pacient(request, pacient_id)
        l_pacients = get_pacients(request)
        return render(request, 'metge/consultar.html ',
                      {'user': nom_complet, 'pacients': l_pacients, 'visites': visites})
    elif login and metge_session:
        l_pacients = get_pacients(request)
        return render(request, 'metge/consultar.html', {'user': nom_complet, 'pacients': l_pacients})
    else:
        return redirect('/')


def get_pacients(request):
    list_ids_pacients = []
    list_pacients = []
    dict_pacients = {}

    for pacient in pacients.find():
        list_ids_pacients.append(pacient['_id'])

    for id_pacient in list_ids_pacients:
        pacient = usuaris.find_one({"_id": id_pacient})
        nom_complet = pacient['Nom'] + " " + pacient['Cognoms']
        dict_pacients = {'id': id_pacient, 'nom_complet': nom_complet}
        list_pacients.append(dict_pacients)
    return list_pacients


def get_visites_x_pacient(request, id_pacient):
    list_visites = []
    dict_visites = {}
    for metge in metges.find():
        for visita in metge['agenda']:
            if visita.get('id_pacient') == ObjectId(id_pacient) and visita.get('realitzada') == "s":
                hora = visita.get('moment_visita').time().strftime('%H:%M:%S')
                dia = visita.get('moment_visita').date()
                informe = visita.get('informe')
                dict_visites = {'hora': hora, 'dia': dia, 'informe': informe}
                list_visites.append(dict_visites)
    return list_visites
