# Rapport sur l'approche CP-SAT

Date : 2026-03-12

## 1. Vue d'ensemble

Le modele traite deux niveaux de decision :

- niveau tiroir : choix de variante, affectation a un tiroir, placement 2D ;
- niveau armoire : affectation des tiroirs a des armoires, placement vertical.

Le point important de la version actuelle est qu'il existe maintenant deux formulations possibles pour les contraintes de non-chevauchement :

- formulation paire-a-paire ;
- formulation globale avec `AddNoOverlap2D` et `AddNoOverlap`.

Le choix est pilote par `SolverConfig.use_global_nooverlap`, qui vaut actuellement `True`.

## 2. Objectif actuel

| Terme | Role | Statut |
|---|---|---|
| `used_cabinet` | minimiser le nombre d'armoires | toujours actif |
| `used_bin` | minimiser le nombre de tiroirs | toujours actif |
| `family_drawer_count` | limiter la dispersion d'une famille sur plusieurs tiroirs | toujours actif |
| `xspan + yspan` | compacite intra-tiroir par famille | construit seulement si `span_weight != 0` |
| `visibility_deviation` | rapprocher certaines familles du niveau des yeux | actif si `visible_families` non vide |
| `heavy_z` | pousser les articles lourds vers le bas | actif si des items sont `heavy` |
| `family_cabinet_span` | limiter la dispersion d'une famille entre armoires | construit si poids non nul |
| `family_height_span` | limiter la dispersion verticale d'une famille | construit si poids non nul |

## 3. Deux formulations pour le non-chevauchement

### 3.1 Comparaison

| Zone | Formulation paire-a-paire | Formulation globale | Choix par defaut |
|---|---|---|---|
| Tiroirs (2D) | booleens `left/right/below` pour chaque paire d'items | `AddNoOverlap2D` avec intervalles optionnels par slot | globale |
| Armoires (Z) | booleens `same_cabinet`, `k_above_m`, `m_above_k` | `AddNoOverlap` avec intervalles optionnels par armoire | globale |

### 3.2 Lecture pratique

| Formulation | Avantages | Inconvenients |
|---|---|---|
| Paire-a-paire | explicite, facile a controler, bonne lecture des causes de conflit | beaucoup de booleens, croissance en `O(n^2)` pour les items et `O(K^2)` pour les tiroirs |
| Globale | exploite les propagateurs natifs d'OR-Tools, souvent meilleure echelle quand `K` grand | cree beaucoup d'intervalles optionnels, plus indirecte a analyser |

### 3.3 Recommandation

- garder les deux formulations est une bonne decision de modelisation ;
- il ne faut pas raisonner sur "le" non-chevauchement, mais sur deux variantes benchmarkables ;
- la formulation globale est coherente comme choix par defaut, surtout pour les grandes instances.

## 4. Contraintes les plus utiles

| Bloc | Pourquoi c'est utile |
|---|---|
| Bornes gloutonnes `max_bins`, `max_cabinets` | reduit directement la taille du modele avant construction |
| `bin_of[0] == 0` et domaine triangulaire `bin_of[i] <= i` | casse une grosse partie des symetries de labels de tiroirs |
| `used_bin` et `used_cabinet` en prefixe | evite les permutations inutiles de tiroirs et d'armoires |
| bornes de placement `x + w <= W`, `y + d <= D` | elimine tot les affectations impossibles |
| poids, hauteur, aire | bonnes coupes rapides avant que la geometrie complete ne se ferme |
| hauteur occupee exacte du tiroir | lie fort le niveau tiroir et le niveau armoire |
| coupes globales sur les armoires | propagent plus tot que le seul non-chevauchement vertical |
| `fam_in_bin` et `family_drawer_count` | rendent l'objectif de regroupement directement exploitable par CP-SAT |
| `family_cabinet_span` et `family_height_span` | ajoutent une vraie notion de proximite inter-tiroirs au niveau armoire |

## 5. Contraintes redondantes ou couteuses

### 5.1 Redondantes mais utiles

| Contrainte | Commentaire |
|---|---|
| aire totale par tiroir | redondante vis-a-vis du non-chevauchement, mais bonne coupe lineaire |
| coupes globales sur `num_cabinets` | redondantes vis-a-vis du placement vertical exact, mais utiles |


### 5.2 Points encore couteux

| Point | Commentaire |
|---|---|
| hauteur occupee avec un `h_contrib[i,k]` par couple admissible | formulation correcte, mais lourde |
| formulation globale du non-chevauchement | souvent meilleure en pratique, mais ajoute beaucoup d'intervalles |
| formulation paire-a-paire | plus interpretable, mais explose vite en booleens |

Le vrai sujet n'est donc plus "supprimer des contraintes manifestement fausses", mais choisir la meilleure forme de non-chevauchement selon les instances.

## 6. Symetries

### 6.1 Deja traitees

| Bris de symetrie | Statut |
|---|---|
| indexation canonique des tiroirs | present |
| prefixe des tiroirs utilises | present |
| prefixe des armoires utilisees | present |
| `cabinet_of_bin[k] <= k` | present |
| variables de tiroirs inutilises fixees | present |
| tri initial des items par famille et taille | present |

### 6.2 Ce qu'il faut faire avec prudence

Il ne faut pas imposer d'ordre global sur `Z_of_bin` pour tous les tiroirs, car `Z` intervient deja dans :

- la penalisation des articles lourds ;
- la proximite au niveau des yeux ;
- la proximite verticale des familles.

Un bris de symetrie trop fort sur `Z` pourrait donc supprimer de bonnes solutions.

### 6.3 Pistes raisonnables

| Idee | Risque |
|---|---|
| ordonner seulement des items strictement equivalents | faible |
| ordonner seulement des tiroirs vraiment equivalents dans une meme armoire | modere mais defensable |
| ordonner globalement tous les `Z_of_bin` | a eviter |

## 7. Conclusion

La version actuelle du modele est plus riche que la precedente sur deux points :

- elle offre deux formulations du non-chevauchement ;
- elle ajoute des termes d'objectif pour la proximite des familles entre armoires et en hauteur.

Les choix structurants les plus importants sont maintenant :

1. utiliser ou non la formulation globale de non-chevauchement selon les instances ;
2. conserver les coupes lineaires rapides qui aident la propagation ;
3. n'ajouter que des bris de symetrie qui ne perturbent pas les objectifs verticaux.

La lecture la plus juste du modele aujourd'hui est donc :

le coeur du probleme n'est plus seulement la combinatoire de placement, mais aussi le choix de la bonne formulation de non-chevauchement pour CP-SAT.
