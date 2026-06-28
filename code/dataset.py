"""
Dataset – classe centrale du logiciel d'analyse de données.
Gère le chargement, la description et le nettoyage des données.
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any


class Dataset:
    """
    Représente un jeu de données chargé depuis un fichier ou un DataFrame.
    Association avec Analyse (1 → *) et Visualisation (1 → *).
    """

    FORMATS_SUPPORTES = {".csv", ".xlsx", ".xls", ".json", ".parquet", ".tsv"}

    def __init__(self, nom: str = "Dataset"):
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

        ext = os.path.splitext(chemin)[1].lower()
        if ext not in self.FORMATS_SUPPORTES:
            raise ValueError(f"Format non supporté : {ext}")

        self._chemin_source = chemin
        self.nom = os.path.basename(chemin)

        loaders = {
            ".csv":     lambda p, kw: pd.read_csv(p, **kw),
            ".tsv":     lambda p, kw: pd.read_csv(p, sep="\t", **kw),
            ".xlsx":    lambda p, kw: pd.read_excel(p, **kw),
            ".xls":     lambda p, kw: pd.read_excel(p, **kw),
            ".json":    lambda p, kw: pd.read_json(p, **kw),
            ".parquet": lambda p, kw: pd.read_parquet(p, **kw),
        }
        self.donnees = loaders[ext](chemin, kwargs)
        self._mettre_a_jour_meta()

    def charger_dataframe(self, df: pd.DataFrame, nom: str = "DataFrame") -> None:
        """Charge directement un DataFrame pandas."""
        self.donnees = df.copy()
        self.nom = nom
        self._mettre_a_jour_meta()

    def charger_exemple(self, nom_exemple: str = "iris") -> None:
        """Charge un jeu de données d'exemple intégré."""
        import io, urllib.request

        exemples = {
            "iris": self._iris_data,
            "titanic": self._titanic_data,
            "tips": self._tips_data,
        }
        if nom_exemple not in exemples:
            raise ValueError(f"Exemple '{nom_exemple}' inconnu. Choix : {list(exemples)}")
        exemples[nom_exemple]()

    def _iris_data(self):
        from sklearn.datasets import load_iris
        iris = load_iris()
        df = pd.DataFrame(iris.data, columns=iris.feature_names)
        df["species"] = pd.Categorical.from_codes(iris.target, iris.target_names)
        self.charger_dataframe(df, "Iris")

    def _titanic_data(self):
        url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=5) as r:
                import io
                self.charger_dataframe(pd.read_csv(io.StringIO(r.read().decode())), "Titanic")
        except Exception:
            # fallback minimal
            np.random.seed(42)
            n = 100
            df = pd.DataFrame({
                "Survived": np.random.randint(0, 2, n),
                "Pclass": np.random.choice([1, 2, 3], n),
                "Age": np.random.uniform(1, 80, n),
                "Fare": np.random.exponential(30, n),
                "Sex": np.random.choice(["male", "female"], n),
            })
            self.charger_dataframe(df, "Titanic (simulé)")

    def _tips_data(self):
        np.random.seed(0)
        n = 244
        df = pd.DataFrame({
            "total_bill": np.round(np.random.lognormal(2.9, 0.5, n), 2),
            "tip": np.round(np.random.lognormal(1.3, 0.4, n), 2),
            "sex": np.random.choice(["Male", "Female"], n),
            "smoker": np.random.choice(["Yes", "No"], n),
            "day": np.random.choice(["Thur", "Fri", "Sat", "Sun"], n),
            "time": np.random.choice(["Lunch", "Dinner"], n),
            "size": np.random.randint(1, 7, n),
        })
        self.charger_dataframe(df, "Tips")

    def _mettre_a_jour_meta(self) -> None:
        if self.donnees is not None:
            self.colonnes = list(self.donnees.columns)
            self.types_colonnes = {c: str(t) for c, t in self.donnees.dtypes.items()}

    # ──────────────────────────────────────────────
    # Description
    # ──────────────────────────────────────────────

    def apercu(self, n: int = 5) -> pd.DataFrame:
        self._verifier_charge()
        return self.donnees.head(n)

    def decrire(self) -> pd.DataFrame:
        self._verifier_charge()
        return self.donnees.describe(include="all")

    def info(self) -> Dict[str, Any]:
        self._verifier_charge()
        df = self.donnees
        return {
            "nom": self.nom,
            "lignes": len(df),
            "colonnes": len(df.columns),
            "taille_mo": df.memory_usage(deep=True).sum() / 1e6,
            "valeurs_manquantes": int(df.isnull().sum().sum()),
            "doublons": int(df.duplicated().sum()),
            "colonnes_num": list(df.select_dtypes(include="number").columns),
            "colonnes_cat": list(df.select_dtypes(include=["object", "category"]).columns),
        }

    def colonnes_numeriques(self) -> List[str]:
        self._verifier_charge()
        return list(self.donnees.select_dtypes(include="number").columns)

    def colonnes_categorielles(self) -> List[str]:
        self._verifier_charge()
        return list(self.donnees.select_dtypes(include=["object", "category"]).columns)

    # ──────────────────────────────────────────────
    # Nettoyage
    # ──────────────────────────────────────────────

    def nettoyer(
        self,
        supprimer_doublons: bool = True,
        strategie_na: str = "aucune",
        valeur_remplacement: Any = None,
    ) -> "Dataset":
        """
        Retourne un nouveau Dataset nettoyé.
        strategie_na: 'supprimer' | 'moyenne' | 'mediane' | 'mode' | 'valeur' | 'aucune'
        """
        self._verifier_charge()
        df = self.donnees.copy()

        if supprimer_doublons:
            df = df.drop_duplicates()

        if strategie_na == "supprimer":
            df = df.dropna()
        elif strategie_na == "moyenne":
            df = df.fillna(df.select_dtypes(include="number").mean())
        elif strategie_na == "mediane":
            df = df.fillna(df.select_dtypes(include="number").median())
        elif strategie_na == "mode":
            df = df.fillna(df.mode().iloc[0])
        elif strategie_na == "valeur":
            df = df.fillna(valeur_remplacement)

        ds_propre = Dataset(f"{self.nom}_nettoyé")
        ds_propre.charger_dataframe(df)
        return ds_propre

    def encoder_categories(self, methode: str = "label") -> "Dataset":
        """Encode les variables catégorielles (label ou one-hot)."""
        self._verifier_charge()
        df = self.donnees.copy()
        cat_cols = self.colonnes_categorielles()

        if methode == "label":
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            for col in cat_cols:
                df[col] = le.fit_transform(df[col].astype(str))
        elif methode == "onehot":
            df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

        ds = Dataset(f"{self.nom}_encodé")
        ds.charger_dataframe(df)
        return ds

    def normaliser(self, methode: str = "standard") -> "Dataset":
        """Normalise / standardise les colonnes numériques."""
        self._verifier_charge()
        df = self.donnees.copy()
        num_cols = self.colonnes_numeriques()

        if methode == "standard":
            from sklearn.preprocessing import StandardScaler
            df[num_cols] = StandardScaler().fit_transform(df[num_cols])
        elif methode == "minmax":
            from sklearn.preprocessing import MinMaxScaler
            df[num_cols] = MinMaxScaler().fit_transform(df[num_cols])
        elif methode == "robust":
            from sklearn.preprocessing import RobustScaler
            df[num_cols] = RobustScaler().fit_transform(df[num_cols])

        ds = Dataset(f"{self.nom}_normalisé")
        ds.charger_dataframe(df)
        return ds

    # ──────────────────────────────────────────────
    # Utilitaires
    # ──────────────────────────────────────────────

    def _verifier_charge(self) -> None:
        if self.donnees is None:
            raise RuntimeError("Aucune donnée chargée. Utilisez charger_fichier() d'abord.")

    def __len__(self) -> int:
        return len(self.donnees) if self.donnees is not None else 0

    def __repr__(self) -> str:
        if self.donnees is None:
            return f"Dataset('{self.nom}', vide)"
        return f"Dataset('{self.nom}', {len(self.donnees)} lignes × {len(self.colonnes)} colonnes)"
