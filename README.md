# Update database 

# Configuration

## Fichier excel à insérer

Le script main.py nécessite un fichier excel en entrée. Ce fichier contient une ou plusieurs colonnes contenant les données à insérer en base de données. Il contient également une ou plusieurs colonnes permettant de filtrer et d'identifier les données à mettre à jour. 

Le fichier doit commencer à la première colonne. Le nom des colonnes doit figurer en première ligne. Une fois le fichier prêt il faut le déplacer dans le répertoire [./data_to_update](./data_to_update)

Ci-dessous un exemple de fichier permettant de mettre à jour l'aire plantée en hectare, en identifiant les parcels par le nom du fichier GPS:

![Excel file image](/img/excel_capture.png)

## Fichier de configuration

Le fichier de configuration est au format .json. Il se présente de cette manière.

```json
{
	"Columns_to_update" : {},
	"Joins": {},
	"Identifying_columns": {}
}
```
### 1. "Columns_to_update":

On doit y ajouter autant de clés qu'il y'a de colonnes contenant des nouvelles données dans le fichier excel. 

- Dans [l'image ci-dessus ](##Fichier-excel-à-insérer), nous n'avons qu'une seule colonne avec des nouvelles données: **Planted_area_ha**. Le nom de cette colonne doit être ajouté en tant que clé dans **"Columns_to_update"**. 
- Ensuite, la clé *"Planted_area_ha"* doit avoir comme valeur un objet contenant deux clés: *"table_name"* et *"field_name"*. 
La clé *"table_name"* correspond à la table qui contient ce champ en base de données, il s'agit de la table *"parcels"* dans notre cas. 
Le champ *"field_name"* correspond au nom du champ dans la table *"parcels"*, dans notre exemple il s'agit du champ *"plantedarea"*.

```json
{
	"Columns_to_update" : {
		"Planted_area_ha": {
		"table_name" : "parcels",
		"field_name" : "plantedarea"
		}
	}, 
	...
}
```
### 2. "Identifying_columns":

Afin d'identifier en base de données les données à mettre à jour. Il est nécessaire d'avoir au moins une colonne qui va permettre de filtrer la base de donnée via une requête *WHERE*. Dans [l'image ci-dessus ](##Fichier-excel-à-insérer), nous avons une seule colonne : **Name_GPS_track**. Cette colonne permet d'identifier les parcelles afin de mettre à jour l'information *"plantedarea"* au bon endroit. 

- Dans le champ *"Identifying_columns"*, on doit premièrement insérer une clé avec comme valeur la colonne contenant les nouvelles données (ici *"Planted_area_ha"*).
- Dans le champ *"Planted_area_ha"*, on insère ensuite toutes les colonnes permettant l'identification (une ou plusieurs), ici nous rajoutons uniquement la clé *"Name_GPS_track"*. 
- La clé *"Name_GPS_track"* va comporter comme dans l'exemple précédent les clés *"table_name"* et *"field_name"* pour identifier la table et le nom du champ correspondants:

```json
{
	...,
	"Identifying_columns" : {
		"Planted_area_ha": {
			"Name_GPS_track": {
				"table_name" : "parcelwaves",
				"field_name" : "gpsfilename"
			}
		}
	}
}
```
### 3. "Joins":

Si les colonnes à mettre à jour et les colonnes pour identifier se situent dans la même table en base de données, il n'est pas nécessaire de remplir cette partie dans le fichier de configuration json. On la laisse vide car il n'y a aucune jointure à faire.

Dans le cas où il faut effectuer une jointure, le champ *Joins* se remplit de cette façon:

```json
{
	...,
	"Joins": {
		"Planted_area_ha": {
			"parcels" : {
				"primary_key" : "id",
				"foreign_keys" : {},
				"tables_to_join" : [ {
					"name": "parcelwaves",
					"join_type": "inner"
					}
				]
			},
			"parcelwaves" : {
				"primary_key" : "id",
				"foreign_keys" : {
					"parcels" : "parcelid"
				},
				"tables_to_join" : []
			}
		}
	},
	...
}
```

- On ajoute d'abord en clé le nom de la colonne à mettre à jour afin d'avoir une jointure adaptée pour chaque colonne contenant les nouvelles données, ici c'est la clé *"Planted_area_ha"*.
- Ensuite on ajoute dans cet objet les tables à joindre en tant que clé : ici *"parcels"* et *"parcelwaves"*
- Chaque table possède sa clé primaire correspondant au champ *"primary_key"*
- Toutes les clés étrangères permettant la jointure doivent être inscrites dans les champs *"foreign_keys"*, avec le nom de la table correspondante en clé et le nom de la clé en valeur.
- Enfin, il faut remplir le champ *"tables_to_join"* qui est une liste. Lorsqu'on veut joindre deux tables, il faut ajouter un objet dans un seul des champs *"tables_to_join"*. La table dans laquelle on va ajouter cet objet est la table qu'on va identifier par sa clé primaire. La table contenant la clé étrangère ne doit pas contenir ce même objet. Dans l'objet créé dans *"tables_to_join"*, nous avons le champ *"name"* qui correspond à la table dans laquelle on va chercher la clé étrangère. Et le champ *"join_type"* qui correspond au type de jointure qu'on veut effectuer (inner, left, right, etc.).

### 4. Enregistrement

Une fois le fichier de configuration .json terminé, il faut le sauvegarder et le déplacer dans le répertoire [./config_files](./config_files)

## Exécution du programme main.py

Lorsque le fichier excel et le fichier de configuration .json sont prêt, il faut effectuer une dernière configuration:

Dans le répertoire de travail, créer un fichier .env contenant le nom, l'utilisateur, le mot de passe, le host, le port et le schema de la BDD. Sous cette forme là :

```docker
DB_NAME=""
DB_USER=""
DB_PASSWORD=""
DB_HOST=""
DB_PORT=""
DB_SCHEMA=""
```
Puis, exécuter le fichier main.py. Le programme vous demandera quel fichier excel choisir dans le répertoire [./data_to_update](./data_to_update). Et ensuite quel fichier de configuration .json choisir dans le dossier [./config_files](./config_files)

Enfin le programme affiche une barre de progression et inscrit toutes les logs dans le répertoire [./logs](./logs)
