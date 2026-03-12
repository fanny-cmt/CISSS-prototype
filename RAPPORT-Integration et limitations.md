# Rapport de comparaison
## Modele Python actuel vs document "Contraintes et besoin de donnees V2"

Date : 2026-03-12

## Hypothese importante

Ce rapport tient compte du fait qu'un pretraitement externe, non present dans ce repo, prepare les donnees avant le solveur. En particulier :

- les objets arrives au solveur sont deja agreges au bon niveau de decision ;
- les variantes ne sont pas seulement des rotations geometriques ;
- une variante peut deja embarquer le bon nombre d'objets, les marges minimales pour la prise en main, et d'autres regles metier amont.

Donc, quand le repo manipule une `variant` avec seulement `w/d/h`, il faut la lire comme un encombrement deja prepare, pas comme une simple orientation brute.

## Synthese courte

| Sujet | Etat | Lecture correcte |
|---|---|---|
| Minimiser le nombre d'armoires | Oui | Gere dans le solveur via `used_cabinet` |
| Mettre les objets lourds en bas | Oui | Gere dans le solveur via `heavy_z` |
| Rapprocher certains articles du niveau des yeux | Partiel | Gere au niveau `visible_families`, donc plutot famille que produit |
| Choix de variante / orientation | Oui | Gere dans le solveur, mais sur des variantes deja preparees en amont |
| Quantites / nombre d'objets dans un contenant | Amont | Porte par le pretraitement, pas par une variable explicite du solveur |
| Espacement minimal pour les mains | Amont | Porte en amont par les variantes |
| Placement 2D dans les tiroirs | Oui | Gere dans le solveur |
| Poids max par tiroir | Oui | Gere dans le solveur |
| Empilement vertical des tiroirs dans l'armoire | Oui | Gere dans le solveur |
| "Un produit sur un seul tiroir" | Amont | Chaque item du solveur est affecte a un seul tiroir |
| Armoires heterogenes & paniers/étagères| Non | Le solveur utilise une geometrie globale, pas un catalogue d'armoires differentes. Pour les paniers/étagères, on suppose qu'on a trois types de paniers, pas de modélisation des étagères |
| Sections / separateurs explicites | Non | Pas de positions explicites de separateurs ni de compartiments internes, mais peut être fait en post processing |
| Mode Kanban | Non | Non modele dans le solveur |
| Premier bac en angle | Non | Non modele dans le solveur |
| Obstacles locaux / barres transversales | Non | Non modeles dans le solveur |
| Objets hauts derrière | Non | Non mais peut être fait en post processing |
| Placement des tiroires sur z | Partiel | Dans le modèle, le panier peut être placé n'importe ou sur z |

## Ce que le modele couvre bien

| Bloc | Ce qui est effectivement fait |
|---|---|
| Affectation | chaque item est place dans un seul tiroir |
| Variantes | une variante est choisie par item |
| Geometrie tiroir | bornes 2D + non-chevauchement |
| Capacites | poids, surface, hauteur occupee |
| Armoires | affectation des tiroirs a des armoires + non-chevauchement vertical |
| Objectif | nombre d'armoires, nombre de tiroirs, regroupement par famille, lourds en bas, familles visibles proches du niveau des yeux |

## Points de discussion

- La modélisation des contraintes de non-chevauchement (dans les tiroirs et dans les armoires) peut être modélisée de deux manières différentes. Il faudra voir sur une instance plus grosse en terme de variables.
- Le regrouprement spatiale des objets de la même famille a été désactivé. Il coutait trop cher en performance et l'organisation internes des tiroires peut être revue en post processing.

## Conclusion

le solveur couvre bien le coeur combinatoire des armoires, mais une partie des contraintes metier au niveau des armoires/étagères et à l'intérieur des bacs ne sont pas prises en compte.