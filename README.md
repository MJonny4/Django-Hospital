# P2-T5-MunteanuIon
+ El projecte té les següents funcionalitats:
+ - Primera pantalla introdueixes el nom d'usuari (login) el sistema comprova si existeix a la base de dades,
+ - si existeix, comprovem si l'usuari té o no té contrasenya, si té es redigit al login, si no té contrasenya es redigit al registre.
+ - si no existeix l'usuari es mostra un error.

+ Si l'usuari es metge i pacient, anira a una pantalla on es pot escollir quin rol vol tenir en aquesta sessió.

+ Funcionalitats de pacients:
+ - Demanar cita, si el pacient es metge no es pot demanar cita a si mateix.
+ - Veure les cites que té pendents, amb l'opció de modificar-les o eliminar-les.
+ - Veure les cites ja realitzades, per poder veure les dades (informe) de la cita.

+ Funcionalitats de metges:
+ - Agenda interactiva, on es pot veure les cites que té el metge, ja siguin cites pendents, cites realitzades o cites encara per fer.
+ - També pot marcar les cites com a realitzades interactuant amb la agenda.

+ Per a executar el projecte: 
+ - Executem el script de PowerShell "start.ps1" i anem al nevegador a la url: http://localhost:3500/

+ Altre informació:
+ - El projecte conté contingut JavaScript per fer funcionalitats asincrones i el framework TailwindCSS per a estils.
+ - Per a poder fer testos de l'aplicació es necesita tenir Models...
+ - No he tocat el Codi per a temor de fer-ho malament, i no fer malbé el projecte.

+ Paquets instal·lats:
+ - pip install pymongo
+ - pip install bycrypt
+ - pip install openxyl
+ - pip install dotenv-python
+ - pip install pandas
+ - pip install django
+ - pip install simplejson
