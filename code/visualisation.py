"""
visualisation.py
================
Classe Visualisation – génère tous les types de graphiques (14 types).
Association avec JeuDonnees (1 → 0..*).
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as grille
import seaborn as sns
from scipy import stats as stats_scipy


class Visualisation:
    """
    Génère des graphiques à partir d'un JeuDonnees.
    Association : une Visualisation est liée à un JeuDonnees.
    """

    def __init__(self, jeu_donnees, style: str = "seaborn-v0_8", palette: str = "deep"):
        self.jeu_donnees = jeu_donnees
        self.style: str = style
        self.palette: str = palette
        self._appliquer_style()

    def _appliquer_style(self):
        try:
            plt.style.use(self.style)
        except Exception:
            pass
        sns.set_palette(self.palette)
        plt.rcParams.update({
            "figure.dpi":        120,
            "figure.facecolor":  "white",
            "axes.facecolor":    "#f8f9fa",
            "axes.grid":         True,
            "grid.alpha":        0.3,
            "font.size":         11,
            "axes.titlesize":    13,
            "axes.titleweight":  "bold",
            "figure.autolayout": True,
        })

    def _preparer_figure(self, taille=(10, 6)) -> tuple:
        self._appliquer_style()
        fig, ax = plt.subplots(figsize=taille)
        return fig, ax

    def _sauvegarder(self, fig: plt.Figure, chemin: Optional[str]) -> Optional[str]:
        if chemin:
            os.makedirs(
                os.path.dirname(chemin) if os.path.dirname(chemin) else ".",
                exist_ok=True
            )
            fig.savefig(chemin, bbox_inches="tight", dpi=120)
        return chemin

    def _tableau(self) -> pd.DataFrame:
        return self.jeu_donnees.donnees

    # ── 1. Histogramme ───────────────────────────────────────────
    def histogramme(self, colonne: str, nb_classes: int = 30,
                    kde: bool = True, couleur: str = "#4C72B0",
                    chemin: Optional[str] = None) -> plt.Figure:
        fig, ax = self._preparer_figure()
        serie = self._tableau()[colonne].dropna()
        ax.hist(serie, bins=nb_classes, color=couleur, alpha=0.7,
                edgecolor="white", density=kde)
        if kde:
            x_min, x_max = serie.min(), serie.max()
            x = np.linspace(x_min, x_max, 300)
            densite = stats_scipy.gaussian_kde(serie)
            ax2 = ax.twinx()
            ax2.plot(x, densite(x), color="#c0392b", linewidth=2, label="KDE")
            ax2.set_ylabel("Densité", color="#c0392b")
            ax2.tick_params(axis="y", labelcolor="#c0392b")
        ax.set_title(f"Histogramme – {colonne}")
        ax.set_xlabel(colonne)
        ax.set_ylabel("Fréquence")
        self._sauvegarder(fig, chemin)
        return fig

    # ── 2. Boîtes à moustaches ───────────────────────────────────
    def boite_moustaches(self, colonnes: Optional[List[str]] = None,
                         grouper_par: Optional[str] = None,
                         chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        if colonnes is None:
            colonnes = list(tableau.select_dtypes(include="number").columns)[:8]
        fig, ax = self._preparer_figure(taille=(max(8, len(colonnes) * 1.5), 6))
        if grouper_par and grouper_par in tableau.columns:
            donnees_groupes = [
                tableau[tableau[grouper_par] == g][colonnes[0]].dropna().values
                for g in tableau[grouper_par].unique()
            ]
            etiquettes = list(tableau[grouper_par].unique())
            ax.boxplot(donnees_groupes, labels=etiquettes, patch_artist=True,
                       boxprops=dict(facecolor="#4C72B0", alpha=0.7))
            ax.set_title(f"Boîtes à moustaches – {colonnes[0]} par {grouper_par}")
        else:
            donnees = [tableau[col].dropna().values for col in colonnes]
            bp = ax.boxplot(donnees, labels=colonnes, patch_artist=True)
            couleurs = sns.color_palette(self.palette, len(colonnes))
            for boite, couleur in zip(bp["boxes"], couleurs):
                boite.set_facecolor(couleur)
                boite.set_alpha(0.7)
            ax.set_title("Boîtes à moustaches")
        ax.set_xlabel("Variable")
        ax.set_ylabel("Valeur")
        plt.xticks(rotation=30, ha="right")
        self._sauvegarder(fig, chemin)
        return fig

    # ── 3. Nuage de points ───────────────────────────────────────
    def nuage_points(self, col_x: str, col_y: str,
                     couleur_par: Optional[str] = None,
                     regression: bool = True,
                     chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        fig, ax = self._preparer_figure()
        kw_dispersion: Dict[str, Any] = {
            "alpha": 0.6, "edgecolors": "white", "linewidth": 0.5
        }
        if couleur_par:
            groupes = tableau[couleur_par].astype("category")
            for g in groupes.cat.categories:
                sous_ensemble = tableau[tableau[couleur_par] == g]
                ax.scatter(sous_ensemble[col_x], sous_ensemble[col_y],
                           label=str(g), **kw_dispersion)
            ax.legend(title=couleur_par, framealpha=0.7)
        else:
            ax.scatter(tableau[col_x], tableau[col_y],
                       color="#4C72B0", **kw_dispersion)
        if regression:
            valide = tableau[[col_x, col_y]].dropna()
            pente, ordonnee, r, p, _ = stats_scipy.linregress(
                valide[col_x], valide[col_y]
            )
            x_ligne = np.linspace(valide[col_x].min(), valide[col_x].max(), 100)
            ax.plot(x_ligne, pente * x_ligne + ordonnee,
                    color="#c0392b", linewidth=2,
                    label=f"Régression (R²={r**2:.2f})")
            ax.legend(framealpha=0.7)
        ax.set_title(f"Nuage de points – {col_x} vs {col_y}")
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)
        self._sauvegarder(fig, chemin)
        return fig

    # ── 4. Diagramme en barres ───────────────────────────────────
    def diagramme_barres(self, colonne: str, top: int = 15,
                         horizontal: bool = False,
                         chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        frequences = tableau[colonne].value_counts().head(top)
        taille = (10, max(4, len(frequences) * 0.5) if horizontal else (10, 5))
        fig, ax = self._preparer_figure(taille=taille)
        couleurs = sns.color_palette(self.palette, len(frequences))
        if horizontal:
            barres = ax.barh(frequences.index.astype(str),
                             frequences.values, color=couleurs)
            ax.set_xlabel("Fréquence")
            for barre, val in zip(barres, frequences.values):
                ax.text(val + 0.1,
                        barre.get_y() + barre.get_height() / 2,
                        f"{val}", va="center", fontsize=9)
        else:
            barres = ax.bar(frequences.index.astype(str),
                            frequences.values, color=couleurs)
            ax.set_ylabel("Fréquence")
            for barre, val in zip(barres, frequences.values):
                ax.text(barre.get_x() + barre.get_width() / 2,
                        val + 0.1,
                        f"{val}", ha="center", va="bottom", fontsize=9)
            plt.xticks(rotation=35, ha="right")
        ax.set_title(f"Distribution – {colonne}")
        self._sauvegarder(fig, chemin)
        return fig

    # ── 5. Camembert ─────────────────────────────────────────────
    def camembert(self, colonne: str, top: int = 8,
                  chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        frequences = tableau[colonne].value_counts().head(top)
        autres = tableau[colonne].value_counts().iloc[top:].sum()
        if autres > 0:
            frequences["Autres"] = autres
        fig, ax = self._preparer_figure(taille=(8, 8))
        couleurs = sns.color_palette(self.palette, len(frequences))
        coins, textes, auto_textes = ax.pie(
            frequences.values,
            labels=frequences.index.astype(str),
            autopct="%1.1f%%",
            colors=couleurs,
            startangle=140,
            pctdistance=0.8,
            wedgeprops=dict(edgecolor="white", linewidth=2),
        )
        for at in auto_textes:
            at.set_fontsize(9)
        ax.set_title(f"Répartition – {colonne}")
        self._sauvegarder(fig, chemin)
        return fig

    # ── 6. Carte de chaleur (corrélation) ────────────────────────
    def carte_chaleur(self, colonnes: Optional[List[str]] = None,
                      methode: str = "pearson",
                      chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        num = tableau.select_dtypes(include="number")
        if colonnes:
            num = num[colonnes]
        matrice_corr = num.corr(method=methode)
        nb_col = len(matrice_corr)
        fig, ax = self._preparer_figure(
            taille=(max(7, nb_col * 0.7), max(6, nb_col * 0.6))
        )
        sns.heatmap(
            matrice_corr, ax=ax, annot=True, fmt=".2f",
            cmap="coolwarm", center=0, vmin=-1, vmax=1,
            linewidths=0.5, linecolor="white",
            annot_kws={"size": 9},
        )
        ax.set_title(f"Carte de chaleur – corrélation ({methode})")
        plt.xticks(rotation=30, ha="right")
        self._sauvegarder(fig, chemin)
        return fig

    # ── 7. Violon ────────────────────────────────────────────────
    def violon(self, col_y: str, col_x: Optional[str] = None,
               chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        fig, ax = self._preparer_figure()
        if col_x:
            sns.violinplot(data=tableau, x=col_x, y=col_y, ax=ax,
                           palette=self.palette, inner="box", cut=0)
            plt.xticks(rotation=30, ha="right")
        else:
            sns.violinplot(data=tableau[[col_y]].dropna(), ax=ax,
                           palette=self.palette, inner="box", cut=0)
        ax.set_title(
            f"Violon – {col_y}" + (f" par {col_x}" if col_x else "")
        )
        self._sauvegarder(fig, chemin)
        return fig

    # ── 8. Densité KDE ───────────────────────────────────────────
    def densite_kde(self, colonnes: Optional[List[str]] = None,
                    remplir: bool = True,
                    chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        num = tableau.select_dtypes(include="number")
        if colonnes:
            num = num[colonnes]
        fig, ax = self._preparer_figure()
        for col in num.columns[:8]:
            serie = num[col].dropna()
            sns.kdeplot(serie, ax=ax, fill=remplir, alpha=0.4, label=col)
        ax.set_title("Densité de probabilité (KDE)")
        ax.legend(framealpha=0.7)
        self._sauvegarder(fig, chemin)
        return fig

    # ── 9. Matrice de dispersion (pairplot) ──────────────────────
    def matrice_dispersion(self, colonnes: Optional[List[str]] = None,
                           teinte: Optional[str] = None,
                           chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        cols_num = list(tableau.select_dtypes(include="number").columns)[:6]
        if colonnes:
            cols_num = [c for c in colonnes if c in tableau.columns][:6]
        tableau_graphe = tableau[cols_num + ([teinte] if teinte else [])].dropna()
        g = sns.pairplot(tableau_graphe, hue=teinte, diag_kind="kde",
                         plot_kws={"alpha": 0.5}, palette=self.palette)
        g.figure.suptitle("Matrice de dispersion", y=1.02,
                           fontweight="bold", fontsize=13)
        if chemin:
            g.figure.savefig(chemin, bbox_inches="tight", dpi=100)
        return g.figure

    # ── 10. Série temporelle ─────────────────────────────────────
    def serie_temporelle(self, colonne: str,
                         colonne_temps: Optional[str] = None,
                         chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau().copy()
        if colonne_temps:
            tableau[colonne_temps] = pd.to_datetime(tableau[colonne_temps])
            tableau = tableau.sort_values(colonne_temps)
            axe_x = tableau[colonne_temps]
        else:
            axe_x = range(len(tableau))
        fig, ax = self._preparer_figure(taille=(12, 5))
        ax.plot(axe_x, tableau[colonne], linewidth=1.5, color="#2980b9")
        ax.fill_between(axe_x, tableau[colonne], alpha=0.15, color="#2980b9")
        ax.set_title(f"Série temporelle – {colonne}")
        ax.set_xlabel(colonne_temps or "Indice")
        ax.set_ylabel(colonne)
        plt.xticks(rotation=30, ha="right")
        self._sauvegarder(fig, chemin)
        return fig

    # ── 11. Graphique Q-Q ────────────────────────────────────────
    def graphique_qq(self, colonne: str,
                     chemin: Optional[str] = None) -> plt.Figure:
        fig, ax = self._preparer_figure()
        serie = self._tableau()[colonne].dropna()
        stats_scipy.probplot(serie, dist="norm", plot=ax)
        ax.set_title(f"Graphique Q-Q – {colonne}")
        ax.get_lines()[0].set(markerfacecolor="#4C72B0", markersize=4, alpha=0.6)
        ax.get_lines()[1].set(color="#c0392b", linewidth=2)
        self._sauvegarder(fig, chemin)
        return fig

    # ── 12. Barres empilées ──────────────────────────────────────
    def barres_empilees(self, col_x: str, col_y: str,
                        chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau()
        tableau_croise = pd.crosstab(tableau[col_x], tableau[col_y],
                                     normalize="index") * 100
        fig, ax = self._preparer_figure(taille=(10, 6))
        tableau_croise.plot(
            kind="bar", stacked=True, ax=ax,
            colormap=self.palette if self.palette in plt.colormaps() else "Set2",
            edgecolor="white", linewidth=0.5
        )
        ax.set_title(f"Barres empilées – {col_y} par {col_x}")
        ax.set_ylabel("Pourcentage (%)")
        ax.legend(title=col_y, bbox_to_anchor=(1.05, 1),
                  loc="upper left", framealpha=0.7)
        plt.xticks(rotation=30, ha="right")
        self._sauvegarder(fig, chemin)
        return fig

    # ── 13. Graphique à bulles ───────────────────────────────────
    def graphique_bulles(self, col_x: str, col_y: str, col_taille: str,
                         col_couleur: Optional[str] = None,
                         chemin: Optional[str] = None) -> plt.Figure:
        tableau = self._tableau().dropna(subset=[col_x, col_y, col_taille])
        fig, ax = self._preparer_figure()
        tailles = (
            (tableau[col_taille] - tableau[col_taille].min()) /
            (tableau[col_taille].max() - tableau[col_taille].min() + 1e-9) * 500 + 20
        )
        sc = ax.scatter(
            tableau[col_x], tableau[col_y], s=tailles,
            c=tableau[col_couleur] if col_couleur else None,
            cmap="plasma", alpha=0.6, edgecolors="white"
        )
        if col_couleur:
            plt.colorbar(sc, ax=ax, label=col_couleur)
        ax.set_title(
            f"Graphique à bulles – {col_x} vs {col_y} (taille : {col_taille})"
        )
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)
        self._sauvegarder(fig, chemin)
        return fig

    # ── 14. Tableau de bord récapitulatif ────────────────────────
    def tableau_de_bord(self, chemin: Optional[str] = None) -> plt.Figure:
        """Génère un tableau de bord 2×3 avec les visualisations clés."""
        tableau = self._tableau()
        cols_num = list(tableau.select_dtypes(include="number").columns)[:6]
        cols_cat = list(tableau.select_dtypes(
            include=["object", "category"]).columns)

        fig = plt.figure(figsize=(18, 12))
        fig.suptitle(
            f"Tableau de bord – {self.jeu_donnees.nom}",
            fontsize=16, fontweight="bold"
        )
        gs = grille.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

        # 1. Histogramme de la 1re variable numérique
        if cols_num:
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.hist(tableau[cols_num[0]].dropna(), bins=25,
                     color="#4C72B0", alpha=0.8, edgecolor="white")
            ax1.set_title(f"Histogramme – {cols_num[0]}", fontsize=11)

        # 2. Boîtes à moustaches
        if len(cols_num) >= 2:
            ax2 = fig.add_subplot(gs[0, 1])
            donnees_boites = [tableau[col].dropna().values for col in cols_num[:5]]
            bp = ax2.boxplot(donnees_boites, labels=cols_num[:5], patch_artist=True)
            couleurs = sns.color_palette(self.palette, len(donnees_boites))
            for boite, coul in zip(bp["boxes"], couleurs):
                boite.set_facecolor(coul)
                boite.set_alpha(0.7)
            ax2.set_title("Boîtes à moustaches", fontsize=11)
            plt.setp(ax2.get_xticklabels(), rotation=20, ha="right")

        # 3. Carte de chaleur corrélation
        if len(cols_num) >= 2:
            ax3 = fig.add_subplot(gs[0, 2])
            matrice_corr = tableau[cols_num].corr()
            sns.heatmap(matrice_corr, ax=ax3, annot=True, fmt=".2f",
                        cmap="coolwarm", center=0, linewidths=0.5,
                        annot_kws={"size": 8})
            ax3.set_title("Corrélation", fontsize=11)

        # 4. Nuage de points (2 premières variables)
        if len(cols_num) >= 2:
            ax4 = fig.add_subplot(gs[1, 0])
            valide = tableau[[cols_num[0], cols_num[1]]].dropna()
            ax4.scatter(valide[cols_num[0]], valide[cols_num[1]],
                        alpha=0.5, color="#27ae60", edgecolors="white", s=30)
            ax4.set_xlabel(cols_num[0])
            ax4.set_ylabel(cols_num[1])
            ax4.set_title(f"Nuage – {cols_num[0]} vs {cols_num[1]}", fontsize=11)

        # 5. Camembert (1re variable catégorielle)
        if cols_cat:
            ax5 = fig.add_subplot(gs[1, 1])
            freq = tableau[cols_cat[0]].value_counts().head(6)
            couleurs = sns.color_palette(self.palette, len(freq))
            ax5.pie(freq.values, labels=freq.index.astype(str),
                    autopct="%1.1f%%", colors=couleurs,
                    startangle=140, wedgeprops={"edgecolor": "white"})
            ax5.set_title(f"Répartition – {cols_cat[0]}", fontsize=11)
        elif cols_num:
            ax5 = fig.add_subplot(gs[1, 1])
            sns.kdeplot(tableau[cols_num[-1]].dropna(), ax=ax5,
                        fill=True, color="#e74c3c", alpha=0.5)
            ax5.set_title(f"KDE – {cols_num[-1]}", fontsize=11)

        # 6. Barres de fréquence
        if cols_cat:
            ax6 = fig.add_subplot(gs[1, 2])
            freq = tableau[cols_cat[0]].value_counts().head(10)
            couleurs = sns.color_palette(self.palette, len(freq))
            ax6.barh(freq.index.astype(str), freq.values, color=couleurs)
            ax6.set_title(f"Fréquences – {cols_cat[0]}", fontsize=11)
        elif cols_num:
            ax6 = fig.add_subplot(gs[1, 2])
            stats_scipy.probplot(tableau[cols_num[0]].dropna(),
                                 dist="norm", plot=ax6)
            ax6.set_title(f"Q-Q plot – {cols_num[0]}", fontsize=11)

        self._sauvegarder(fig, chemin)
        return fig
