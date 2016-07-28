# VIPèRe

## Objectif
Cet outil permet de lancer des tests de vérification des données navitia et de visualiser les erreurs sur une carte afin de permettre de les corriger plus facilement.

## Installation
### Pour le BackEnd
L'execution se fait avec Python3, et certains packets sont necessaires :
* geojson
* shapely
* requests
* clingon

Pour les installer (sous Ubuntu/Debian) : `pip3 install -r requirements.txt`

### Pour le FrontEnd
Il s'agit d'un site en HTML/JS qui nécessite une configuration sur un serveur type Apache ou autre.

## Lancement des scripts
Deux modes de fonctionnement existent pour lancer les tests :

*Lancer un test seul* : il faut dans ce cas spécifier toutes les informations nécessaires à sa bonne exécution.  
Le endpoint et le coverage sont toujours obligatoires. D'autres paramètres peuvent être attendus en fonction du test.  
`python3 [script.py] [endpoint_name] [coverage]`

exemple :
`python3 check_bss_realtime.py customer fr-nw 45147 45234 45286`

*Lancer tous les tests* : Dans ce cas, la configuration se fait dans un fichier params.json à la racine de Vipère.
Il doit contenir
* la liste des endpoint navitia qu'il est possible d'appeler (l'url de Jormungandr, le token, l'url de Tyr)
* la liste des tests et leurs paramètres

Voir le fichier params.default.json pour le format.

Le lancement de tous les tests sur un des endpoint se fait alors via la commande :  
`python3 run_all_tests.py [endpoint_name]`  

## Fichiers de résutats
Chaque test écrit un fichier CSV par coverage selon la structure suivante :
* Chaque fichier doit s'appeler : `[env]_[coverage]_[test].csv`
* encodage : `utf-8`
* séparateur : ";"

Les champs du fichier csv sont :
* coverage
* env
* test_datetime
* object_id
* object_type
* test_category
* error
* infos
* error_level (green / orange / red)
* wkt
