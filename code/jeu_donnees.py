"""
jeu_donnees.py
==============
Classe JeuDonnees – cœur du logiciel.
Gère le chargement, la description et le nettoyage des données.

Relations UML :
  Association 1 → 0..* avec Analyse
  Association 1 → 0..* avec Visualisation
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any


class JeuDonnees:
    """
    Représente un jeu de données chargé depuis un fichier ou un DataFrame.
    """

    FORMATS_SUPPORTES = {".csv", ".xlsx", ".xls", ".json", ".parquet", ".tsv"}

    def __init__(self, nom: str = "JeuDonnees"):
        # Attributs principaux (noms en français)
        self.nom: str = nom
        self.colonnes: List[str] = []
        self.types_colonnes: Dict[str, str] = {}
        self.donnees: Optional[pd.DataFrame] = None
        self._chemin_source: Optional[str] = None

    # ──────────────────────────────────────────────
    # Chargement
    # ──────────────────────────────────────────────

    def charger_fichier(self, chemin: str, **kwargs) -> None:
        """Charge un fichier CSV / Excel / JSON / Parquet / TSV."""
        if not os.path.exists(chemin):
            raise FileNotFoundError(f"Fichier introuvable : {chemin}")
        extension = os.path.splitext(chemin)[1].lower()
        if extension not in self.FORMATS_SUPPORTES:
            raise ValueError(f"Format non supporté : {extension}")

        self._chemin_source = chemin
        self.nom = os.path.basename(chemin)

        chargeurs = {
            ".csv":     lambda c, kw: pd.read_csv(c, **kw),
            ".tsv":     lambda c, kw: pd.read_csv(c, sep="\t", **kw),
            ".xlsx":    lambda c, kw: pd.read_excel(c, **kw),
            ".xls":     lambda c, kw: pd.read_excel(c, **kw),
            ".json":    lambda c, kw: pd.read_json(c, **kw),
            ".parquet": lambda c, kw: pd.read_parquet(c, **kw),
        }
        self.donnees = chargeurs[extension](chemin, kwargs)
        self._actualiser_metadonnees()

    def charger_dataframe(self, tableau: pd.DataFrame, nom: str = "Tableau") -> None:
        """Charge directement un DataFrame pandas."""
        self.donnees = tableau.copy()
        self.nom = nom
        self._actualiser_metadonnees()

    def charger_exemple(self, nom_exemple: str = "iris") -> None:
        """Charge un jeu de données d'exemple intégré."""
        exemples_disponibles = {
            "iris":    self._charger_iris,
            "titanic": self._charger_titanic,
            "pourboires": self._charger_pourboires,
        }
        if nom_exemple not in exemples_disponibles:
            raise ValueError(
                f"Exemple '{nom_exemple}' inconnu. "
                f"Choix disponibles : {list(exemples_disponibles)}"
            )
        exemples_disponibles[nom_exemple]()

    def _charger_iris(self):
        from sklearn.datasets import load_iris
        donnees_iris = load_iris()
        # Traduction des noms de colonnes en français
        noms_colonnes = [
            "longueur_sepal_cm",
            "largeur_sepal_cm",
            "longueur_petale_cm",
            "largeur_petale_cm",
        ]
        tableau = pd.DataFrame(donnees_iris.data, columns=noms_colonnes)
        tableau["espece"] = pd.Categorical.from_codes(
            donnees_iris.target, donnees_iris.target_names
        )
        self.charger_dataframe(tableau, "Iris")

    def _charger_titanic(self):
        np.random.seed(42)
        n = 200
        tableau = pd.DataFrame({
            "survie":        np.random.randint(0, 2, n),
            "classe":        np.random.choice([1, 2, 3], n),
            "age":           np.round(np.random.uniform(1, 80, n), 1),
            "tarif":         np.round(np.random.exponential(30, n), 2),
            "sexe":          np.random.choice(["homme", "femme"], n),
            "port_embarq":   np.random.choice(["Cherbourg", "Southampton", "Queenstown"], n),
        })
        self.charger_dataframe(tableau, "Titanic")

    def _charger_pourboires(self):
        np.random.seed(0)
        n = 244
        tableau = pd.DataFrame({
            "addition":      np.round(np.random.lognormal(2.9, 0.5, n), 2),
            "pourboire":     np.round(np.random.lognormal(1.3, 0.4, n), 2),
            "sexe":          np.random.choice(["Homme", "Femme"], n),
            "fumeur":        np.random.choice(["Oui", "Non"], n),
            "jour":          np.random.choice(["Jeudi", "Vendredi", "Samedi", "Dimanche"], n),
            "moment":        np.random.choice(["Déjeuner", "Dîner"], n),
            "nb_personnes":  np.random.randint(1, 7, n),
        })
        self.charger_dataframe(tableau, "Pourboires")

    def _actualiser_metadonnees(self) -> None:
        if self.donnees is not None:
            self.colonnes = list(self.donnees.columns)
            self.types_colonnes = {
                col: str(dtype)
                for col, dtype in self.donnees.dtypes.items()
            }

    # ──────────────────────────────────────────────
    # Description
    # ──────────────────────────────────────────────

    def apercu(self, nb_lignes: int = 5) -> pd.DataFrame:
        """Retourne les premières lignes du jeu de données."""
        self._verifier_chargement()
        return self.donnees.head(nb_lignes)

    def decrire(self) -> pd.DataFrame:
        """Statistiques descriptives de base."""
        self._verifier_chargement()
        return self.donnees.describe(include="all")

    def info(self) -> Dict[str, Any]:
        """Informations générales sur le jeu de données."""
        self._verifier_chargement()
        tableau = self.donnees
        return {
            "nom":                self.nom,
            "nb_lignes":          len(tableau),
            "nb_colonnes":        len(tableau.columns),
            "taille_mo":          round(tableau.memory_usage(deep=True).sum() / 1e6, 3),
            "valeurs_manquantes": int(tableau.isnull().sum().sum()),
            "doublons":           int(tableau.duplicated().sum()),
            "colonnes_num":       list(tableau.select_dtypes(include="number").columns),
            "colonnes_cat":       list(tableau.select_dtypes(
                                      include=["object", "category"]).columns),
        }

    def colonnes_numeriques(self) -> List[str]:
        """Retourne la liste des colonnes numériques."""
        self._verifier_chargement()
        return list(self.donnees.select_dtypes(include="number").columns)

    def colonnes_categorielles(self) -> List[str]:
        """Retourne la liste des colonnes catégorielles."""
        self._verifier_chargement()
        return list(self.donnees.select_dtypes(
            include=["object", "category"]).columns)

    # ──────────────────────────────────────────────
    # Nettoyage et transformation
    # ──────────────────────────────────────────────

    def nettoyer(
        self,
        supprimer_doublons: bool = True,
        strategie_na: str = "aucune",
        valeur_remplacement: Any = None,
    ) -> "JeuDonnees":
        """
        Retourne un nouveau JeuDonnees nettoyé.
        strategie_na : 'supprimer' | 'moyenne' | 'mediane' | 'mode' | 'valeur' | 'aucune'
        """
        self._verifier_chargement()
        tableau = self.donnees.copy()

        if supprimer_doublons:
            tableau = tableau.drop_duplicates()

        if strategie_na == "supprimer":
            tableau = tableau.dropna()
        elif strategie_na == "moyenne":
            cols_num = tableau.select_dtypes(include="number").columns
            tableau[cols_num] = tableau[cols_num].fillna(
                tableau[cols_num].mean()
            )
        elif strategie_na == "mediane":
            cols_num = tableau.select_dtypes(include="number").columns
            tableau[cols_num] = tableau[cols_num].fillna(
                tableau[cols_num].median()
            )
        elif strategie_na == "mode":
            tableau = tableau.fillna(tableau.mode().iloc[0])
        elif strategie_na == "valeur":
            tableau = tableau.fillna(valeur_remplacement)

        jd_propre = JeuDonnees(f"{self.nom}_nettoyé")
        jd_propre.charger_dataframe(tableau)
        return jd_propre

    def encoder_categories(self, methode: str = "etiquette") -> "JeuDonnees":
        """
        Encode les variables catégorielles.
        methode : 'etiquette' (label encoding) ou 'binaire' (one-hot encoding)
        """
        self._verifier_chargement()
        tableau = self.donnees.copy()
        cols_cat = self.colonnes_categorielles()

        if methode == "etiquette":
            from sklearn.preprocessing import LabelEncoder
            encodeur = LabelEncoder()
            for col in cols_cat:
                tableau[col] = encodeur.fit_transform(tableau[col].astype(str))
        elif methode == "binaire":
            tableau = pd.get_dummies(tableau, columns=cols_cat, drop_first=True)

        jd = JeuDonnees(f"{self.nom}_encodé")
        jd.charger_dataframe(tableau)
        return jd

    def normaliser(self, methode: str = "standard") -> "JeuDonnees":
        """
        Normalise les colonnes numériques.
        methode : 'standard' | 'minmax' | 'robuste'
        """
        self._verifier_chargement()
        tableau = self.donnees.copy()
        cols_num = self.colonnes_numeriques()

        if methode == "standard":
            from sklearn.preprocessing import StandardScaler
            tableau[cols_num] = StandardScaler().fit_transform(tableau[cols_num])
        elif methode == "minmax":
            from sklearn.preprocessing import MinMaxScaler
            tableau[cols_num] = MinMaxScaler().fit_transform(tableau[cols_num])
        elif methode == "robuste":
            from sklearn.preprocessing import RobustScaler
            tableau[cols_num] = RobustScaler().fit_transform(tableau[cols_num])

        jd = JeuDonnees(f"{self.nom}_normalisé")
        jd.charger_dataframe(tableau)
        return jd

    # ──────────────────────────────────────────────
    # Utilitaires internes
    # ──────────────────────────────────────────────

    def _verifier_chargement(self) -> None:
        if self.donnees is None:
            raise RuntimeError(
                "Aucune donnée chargée. "
                "Utilisez charger_fichier() ou charger_exemple() d'abord."
            )

    def __len__(self) -> int:
        return len(self.donnees) if self.donnees is not None else 0

    def __repr__(self) -> str:
        if self.donnees is None:
            return f"JeuDonnees('{self.nom}', vide)"
        return (
            f"JeuDonnees('{self.nom}', "
            f"{len(self.donnees)} lignes × {len(self.colonnes)} colonnes)"
        )
