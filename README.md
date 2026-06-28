# DataAnalyst Pro 
Logiciel d'analyse de données – Master 1 IFOAD – **entièrement en français**

## Structure du projet
```
data_analyzer/
├── code/
│   ├── main.py           ← Programme principal (interface graphique)
│   ├── jeu_donnees.py    ← Classe JeuDonnees  (chargement & nettoyage)
│   ├── analyse.py        ← Classes Analyse (abstraite), AnalyseDescriptive,
│   │                          AnalyseStatistique, AnalyseML
│   ├── visualisation.py  ← Classe Visualisation (14 types de graphiques)
│   └── rapport.py        ← Classe Rapport (export HTML)
├── data/                 ← Vos fichiers de données
├── exports/              ← Graphiques et rapports générés
└── requirements.txt
```

## Relations UML (POO)
| Relation       | Classes                                          | Cardinalité |
|----------------|--------------------------------------------------|-------------|
| Héritage       | Analyse → AnalyseDescriptive                     | 1:1         |
| Héritage       | Analyse → AnalyseStatistique                     | 1:1         |
| Héritage       | Analyse → AnalyseML                              | 1:1         |
| Association    | JeuDonnees → Analyse                             | 1 → 0..*   |
| Association    | JeuDonnees → Visualisation                       | 1 → 0..*   |
| Agrégation ◇  | Rapport → Analyse                                | 1 → 1..*   |
| Composition ◆ | Rapport → Visualisation                          | 1 → 1..*   |

## Installation
```bash
pip install -r requirements.txt
```

## Lancement
```bash
cd code
python main.py
```

## Fonctionnalités (entièrement en français)

###  Données
- Chargement : CSV, Excel, JSON, Parquet, TSV
- Exemples intégrés : Iris, Titanic, Pourboires (noms en français)
- Nettoyage : doublons, valeurs manquantes (plusieurs stratégies)
- Normalisation : standard, min-max, robuste
- Encodage catégoriel : étiquette / binaire (one-hot)

###  Analyses descriptives (11 analyses)
1. Statistiques de base (min, max, moyenne, écart-type, percentiles)
2. Asymétrie (skewness) & Aplatissement (kurtosis)
3. Valeurs manquantes et pourcentages
4. Fréquences des variables catégorielles
5. Matrice de corrélation (Pearson)
6. Quantiles personnalisables
7. Coefficient de variation
8. Détection valeurs aberrantes (Z-score)
9. Détection valeurs aberrantes (IQR)
10. Entropie des variables catégorielles
11. Comptage des doublons

###  Tests statistiques (13+ tests)
Paramétriques : Shapiro-Wilk, D'Agostino, KS, test t (1 et 2 éch.),
               ANOVA (F), Levene, Bartlett, Kendall
Non paramétriques : Wilcoxon, Mann-Whitney, Kruskal-Wallis, Friedman, Runs
Associatifs : Chi², Spearman

###  Machine Learning (6 méthodes)
1. ACP (Analyse en Composantes Principales) + chargements
2. K-Means (silhouette, Calinski-Harabasz, Davies-Bouldin)
3. Régression linéaire multiple + validation croisée
4. Régression Ridge / Lasso
5. Forêt aléatoire (importance des variables)
6. Détection d'anomalies (Isolation Forest, Z-score, IQR)
7. DBSCAN + Hiérarchique (depuis l'interface)

###  Graphiques (14 types)
1. Histogramme + KDE
2. Boîtes à moustaches
3. Nuage de points + droite de régression
4. Diagramme en barres
5. Camembert
6. Carte de chaleur (corrélation)
7. Violon
8. Densité KDE multi-colonnes
9. Matrice de dispersion (pairplot)
10. Série temporelle
11. Graphique Q-Q
12. Barres empilées (%)
13. Graphique à bulles
14. Tableau de bord récapitulatif 2×3

