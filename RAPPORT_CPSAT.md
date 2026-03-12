# Rapport sur l'approche algorithmique CP-SAT

## 1. Vue d'ensemble du modèle

Le modèle résout un problème de placement en deux niveaux :

- niveau 1 : affecter chaque article a un tiroir, choisir sa variante, puis le placer en 2D dans ce tiroir ;
- niveau 2 : affecter chaque tiroir utilise a une armoire et le placer en hauteur.

Le solveur minimise principalement :

- le nombre d'armoires ;
- puis le nombre de tiroirs ;
- puis la dispersion des familles ;
- puis, selon les poids d'objectif, la compacite spatiale, la visibilite et la position basse des articles lourds.

Le modele est structure autour de trois familles de variables :

- affectation : `bin_of[i]`, `cabinet_of_bin[k]`, `variant_of[i]` ;
- geometrie : `x[i]`, `y[i]`, `Z_of_bin[k]`, `eff_w[i]`, `eff_d[i]`, `eff_h[i]` ;
- activation / agregation : `used_bin[k]`, `used_cabinet[c]`, `fam_in_bin[f,k]`, `occupied_height_of_bin[k]`.

En taille, le modele grossit vite :

- `is_in[i,k]` est en `O(nK)` ;
- le non-chevauchement 2D est en `O(n^2)` couples ;
- le placement vertical des tiroirs est en `O(K^2)` couples ;
- les spans de famille ajoutent `O(FK)` variables entieres.

Le point critique en temps est donc moins l'objectif que la combinatoire creee par les couples d'articles et de tiroirs.

## 2. Contraintes les plus utiles

### 2.1 Bornes superieures gloutonnes

Le calcul glouton de `max_bins` et `max_cabinets` est probablement la contrainte la plus rentable du modele, meme s'il est implemente avant la construction du CP. Il reduit directement :

- le nombre de slots tiroirs `K` ;
- le nombre de slots armoires ;
- toutes les familles de variables en `O(nK)`, `O(FK)` et `O(K^2)`.

Sans cette borne, le modele passerait rapidement d'un probleme difficile a un probleme beaucoup trop large.

### 2.2 Bris de symetrie sur les tiroirs

Les contraintes suivantes sont tres utiles :

- `bin_of[0] == 0` ;
- domaine triangulaire `bin_of[i] in [0..i]` ;
- prefixe contigu sur `used_bin[k]` ;
- `num_bins == sum(used_bin)`.

Elles suppriment les permutations inutiles de labels de tiroirs, qui sont une source majeure de symetrie dans les modeles de bin packing.

### 2.3 Contraintes de geometrie locale

Les contraintes :

- `x[i] + eff_w[i] <= W_of_bin[k]` ;
- `y[i] + eff_d[i] <= D_of_bin[k]` ;
- compatibilite hauteur `10 * eff_h[i] <= 13 * H_of_bin[k]`

sont essentielles. Elles filtrent tres tot les affectations impossibles entre article, variante et type de tiroir.

### 2.4 Non-chevauchement 2D par disjonction

La disjonction

- gauche / droite / dessous / dessus / pas dans le meme tiroir

est la contrainte centrale de faisabilite. Elle est couteuse, mais indispensable. C'est aussi l'une des principales sources de propagation, surtout quand les dimensions effectives sont deja bien liees aux variantes. 

### 2.5 Contraintes de charge et hauteur occupee

Les contraintes de poids par tiroir et le calcul exact de `occupied_height_of_bin[k]` sont importantes car elles connectent :

- les choix de variantes ;
- les choix de type de tiroir ;
- le placement vertical dans les armoires.

Le calcul exact de la hauteur occupee renforce nettement la phase "armoires".

### 2.6 Coupes globales sur les armoires

Les deux contraintes suivantes sont tres utiles meme si elles sont logiquement redondantes :

- somme des hauteurs occupees + interstices <= capacite totale des armoires ;
- borne inferieure sur `num_cabinets` a partir de `min_bin_height`.

Ce sont de bonnes coupes globales : elles propagent plus tot que le seul non-chevauchement vertical paire par paire.

### 2.7 Comptage des familles par tiroir

`fam_in_bin[f,k]` et `family_drawer_count[f]` sont utiles parce qu'ils rendent l'objectif "regrouper les familles" explicite. Sans ce comptage, CP-SAT aurait plus de mal a relier l'objectif a la structure des affectations.

## 3. Contraintes redondantes ou faibles

Il faut distinguer deux cas :

- redondante mais utile : logiquement impliquee, mais bonne pour la propagation ;
- redondante et peu rentable : ajoute surtout des variables/booleens sans gain clair.

### 3.1 Redondantes mais utiles

#### Contrainte d'aire par tiroir

La contrainte d'aire totale dans `add_area_constraints()` est redondante vis-a-vis de :

- l'inclusion dans le tiroir ;
- le non-chevauchement 2D.

Malgre cela, elle est utile comme coupe lineaire bon marche. Elle peut eliminer tres tot des affectations impossibles sans attendre que la disjonction geometrique se structure.

Conclusion : a conserver.

#### Coupes globales sur les armoires

Les inegalites globales sur `num_cabinets` sont elles aussi redondantes par rapport au placement vertical exact, mais elles valent le cout.

Conclusion : a conserver.

### 3.2 Redondantes et supprimables dans la formulation actuelle

#### `is_in[i,k] => fam_in_bin[f,k]`

Dans `add_family_constraints()`, chaque `fam_in_bin[f,k]` est ensuite defini par :

- `fam_in_bin[f,k] = max(is_in[i,k] pour les items de la famille f)`.

Du coup, les implications prealables `is_in[i,k] => fam_in_bin[f,k]` n'apportent quasiment rien : `add_max_equality()` impose deja cette relation.

Statut dans le code actuel :

- supprime.

Effet attendu :

- moins de contraintes booleennes ;
- meme semantics ;
- perte de propagation probablement tres faible.

#### `b => used_cabinet[c]` dans `add_cabinet_constraints()`

La variable `used_cabinet[c]` est ensuite fixee par `add_max_equality(used_cabinet[c], bins_in_c)`. L'implication individuelle depuis chaque `bin_in_cabinet[k,c]` devient donc redondante.

Statut dans le code actuel :

- supprime.

Effet attendu :

- leger allegement du modele ;
- pas de perte de force notable puisque le max equality fait deja le lien.

#### `cabinet_of_bin[k] != c` sous `[used_bin[k], b.Not()]`

Cette contrainte sert a dire : si le tiroir `k` est utilise et que le booleen `b` pour l'armoire `c` est faux, alors `cabinet_of_bin[k] != c`.

Mais comme le modele impose deja :

- `sum(bin_in_cabinet[k,*]) == used_bin[k]` ;
- `b => cabinet_of_bin[k] == c`,

on a deja une affectation exacte quand `used_bin[k] = 1`. Cette inegalite reifiee est donc en grande partie redondante.

Statut dans le code actuel :

- supprime.

La suppression est correcte car `sum(bin_in_cabinet[k,*]) == used_bin[k]` impose deja une selection unique, et toute variable `b` vraie fixe deja `cabinet_of_bin[k]`.

### 3.3 Contraintes faibles ou cheres pour un gain discutable

#### `add_spatial_span_constraints()`

Cette partie ajoute beaucoup de variables entieres (`xmin/xmax/ymin/ymax/xspan/yspan`) pour chaque couple famille-tiroir. Or `span_weight` vaut actuellement `0` dans `SolverConfig`.

Dans cet etat :

- le span n'influence pas l'objectif ;
- il ne semble pas renforcer des contraintes de faisabilite ;
- il ajoute pourtant une couche non negligeable de variables et de contraintes.

Conclusion : si `span_weight == 0`, il vaut mieux ne pas construire du tout ces variables. C'est probablement l'optimisation la plus simple a fort retour.

Statut dans le code actuel :

- implemente.

#### Calcul exact de `occupied_height_of_bin` via un `h_contrib[i,k]` par couple item-tiroir

La contrainte est utile, mais la formulation est lourde car elle cree un entier auxiliaire `h_contrib[i,k]` pour chaque couple admissible.

Si les temps deviennent critiques, c'est un bon endroit pour reformuler avec une structure plus compacte, par exemple en liant d'abord la hauteur max aux items du tiroir effectivement utilises, ou en exploitant davantage `used_bin[k]` et des bornes pre-calculees.

## 4. Bris de symetrie deja presents

Le modele contient deja de bons bris de symetrie :

- indexation canonique des tiroirs via `bin_of[i] <= i` ;
- tiroirs utilises en prefixe ;
- armoires utilisees en prefixe ;
- `cabinet_of_bin[k] <= k` ;
- variables de tiroirs inutilises fixees a une valeur canonique ;
- tri initial des articles par famille puis taille.

Ces choix sont sains. Ils evitent deja une partie importante des permutations triviales.

## 5. Symetries restantes a casser

### 5.1 Ordonner les tiroirs equivalents

Il reste une symetrie forte entre deux tiroirs utilises de meme type portant des contenus comparables. Le solveur peut encore explorer plusieurs permutations de labels pour des tiroirs structurellement identiques.

Bris recommande :

- pour `k < k+1`, imposer un ordre sur un resume du tiroir, par exemple `(cabinet_of_bin[k], Z_of_bin[k], bin_type[k]) <= lex (cabinet_of_bin[k+1], Z_of_bin[k+1], bin_type[k+1])` quand les deux tiroirs sont utilises.

Version plus simple :

- `cabinet_of_bin[k] <= cabinet_of_bin[k+1]` pour les tiroirs utilises ;
- et, a cabinet egal, `Z_of_bin[k] <= Z_of_bin[k+1]`.

Cela reduit les permutations entre tiroirs utilises.

### 5.2 Ordonner les tiroirs a l'interieur d'une meme armoire

Le non-chevauchement vertical autorise deux tiroirs identiques a etre inverses en hauteur sans changer la qualite de la solution.

Bris recommande :

- si deux tiroirs `k < m` sont dans la meme armoire et de meme type, imposer `Z_of_bin[k] <= Z_of_bin[m]`.

C'est souvent tres rentable car le sous-probleme vertical est sinon riche en permutations.

### 5.3 Ordonner les articles equivalents

Si plusieurs articles ont :

- meme famille ;
- meme poids ;
- memes variantes ;
- meme attribut `heavy`,

alors ils sont interchangeables. Le solveur peut donc permuter leurs `bin_of/x/y/variant_of`.

Bris recommande :

- pour des articles strictement equivalents consecutifs apres tri, imposer un ordre lexicographique sur `(bin_of, x, y, variant_of)`.

C'est un levier classique et souvent efficace sur les instances avec beaucoup de doublons.

### 5.4 Casser la symetrie des armoires identiques

Les armoires sont indiscernables a capacite egale. Le prefixe sur `used_cabinet` ne suffit pas a eliminer toutes les permutations de contenu.

Bris recommande :

- ordonner les armoires par charge totale, ou par plus petit index de tiroir assigne, ou par hauteur totale occupee.

Une version simple consiste a introduire un indicateur `first_bin_in_cabinet[c]` et imposer qu'il soit croissant avec `c`.

## 6. Recommandations concretes, par impact

### Priorite 1 : supprimer ce qui est construit pour rien

Statut :

- les trois points ci-dessous ont ete implementes dans la version actuelle du modele ;
- ils ont ete testes par benchmark.

1. Ne pas construire `xspan/yspan/xmin/xmax/ymin/ymax` quand `config.span_weight == 0`.
2. Supprimer les implications `is_in => fam_in_bin`.
3. Supprimer `b => used_cabinet[c]` et la contrainte reifiee `cabinet_of_bin[k] != c`.

Validation :

- ces changements sont corrects structurellement et ne modifient pas l'ensemble des solutions faisables ni l'objectif ;
- ils allegent surtout le nombre de variables et de contraintes reifiees ;
- leur impact sur les performances a ete verifie experimentalement par benchmark.

### Priorite 2 : renforcer les symetries sur les tiroirs et armoires

1. Renforcer les bris de symetrie uniquement entre tiroirs equivalents, sans imposer d'ordre global sur la hauteur `Z`.
2. Ajouter un bris de symetrie sur les tiroirs identiques ou de meme type.
3. Ordonner les armoires par un resume simple de leur contenu.

### Priorite 3 : traiter les articles equivalents

1. Detecter les articles identiques apres pre-processing.
2. Ajouter des contraintes d'ordre uniquement sur ces groupes.

Cette famille de bris peut donner un bon gain sans penaliser les instances heterogenes.

## 7. Strategie de benchmark recommandee

Pour savoir quoi garder, il faut mesurer sur plusieurs instances avec :

- temps total ;
- nombre de conflits ;
- nombre de branches ;
- premiere solution ;
- meilleur gap a 10 s, 30 s, 60 s.

Ordre conseille pour les essais a partir de la version actuelle :

1. nouvelle baseline apres priorites 1 ;
2. baseline + ordre des tiroirs dans chaque armoire ;
3. baseline + bris de symetrie sur articles equivalents ;
4. baseline + ordre partiel sur les tiroirs de meme type ;
5. combinaisons des meilleurs candidats.

Il faut evaluer chaque changement separement, car en CP-SAT une contrainte redondante peut soit accelerer, soit ralentir selon l'instance.

## 8. Conclusion

Le modele est globalement bien pose : il combine des contraintes locales fortes, des coupes globales utiles et deja quelques bons bris de symetrie. Les priorites 1 ont ete appliquees correctement, ce qui simplifie deja le modele sans changer sa logique. Les gains les plus probables a court terme sont maintenant :

- ajouter un ordre canonique plus fort sur les tiroirs et sur les articles equivalents.

Si l'objectif est d'ameliorer la rapidite sans changer la logique metier, c'est la direction la plus pragmatique.
