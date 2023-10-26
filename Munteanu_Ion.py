print("╔═══════════════════════════════════════════════════════════════════════════════════════════╗")
print("║                                                                                           ║")
print("╠═══════════════════════════════ Author: Ion Munteanu ══════════════════════════════════════╣")
print("╠═                                                                                         ═╣")
print("╠═           ██████████████╗        █████████████████╗       ████        ██╗               ═╣")
print("╠═           ╚════╗██╔═════╝        ██             ██║       ██ ██       ██║               ═╣")
print("╠═                ║██║              ██             ██║       ██  ██      ██║               ═╣")
print("╠═                ║██║              ██             ██║       ██   ██     ██║               ═╣")
print("╠═                ║██║              ██             ██║       ██    ██    ██║               ═╣")
print("╠═                ║██║              ██             ██║       ██     ██   ██║               ═╣")
print("╠═                ║██║              ██             ██║       ██      ██  ██║               ═╣")
print("╠═           ╔════╝██╚═════╗        ██             ██║       ██       ██ ██║               ═╣")
print("╠═           ███████████████        █████████████████╝       ██        ████╝               ═╣")
print("╠═                                                                                         ═╣")
print("╚═══════════════════════════════════════════════════════════════════════════════════════════╝")
import os
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

# Carreguem les variables d'entorn
load_dotenv()

# Connectem a MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
if client:
    print("Conectat a MongoDB")
else:
    print("Error de connexió a MongoDB")

# Obrim el fitxer 'Tasca3.xlsx'
file_errors_location = os.getenv("ARXIU")
df = pd.read_excel(file_errors_location)
users_list = df.to_dict('records')

# Connectem a la basa de dades 'imunteanu'
db = client[os.getenv("BD")]

# Creem les coleccions 'usuaris', 'pacients' i 'metges'
usuaris = db[os.getenv("USUARIS")]
pacients = db[os.getenv("PACIENTS")]
metges = db[os.getenv("METGES")]

# Creem els diccionaris per guardar els objectes de cada usuari
dict_pacients = {}
dict_metges = {}

# Insert de usuaris
for row in users_list:
    zero = '0'
    cognoms = row['Cognoms_i_Nom'].split(',')
    user = usuaris.insert_one({
        'id_temporal': row['id_temporal'],
        'DNI': row['DNI'] if type(row['DNI']) != float else None,
        'login': row['login'],
        'Sexe': row['Sexe'],
        'Nom': cognoms[1].lstrip(),
        'Cognoms': cognoms[0].lstrip(),
        'Data_Naixement': datetime.strptime(row['Data_Naixement'], '%Y-%m-%dT%H:%M:%S.%fZ') if type(
            row['Data_Naixement']) != float else None,
        'Adreça': row['Adreça'] if type(row['Adreça']) != float else None,
        'Població': row['Població'] if type(row['Població']) != float else None,
        'CP': str(zero) + str(row['CP']) if type(row['CP']) != float else None,
        'Província': row['Província'] if type(row['Província']) != float else None,
        'País': row['País'] if type(row['País']) != float else None,
    })

    print("Usari inserit: " + row['Cognoms_i_Nom'] + "")
    objectId = user.inserted_id

    if type(row['Mutua']) != float and type(row['Num_mutualista']) != float:
        pacient = {
            '_id': objectId,
            'Mutua': row['Mutua'],
            'Num_mutualista': row['Num_mutualista']
        }
        pacients.insert_one(pacient)
        dict_pacients[row["id_temporal"]] = pacient

    if type(row['Especialitat']) != float:
        metge = {
            '_id': objectId,
            'Num_colegiat': row['Num_colegiat'],
            'Especialitat': row['Especialitat']
        }
        metges.insert_one(metge)
        dict_metges[row["id_temporal"]] = metge

# Insertar horaris als metges
list_horaris = pd.read_excel(file_errors_location, sheet_name='HORARIS').to_dict('records')
semanas = pd.date_range(start='2023-01-01', end='2023-06-30', freq='W-MON').to_pydatetime().tolist()
for horari in list_horaris:
    metge = dict_metges[horari["id_temporal_metge"]]
    for semana in semanas:
        for dia in range(0, 6):
            if horari['Dilluns'] == 's' and dia == 0:
                for hora in range(horari['Inici Horari'].hour, horari['Fi Horari'].hour):
                    for minuts in range(0, 60, 30):
                        metges.update_one(
                            {'_id': metge["_id"]},
                            {'$push': {
                                'agenda': {
                                    'moment_visita': semana + timedelta(days=dia, hours=hora, minutes=minuts),
                                    'id_pacient': 0,
                                    'realitzada': "n",
                                    'informe': ''
                                }
                            }}
                        )
            if horari['Dimarts'] == 's' and dia == 1:
                for hora in range(horari['Inici Horari'].hour, horari['Fi Horari'].hour):
                    for minuts in range(0, 60, 30):
                        metges.update_one(
                            {'_id': metge["_id"]},
                            {'$push': {
                                'agenda': {
                                    'moment_visita': semana + timedelta(days=dia, hours=hora, minutes=minuts),
                                    'id_pacient': 0,
                                    'realitzada': "n",
                                    'informe': ''
                                }
                            }}
                        )
            if horari['Dimecres'] == 's' and dia == 2:
                for hora in range(horari['Inici Horari'].hour, horari['Fi Horari'].hour):
                    for minuts in range(0, 60, 30):
                        metges.update_one(
                            {'_id': metge["_id"]},
                            {'$push': {
                                'agenda': {
                                    'moment_visita': semana + timedelta(days=dia, hours=hora, minutes=minuts),
                                    'id_pacient': 0,
                                    'realitzada': "n",
                                    'informe': ''
                                }
                            }}
                        )
            if horari['Dijous'] == 's' and dia == 3:
                for hora in range(horari['Inici Horari'].hour, horari['Fi Horari'].hour):
                    for minuts in range(0, 60, 30):
                        metges.update_one(
                            {'_id': metge["_id"]},
                            {'$push': {
                                'agenda': {
                                    'moment_visita': semana + timedelta(days=dia, hours=hora, minutes=minuts),
                                    'id_pacient': 0,
                                    'realitzada': "n",
                                    'informe': ''
                                }
                            }}
                        )
            if horari['Divendres'] == 's' and dia == 4:
                for hora in range(horari['Inici Horari'].hour, horari['Fi Horari'].hour):
                    for minuts in range(0, 60, 30):
                        metges.update_one(
                            {'_id': metge["_id"]},
                            {'$push': {
                                'agenda': {
                                    'moment_visita': semana + timedelta(days=dia, hours=hora, minutes=minuts),
                                    'id_pacient': 0,
                                    'realitzada': "n",
                                    'informe': ''
                                }
                            }}
                        )
            if horari['Dissabte'] == 's' and dia == 5:
                for hora in range(horari['Inici Horari'].hour, horari['Fi Horari'].hour):
                    for minuts in range(0, 60, 30):
                        metges.update_one(
                            {'_id': metge["_id"]},
                            {'$push': {
                                'agenda': {
                                    'moment_visita': semana + timedelta(days=dia, hours=hora, minutes=minuts),
                                    'id_pacient': 0,
                                    'realitzada': "n",
                                    'informe': ''
                                }
                            }}
                        )
    print("Metge: ", metge["_id"], " Horari: ", horari["Inici Horari"], " - ", horari["Fi Horari"], " Insertat")

# Eliminar dies festius de la agenda dels metges
festius = pd.date_range(start='2023-04-02', end='2023-04-11', freq='D')
festius = festius.append(pd.date_range(start='2023-05-01', end='2023-05-01', freq='D'))
festius = festius.append(pd.date_range(start='2023-06-24', end='2023-06-24', freq='D'))
for metge in metges.find():
    for visita in metge["agenda"]:
        for festiu in festius:
            if festiu.date() == visita["moment_visita"].date():
                metges.update_one(
                    {'_id': metge["_id"]},
                    {'$pull': {
                        'agenda': {
                            'moment_visita': visita["moment_visita"]
                        }
                    }}
                )
                print("Metge: ", metge["_id"], " Visita: ", visita["moment_visita"], " Eliminada per festiu")

# Actualitzar visites ja realitzades
list_vistes = pd.read_excel(file_errors_location, sheet_name='VISITES').to_dict('records')
for visita in list_vistes:
    metge = dict_metges[visita["id_temporal_metge"]]
    metges.update_one(
        {'_id': metge["_id"],
            'agenda.moment_visita': datetime.strptime(visita["Moment_visita"], '%Y-%m-%dT%H:%M:%S.%fZ')},
        {'$set': {
            'agenda.$.id_pacient': usuaris.find_one({'id_temporal': visita["id_temporal_pacient"]})["_id"],
            'agenda.$.realitzada': visita["Realitzada"],
            'agenda.$.informe': visita["Informe"]
        }}
    )
    print("Metge: ", metge["_id"], " Dia: ", visita["Moment_visita"], " Actualitzat")

# Ordenar agenda del metge que te turn de tarda i mati
usuari = usuaris.find_one({'id_temporal': 6})
metge = metges.find_one({'_id': usuari["_id"]})
metges.update_one(
    {'_id': metge["_id"]},
    {'$set': {
        'agenda': sorted(metge["agenda"], key=lambda k: k['moment_visita'])
    }}
)
print("Metge: ", metge["_id"], " Agenda ordenada")

# Borrar camps nulls
for user in usuaris.find():
    for key in user:
        if user[key] is None:
            usuaris.update_one(
                {'_id': user["_id"]},
                {'$unset': {key: ''}}
            )
            print("Usuari: ", user["_id"], " Camp: ", key, " Eliminat")

# Borrar tots els id_temporal de la col·lecció usuaris
usuaris.update_many({}, {'$unset': {'id_temporal': ''}})
print("id_temporal eliminats de la col·lecció usuaris")
print("Script finalitzat")
