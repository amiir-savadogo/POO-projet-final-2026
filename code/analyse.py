"""
analyse.py
==========
Hiérarchie d'analyses statistiques :

  Analyse (classe abstraite)
    ├── AnalyseDescriptive   – statistiques descriptives
    ├── AnalyseStatistique   – tests paramétriques & non paramétriques
    └── AnalyseML            – machine learning

Relations UML :
  Analyse  ← héritage ← AnalyseDescriptive / AnalyseStatistique / AnalyseML
  Analyse  → association → JeuDonnees  (self.jeu_donnees)
"""

from __future__ import annotations

import abc
import csv
import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats as stats_scipy


# ─────────────────────────────────────────────────────────────────────────────
#  CLASSE ABSTRAITE : Analyse
# ─────────────────────────────────────────────────────────────────────────────

class Analyse(abc.ABC):
    """
    Classe mère abstraite pour toutes les analyses.
    Association avec JeuDonnees (1 JeuDonnees → 0..* Analyse).
    """

    def __init__(self, jeu_donnees, nom: str = "Analyse"):
        self.jeu_donnees = jeu_donnees          # association avec JeuDonnees
        self.nom: str = nom
        self.resultats: Dict[str, Any] = {}
        self.date_execution: Optional[datetime.datetime] = None
        self._erreur: Optional[str] = None

    # ── Méthode abstraite (à implémenter dans chaque sous-classe) ────────────
    @abc.abstractmethod
    def executer(self, **kwargs) -> Dict[str, Any]:
        """Lance l'analyse et retourne un dictionnaire de résultats."""

    # ── Méthodes concrètes communes à toutes les analyses ───────────────────
    def rapport(self) -> str:
        """Retourne un rapport texte des résultats."""
        if not self.resultats:
            return (
                f"[{self.nom}] Aucun résultat disponible. "
                "Lancez d'abord l'analyse."
            )
        lignes = [
            f"{'═'*60}",
            f"  {self.nom.upper()}",
            f"{'═'*60}",
            f"  Exécuté le : {self.date_execution}",
            f"  Données    : {self.jeu_donnees.nom}",
            "",
        ]
        for cle, valeur in self.resultats.items():
            if isinstance(valeur, pd.DataFrame):
                lignes.append(f"── {cle} ──")
                lignes.append(valeur.to_string())
            elif isinstance(valeur, dict):
                lignes.append(f"── {cle} ──")
                for k, v in valeur.items():
                    lignes.append(f"  {k} : {self._formater(v)}")
            else:
                lignes.append(f"{cle} : {self._formater(valeur)}")
        return "\n".join(lignes)

    def exporter_csv(self, chemin: str) -> None:
        """Exporte les résultats tabulaires en CSV."""
        with open(chemin, "w", newline="", encoding="utf-8") as fichier:
            ecrivain = csv.writer(fichier)
            for cle, valeur in self.resultats.items():
                ecrivain.writerow([f"=== {cle} ==="])
                if isinstance(valeur, pd.DataFrame):
                    ecrivain.writerow(valeur.columns.tolist())
                    for ligne in valeur.itertuples(index=False):
                        ecrivain.writerow(list(ligne))
                elif isinstance(valeur, dict):
                    for k, v in valeur.items():
                        ecrivain.writerow([k, self._formater(v)])
                else:
                    ecrivain.writerow([cle, self._formater(valeur)])
                ecrivain.writerow([])

    def obtenir_resultats(self) -> Dict[str, Any]:
        """Retourne le dictionnaire de résultats."""
        return self.resultats

    # ── Utilitaires internes ─────────────────────────────────────────────────
    @staticmethod
    def _formater(valeur) -> str:
        if isinstance(valeur, float):
            return f"{valeur:.6g}"
        return str(valeur)

    def _demarrer_chrono(self):
        """Enregistre la date/heure de début d'exécution."""
        self.date_execution = datetime.datetime.now()


# ─────────────────────────────────────────────────────────────────────────────
#  SOUS-CLASSE 1 : AnalyseDescriptive
# ─────────────────────────────────────────────────────────────────────────────

class AnalyseDescriptive(Analyse):
    """
    Statistiques descriptives complètes (11 analyses).
    Hérite de Analyse.
    """

    def __init__(self, jeu_donnees):
        super().__init__(jeu_donnees, "Analyse Descriptive")
        self.percentiles: List[float] = [0.10, 0.25, 0.50, 0.75, 0.90]
        self.asymetrie: Optional[float] = None

    def executer(self, colonnes: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Lance toutes les analyses descriptives.
        colonnes : liste de colonnes à analyser (toutes si None)
        """
        self._demarrer_chrono()
        tableau = self.jeu_donnees.donnees
        if colonnes:
            tableau = tableau[colonnes]

        num = tableau.select_dtypes(include="number")
        cat = tableau.select_dtypes(include=["object", "category"])

        self.resultats = {}

        # 1. Statistiques de base
        self.resultats["statistiques_base"] = num.describe(
            percentiles=self.percentiles
        )

        # 2. Asymétrie et aplatissement
        if not num.empty:
            tableau_asym = pd.DataFrame({
                "Asymétrie (skewness)":     num.skew(),
                "Aplatissement (kurtosis)": num.kurtosis(),
            })
            self.resultats["asymetrie_aplatissement"] = tableau_asym
            self.asymetrie = float(num.skew().mean())

        # 3. Valeurs manquantes
        manquants = pd.DataFrame({
            "Valeurs manquantes": tableau.isnull().sum(),
            "Pourcentage (%)":    (tableau.isnull().mean() * 100).round(2),
        })
        self.resultats["valeurs_manquantes"] = manquants

        # 4. Fréquences des variables catégorielles
        frequences_dict = {}
        for col in cat.columns:
            frequences_dict[col] = tableau[col].value_counts().head(20)
        if frequences_dict:
            self.resultats["frequences_categories"] = frequences_dict

        # 5. Matrice de corrélation
        if len(num.columns) >= 2:
            self.resultats["matrice_correlation"] = num.corr()

        # 6. Quantiles personnalisés
        if not num.empty:
            self.resultats["quantiles"] = num.quantile(self.percentiles)

        # 7. Coefficient de variation
        if not num.empty:
            cv = (num.std() / num.mean().abs() * 100).rename("CV (%)")
            self.resultats["coefficient_variation"] = cv.to_frame()

        # 8. Détection outliers par Z-score
        if not num.empty:
            z = np.abs(stats_scipy.zscore(num.dropna()))
            nb_outliers = (z > 3).sum(axis=0)
            self.resultats["outliers_zscore"] = pd.DataFrame(
                {"Nb outliers (|z|>3)": nb_outliers}
            )

        # 9. Détection outliers par IQR
        if not num.empty:
            Q1, Q3 = num.quantile(0.25), num.quantile(0.75)
            ecart_interquartile = Q3 - Q1
            masque = (
                (num < (Q1 - 1.5 * ecart_interquartile)) |
                (num > (Q3 + 1.5 * ecart_interquartile))
            )
            self.resultats["outliers_iqr"] = pd.DataFrame(
                {"Nb outliers (IQR)": masque.sum()}
            )

        # 10. Entropie des variables catégorielles
        entropie_dict = {}
        for col in cat.columns:
            frequences = tableau[col].value_counts(normalize=True)
            entropie_dict[col] = float(stats_scipy.entropy(frequences))
        if entropie_dict:
            self.resultats["entropie_categories"] = pd.DataFrame.from_dict(
                entropie_dict, orient="index", columns=["Entropie (bits)"]
            )

        # 11. Doublons
        self.resultats["doublons"] = {
            "Total doublons":  int(tableau.duplicated().sum()),
            "Pourcentage (%)": round(tableau.duplicated().mean() * 100, 2),
        }

        return self.resultats

    def frequences(self, colonne: str, top: int = 10) -> pd.Series:
        """Fréquences d'une colonne catégorielle."""
        return self.jeu_donnees.donnees[colonne].value_counts().head(top)

    def correlation(self, methode: str = "pearson") -> pd.DataFrame:
        """Matrice de corrélation (pearson / spearman / kendall)."""
        num = self.jeu_donnees.donnees.select_dtypes(include="number")
        return num.corr(method=methode)


# ─────────────────────────────────────────────────────────────────────────────
#  SOUS-CLASSE 2 : AnalyseStatistique
# ─────────────────────────────────────────────────────────────────────────────

class AnalyseStatistique(Analyse):
    """
    Tests statistiques paramétriques et non paramétriques (16 tests).
    Hérite de Analyse.
    """

    def __init__(self, jeu_donnees):
        super().__init__(jeu_donnees, "Analyse Statistique")
        self.seuil: float = 0.05          # seuil de significativité α
        self.p_valeur: Optional[float] = None

    def executer(self, colonnes: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Lance tous les tests statistiques pertinents automatiquement."""
        self._demarrer_chrono()
        tableau = self.jeu_donnees.donnees
        num = tableau.select_dtypes(include="number")
        if colonnes:
            num = tableau[colonnes].select_dtypes(include="number")

        self.resultats = {}
        liste_colonnes = list(num.columns)

        # Tests de normalité
        self.resultats["test_normalite"] = self._tests_normalite(num)

        # Test t à 1 échantillon
        if liste_colonnes:
            self.resultats["test_t_1_echantillon"] = self._test_t_1ech(num)

        # Test t à 2 échantillons indépendants
        if len(liste_colonnes) >= 2:
            self.resultats["test_t_2_echantillons"] = self._test_t_2ech(
                num[liste_colonnes[0]], num[liste_colonnes[1]]
            )

        # Test de Wilcoxon
        if len(liste_colonnes) >= 2:
            self.resultats["test_wilcoxon"] = self._wilcoxon(
                num[liste_colonnes[0]], num[liste_colonnes[1]]
            )

        # Test de Mann-Whitney U
        if len(liste_colonnes) >= 2:
            self.resultats["test_mann_whitney"] = self._mann_whitney(
                num[liste_colonnes[0]], num[liste_colonnes[1]]
            )

        # ANOVA
        if len(liste_colonnes) >= 3:
            self.resultats["anova"] = self._anova(num)

        # Kruskal-Wallis
        if len(liste_colonnes) >= 3:
            self.resultats["kruskal_wallis"] = self._kruskal_wallis(num)

        # Test de Levene
        if len(liste_colonnes) >= 2:
            self.resultats["test_levene"] = self._levene(num)

        # Test de Bartlett
        if len(liste_colonnes) >= 2:
            self.resultats["test_bartlett"] = self._bartlett(num)

        # Chi² (variables catégorielles)
        cols_cat = list(tableau.select_dtypes(
            include=["object", "category"]).columns)
        if len(cols_cat) >= 2:
            self.resultats["test_chi2"] = self._chi2(
                tableau[cols_cat[0]], tableau[cols_cat[1]]
            )

        # Corrélation de Spearman
        if len(liste_colonnes) >= 2:
            self.resultats["correlation_spearman"] = self._correlation_spearman(num)

        # Corrélation de Kendall
        if len(liste_colonnes) >= 2:
            self.resultats["correlation_kendall"] = num.corr(method="kendall")

        # Test des runs (aléatoire)
        if liste_colonnes:
            self.resultats["test_runs"] = self._test_runs(num[liste_colonnes[0]])

        # Test de Friedman
        if len(liste_colonnes) >= 3:
            self.resultats["test_friedman"] = self._friedman(num)

        return self.resultats

    # ── Tests internes ───────────────────────────────────────────────────────

    def _tests_normalite(self, num: pd.DataFrame) -> pd.DataFrame:
        lignes = []
        for col in num.columns:
            serie = num[col].dropna()
            if len(serie) < 3:
                continue
            nb_obs = len(serie)

            # Shapiro-Wilk (max 5000 observations)
            if nb_obs <= 5000:
                stat_sw, p_sw = stats_scipy.shapiro(serie)
            else:
                stat_sw, p_sw = np.nan, np.nan

            # D'Agostino-Pearson
            if nb_obs >= 8:
                stat_dp, p_dp = stats_scipy.normaltest(serie)
            else:
                stat_dp, p_dp = np.nan, np.nan

            # Kolmogorov-Smirnov
            serie_std = (serie - serie.mean()) / (serie.std() + 1e-12)
            stat_ks, p_ks = stats_scipy.kstest(serie_std, "norm")

            lignes.append({
                "Colonne":        col,
                "n":              nb_obs,
                "Shapiro W":      round(stat_sw, 4) if not np.isnan(stat_sw) else "N/A",
                "Shapiro p":      round(p_sw, 4)    if not np.isnan(p_sw)    else "N/A",
                "D'Agostino p":   round(p_dp, 4)    if not np.isnan(p_dp)    else "N/A",
                "KS p":           round(p_ks, 4),
                "Distribution":   "Normale" if (p_sw if not np.isnan(p_sw) else 0) > self.seuil
                                  else "Non normale",
            })
        return pd.DataFrame(lignes)

    def _test_t_1ech(self, num: pd.DataFrame) -> pd.DataFrame:
        lignes = []
        for col in num.columns:
            serie = num[col].dropna()
            stat_t, p = stats_scipy.ttest_1samp(serie, 0)
            lignes.append({
                "Colonne":       col,
                "t":             round(stat_t, 4),
                "p-valeur":      round(p, 4),
                "Significatif":  "Oui" if p < self.seuil else "Non",
            })
        return pd.DataFrame(lignes)

    def _test_t_2ech(self, serie1: pd.Series, serie2: pd.Series) -> Dict:
        stat_t, p = stats_scipy.ttest_ind(serie1.dropna(), serie2.dropna())
        return {
            "t":            round(stat_t, 4),
            "p-valeur":     round(p, 4),
            "Significatif": p < self.seuil,
            "Colonnes":     f"{serie1.name} vs {serie2.name}",
        }

    def _wilcoxon(self, serie1: pd.Series, serie2: pd.Series) -> Dict:
        try:
            nb_min = min(len(serie1.dropna()), len(serie2.dropna()))
            stat_w, p = stats_scipy.wilcoxon(
                serie1.dropna().iloc[:nb_min].values,
                serie2.dropna().iloc[:nb_min].values
            )
            return {"W": round(stat_w, 4), "p-valeur": round(p, 4),
                    "Significatif": p < self.seuil}
        except Exception as erreur:
            return {"erreur": str(erreur)}

    def _mann_whitney(self, serie1: pd.Series, serie2: pd.Series) -> Dict:
        stat_u, p = stats_scipy.mannwhitneyu(
            serie1.dropna(), serie2.dropna(), alternative="two-sided"
        )
        return {"U": round(stat_u, 4), "p-valeur": round(p, 4),
                "Significatif": p < self.seuil}

    def _anova(self, num: pd.DataFrame) -> Dict:
        groupes = [num[col].dropna().values for col in num.columns]
        stat_f, p = stats_scipy.f_oneway(*groupes)
        return {"F": round(stat_f, 4), "p-valeur": round(p, 4),
                "Significatif": p < self.seuil}

    def _kruskal_wallis(self, num: pd.DataFrame) -> Dict:
        groupes = [num[col].dropna().values for col in num.columns]
        stat_h, p = stats_scipy.kruskal(*groupes)
        return {"H": round(stat_h, 4), "p-valeur": round(p, 4),
                "Significatif": p < self.seuil}

    def _levene(self, num: pd.DataFrame) -> Dict:
        groupes = [num[col].dropna().values for col in num.columns]
        stat_w, p = stats_scipy.levene(*groupes)
        return {"W": round(stat_w, 4), "p-valeur": round(p, 4),
                "Variances homogènes": p >= self.seuil}

    def _bartlett(self, num: pd.DataFrame) -> Dict:
        groupes = [num[col].dropna().values for col in num.columns]
        stat_t, p = stats_scipy.bartlett(*groupes)
        return {"T": round(stat_t, 4), "p-valeur": round(p, 4),
                "Variances homogènes": p >= self.seuil}

    def _chi2(self, serie1: pd.Series, serie2: pd.Series) -> Dict:
        tableau_contingence = pd.crosstab(serie1, serie2)
        chi2, p, ddl, _ = stats_scipy.chi2_contingency(tableau_contingence)
        return {"χ²": round(chi2, 4), "p-valeur": round(p, 4),
                "Degrés de liberté": ddl,
                "Significatif": p < self.seuil}

    def _correlation_spearman(self, num: pd.DataFrame) -> pd.DataFrame:
        corr, _ = stats_scipy.spearmanr(num.dropna())
        if isinstance(corr, float):
            corr = np.array([[1, corr], [corr, 1]])
        return pd.DataFrame(
            corr, index=num.columns, columns=num.columns
        ).round(4)

    def _test_runs(self, serie: pd.Series) -> Dict:
        try:
            serie_propre = serie.dropna()
            mediane = serie_propre.median()
            binaire = (serie_propre > mediane).astype(int).tolist()
            nb_runs = 1 + sum(
                1 for i in range(1, len(binaire))
                if binaire[i] != binaire[i - 1]
            )
            n1 = sum(binaire)
            n2 = len(binaire) - n1
            if n1 < 1 or n2 < 1:
                return {"erreur": "Données constantes"}
            mu = (2 * n1 * n2) / (n1 + n2) + 1
            variance = (
                2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)
            ) / ((n1 + n2) ** 2 * (n1 + n2 - 1))
            z = (nb_runs - mu) / (variance ** 0.5) if variance > 0 else 0
            p = 2 * (1 - stats_scipy.norm.cdf(abs(z)))
            return {
                "Nb runs": nb_runs,
                "z":        round(z, 4),
                "p-valeur": round(p, 4),
                "Aléatoire": p >= self.seuil,
            }
        except Exception as erreur:
            return {"erreur": str(erreur)}

    def _friedman(self, num: pd.DataFrame) -> Dict:
        try:
            groupes = [num[col].dropna().values for col in num.columns]
            stat_f, p = stats_scipy.friedmanchisquare(*groupes)
            return {"χ²": round(stat_f, 4), "p-valeur": round(p, 4),
                    "Significatif": p < self.seuil}
        except Exception as erreur:
            return {"erreur": str(erreur)}

    # ── API publique ─────────────────────────────────────────────────────────

    def tester_normalite(self, colonne: str) -> Dict:
        serie = self.jeu_donnees.donnees[colonne].dropna()
        stat_w, p = stats_scipy.shapiro(serie[:5000])
        self.p_valeur = float(p)
        return {
            "colonne":          colonne,
            "W":                round(stat_w, 4),
            "p-valeur":         round(p, 4),
            "Normale (α=5%)":   p > self.seuil,
        }

    def test_t(self, colonne1: str, colonne2: str) -> Dict:
        return self._test_t_2ech(
            self.jeu_donnees.donnees[colonne1],
            self.jeu_donnees.donnees[colonne2]
        )

    def anova(self, *colonnes: str) -> Dict:
        tableau = self.jeu_donnees.donnees
        groupes = [tableau[col].dropna().values for col in colonnes]
        stat_f, p = stats_scipy.f_oneway(*groupes)
        self.p_valeur = float(p)
        return {"F": round(stat_f, 4), "p-valeur": round(p, 4),
                "Significatif": p < self.seuil}

    def test_chi2(self, colonne1: str, colonne2: str) -> Dict:
        return self._chi2(
            self.jeu_donnees.donnees[colonne1],
            self.jeu_donnees.donnees[colonne2]
        )


# ─────────────────────────────────────────────────────────────────────────────
#  SOUS-CLASSE 3 : AnalyseML
# ─────────────────────────────────────────────────────────────────────────────

class AnalyseML(Analyse):
    """
    Analyses de machine learning : régression, clustering, PCA, etc. (9 méthodes).
    Hérite de Analyse.
    """

    def __init__(self, jeu_donnees):
        super().__init__(jeu_donnees, "Analyse Machine Learning")
        self.modele: Any = None
        self.metriques: Dict[str, float] = {}

    def executer(self, colonne_cible: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Lance toutes les analyses ML pertinentes."""
        self._demarrer_chrono()
        self.resultats = {}

        tableau = self.jeu_donnees.donnees.copy()
        num = tableau.select_dtypes(include="number").dropna()

        if len(num.columns) < 2:
            self.resultats["erreur"] = "Pas assez de colonnes numériques (minimum 2)."
            return self.resultats

        # 1. ACP (Analyse en Composantes Principales)
        self.resultats["acp"] = self._acp(num)

        # 2. K-Means (partitionnement)
        self.resultats["kmeans"] = self._kmeans(num)

        # 3. Régression linéaire
        if colonne_cible and colonne_cible in num.columns:
            self.resultats["regression_lineaire"] = self._regression_lineaire(
                num, colonne_cible
            )
        elif len(num.columns) >= 2:
            cible_auto = num.columns[-1]
            self.resultats["regression_lineaire"] = self._regression_lineaire(
                num, cible_auto
            )

        # 4. Régression Ridge et Lasso
        if colonne_cible and colonne_cible in num.columns:
            self.resultats["regression_ridge"] = self._regression_regularisee(
                num, colonne_cible, "ridge"
            )
            self.resultats["regression_lasso"] = self._regression_regularisee(
                num, colonne_cible, "lasso"
            )

        # 5. Forêt aléatoire (importance des variables)
        if colonne_cible and colonne_cible in num.columns:
            self.resultats["foret_aleatoire"] = self._foret_aleatoire(
                num, colonne_cible
            )

        # 6. Détection d'anomalies (Isolation Forest)
        self.resultats["anomalies_isolation"] = self._isolation_forest(num)

        # 7. DBSCAN (partitionnement par densité)
        self.resultats["dbscan"] = self._dbscan(num)

        # 8. Variance expliquée cumulée (ACP)
        self.resultats["variance_cumulee_acp"] = self._variance_cumulee(num)

        return self.resultats

    # ── Méthodes internes ML ─────────────────────────────────────────────────

    def _acp(self, num: pd.DataFrame) -> Dict:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        normaliseur = StandardScaler()
        X = normaliseur.fit_transform(num)
        nb_composantes = min(len(num.columns), len(num), 10)
        acp = PCA(n_components=nb_composantes)
        acp.fit(X)
        self.modele = acp
        return {
            "nb_composantes":        nb_composantes,
            "variance_expliquee":    [round(v, 4) for v in acp.explained_variance_ratio_],
            "variance_cumulee":      [round(v, 4) for v in acp.explained_variance_ratio_.cumsum()],
            "chargements":           pd.DataFrame(
                acp.components_,
                columns=num.columns,
                index=[f"CP{i+1}" for i in range(nb_composantes)]
            ).round(4),
        }

    def _kmeans(self, num: pd.DataFrame, nb_groupes: int = 3) -> Dict:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import (
            silhouette_score, calinski_harabasz_score, davies_bouldin_score
        )
        X = StandardScaler().fit_transform(num)
        km = KMeans(n_clusters=nb_groupes, random_state=42, n_init=10)
        etiquettes = km.fit_predict(X)
        return {
            "nb_groupes":        nb_groupes,
            "inertie":           round(km.inertia_, 4),
            "silhouette":        round(silhouette_score(X, etiquettes), 4),
            "calinski_harabasz": round(calinski_harabasz_score(X, etiquettes), 4),
            "davies_bouldin":    round(davies_bouldin_score(X, etiquettes), 4),
            "taille_groupes":    pd.Series(etiquettes).value_counts().sort_index().to_dict(),
        }

    def _regression_lineaire(self, num: pd.DataFrame, cible: str) -> Dict:
        from sklearn.linear_model import LinearRegression
        from sklearn.model_selection import cross_val_score
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        from sklearn.preprocessing import StandardScaler
        y = num[cible]
        X = num.drop(columns=[cible])
        X_norm = StandardScaler().fit_transform(X)
        modele = LinearRegression()
        modele.fit(X_norm, y)
        y_pred = modele.predict(X_norm)
        cv = cross_val_score(modele, X_norm, y, cv=min(5, len(y)), scoring="r2")
        self.modele = modele
        self.metriques["r2"] = round(r2_score(y, y_pred), 4)
        return {
            "variable_cible":   cible,
            "variables_pred":   list(X.columns),
            "R²":               round(r2_score(y, y_pred), 4),
            "R² validation":    round(cv.mean(), 4),
            "ECM":              round(mean_squared_error(y, y_pred), 4),
            "EAM":              round(mean_absolute_error(y, y_pred), 4),
            "RECM":             round(mean_squared_error(y, y_pred) ** 0.5, 4),
            "coefficients":     dict(zip(X.columns, modele.coef_.round(4))),
            "constante":        round(modele.intercept_, 4),
        }

    def _regression_regularisee(self, num: pd.DataFrame, cible: str, type_reg: str) -> Dict:
        from sklearn.linear_model import Ridge, Lasso
        from sklearn.metrics import r2_score, mean_squared_error
        from sklearn.preprocessing import StandardScaler
        y = num[cible]
        X = StandardScaler().fit_transform(num.drop(columns=[cible]))
        Modele = Ridge if type_reg == "ridge" else Lasso
        modele = Modele(alpha=1.0)
        modele.fit(X, y)
        y_pred = modele.predict(X)
        return {
            "type":     type_reg.upper(),
            "R²":       round(r2_score(y, y_pred), 4),
            "ECM":      round(mean_squared_error(y, y_pred), 4),
        }

    def _foret_aleatoire(self, num: pd.DataFrame, cible: str) -> Dict:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import r2_score
        y = num[cible]
        X = num.drop(columns=[cible])
        foret = RandomForestRegressor(n_estimators=100, random_state=42)
        foret.fit(X, y)
        importance = pd.Series(
            foret.feature_importances_, index=X.columns
        ).sort_values(ascending=False)
        return {
            "R² (entrainement)":    round(r2_score(y, foret.predict(X)), 4),
            "importance_variables": importance.round(4).to_dict(),
        }

    def _isolation_forest(self, num: pd.DataFrame) -> Dict:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        X = StandardScaler().fit_transform(num)
        iso = IsolationForest(contamination=0.05, random_state=42)
        etiquettes = iso.fit_predict(X)
        nb_anomalies = int((etiquettes == -1).sum())
        return {
            "nb_anomalies":     nb_anomalies,
            "taux_anomalies":   round(nb_anomalies / len(num) * 100, 2),
        }

    def _dbscan(self, num: pd.DataFrame) -> Dict:
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        X = StandardScaler().fit_transform(num)
        db = DBSCAN(eps=0.5, min_samples=5)
        etiquettes = db.fit_predict(X)
        nb_groupes = len(set(etiquettes)) - (1 if -1 in etiquettes else 0)
        nb_bruit = int((etiquettes == -1).sum())
        return {
            "nb_groupes": nb_groupes,
            "nb_bruit":   nb_bruit,
        }

    def _variance_cumulee(self, num: pd.DataFrame) -> Dict:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        X = StandardScaler().fit_transform(num)
        acp = PCA()
        acp.fit(X)
        cum = acp.explained_variance_ratio_.cumsum()
        n95 = int(np.argmax(cum >= 0.95)) + 1
        n99 = int(np.argmax(cum >= 0.99)) + 1
        return {
            "CP pour 95% variance": n95,
            "CP pour 99% variance": n99,
        }

    # ── API publique ─────────────────────────────────────────────────────────

    def acp(self, nb_composantes: int = 2) -> Dict:
        num = self.jeu_donnees.donnees.select_dtypes(include="number").dropna()
        return self._acp(num)

    def partitionnement(self, nb_groupes: int = 3) -> Dict:
        num = self.jeu_donnees.donnees.select_dtypes(include="number").dropna()
        return self._kmeans(num, nb_groupes)

    def regression(self, colonne_cible: str) -> Dict:
        num = self.jeu_donnees.donnees.select_dtypes(include="number").dropna()
        return self._regression_lineaire(num, colonne_cible)
