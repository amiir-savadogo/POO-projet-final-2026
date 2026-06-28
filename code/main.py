"""
main.py – Interface graphique principale (style SPSS)
======================================================
Toutes les variables, commentaires et textes sont en français.
"""

import sys, os, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import numpy as np

# Ajoute le dossier du projet au chemin Python
_DOSSIER_BASE = os.path.dirname(os.path.abspath(__file__))
if _DOSSIER_BASE not in sys.path:
    sys.path.insert(0, _DOSSIER_BASE)

from jeu_donnees import JeuDonnees
from analyse import AnalyseDescriptive, AnalyseStatistique, AnalyseML
from visualisation import Visualisation
from rapport import Rapport

# ─────────────────────────────────────────────────────────────
# COULEURS ET POLICES
# ─────────────────────────────────────────────────────────────
COULEURS = {
    "fond":       "#F0F4F8",
    "barre_lat":  "#1A365D",
    "menu_titre": "#2B6CB0",
    "carte":      "#FFFFFF",
    "accent":     "#3182CE",
    "vert":       "#276749",
    "rouge":      "#C53030",
    "orange":     "#C05621",
    "texte":      "#2D3748",
    "discret":    "#718096",
    "bordure":    "#CBD5E0",
    "sortie_fond":"#0D1117",
    "sortie_txt": "#C9D1D9",
}
POL_NORMALE = ("Segoe UI", 10)
POL_GRAS    = ("Segoe UI", 10, "bold")
POL_PETITE  = ("Segoe UI", 9)
POL_TITRE   = ("Segoe UI", 13, "bold")
POL_CODE    = ("Consolas", 10)


def creer_bouton(parent, texte, commande, couleur=None, **kw):
    couleur = couleur or COULEURS["accent"]
    def _assombrir(c):
        h = c.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return "#{:02x}{:02x}{:02x}".format(int(r*.8), int(g*.8), int(b*.8))
    btn = tk.Button(
        parent, text=texte, command=commande,
        bg=couleur, fg="white", font=POL_GRAS,
        relief="flat", padx=12, pady=6,
        cursor="hand2", bd=0,
        activebackground=couleur, activeforeground="white", **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_assombrir(couleur)))
    btn.bind("<Leave>", lambda e: btn.config(bg=couleur))
    return btn


# ─────────────────────────────────────────────────────────────
# BOÎTES DE DIALOGUE STYLE SPSS
# ─────────────────────────────────────────────────────────────

class DialogueBase(tk.Toplevel):
    """
    Fenêtre modale de base.
    Corps scrollable + boutons OK/Annuler toujours visibles.
    """
    def __init__(self, parent, titre, largeur=520, hauteur=460):
        super().__init__(parent)
        self.title(titre)
        larg = min(largeur, self.winfo_screenwidth() - 40)
        haut = min(hauteur, self.winfo_screenheight() - 80)
        self.geometry(f"{larg}x{haut}")
        self.minsize(380, 300)
        self.configure(bg=COULEURS["fond"])
        self.resizable(True, True)
        self.grab_set()
        self.resultat = None

        # Titre fixe en haut
        tk.Label(self, text=titre, font=POL_TITRE,
                 bg=COULEURS["menu_titre"], fg="white",
                 anchor="w", padx=16, pady=10).pack(fill="x", side="top")

        # Boutons FIXES en bas
        cadre_boutons = tk.Frame(self, bg="#dce8f5", pady=8)
        cadre_boutons.pack(fill="x", side="bottom")
        self.bind("<Return>", lambda e: self._valider())
        self.bind("<Escape>", lambda e: self.destroy())
        creer_bouton(cadre_boutons, "✔  Confirmer", self._valider,
                     couleur=COULEURS["vert"]).pack(side="right", padx=12)
        creer_bouton(cadre_boutons, "✖  Annuler", self.destroy,
                     couleur=COULEURS["rouge"]).pack(side="right", padx=4)
        tk.Label(cadre_boutons,
                 text="Entrée = Confirmer  |  Échap = Annuler",
                 font=POL_PETITE, fg=COULEURS["discret"],
                 bg="#dce8f5").pack(side="left", padx=12)

        tk.Frame(self, bg=COULEURS["bordure"], height=1).pack(
            fill="x", side="bottom"
        )

        # Corps scrollable
        conteneur_scroll = tk.Frame(self, bg=COULEURS["fond"])
        conteneur_scroll.pack(fill="both", expand=True, side="top")

        barre_v = ttk.Scrollbar(conteneur_scroll, orient="vertical")
        barre_v.pack(side="right", fill="y")

        canvas_corps = tk.Canvas(conteneur_scroll, bg=COULEURS["fond"],
                                 highlightthickness=0,
                                 yscrollcommand=barre_v.set)
        canvas_corps.pack(side="left", fill="both", expand=True)
        barre_v.config(command=canvas_corps.yview)

        self.corps = tk.Frame(canvas_corps, bg=COULEURS["fond"])
        id_corps = canvas_corps.create_window((0, 0), window=self.corps, anchor="nw")

        def _ajuster_largeur(evt):
            canvas_corps.itemconfig(id_corps, width=evt.width)
        canvas_corps.bind("<Configure>", _ajuster_largeur)

        def _actualiser_scroll(evt=None):
            self.corps.update_idletasks()
            canvas_corps.configure(scrollregion=canvas_corps.bbox("all"))
        self.corps.bind("<Configure>", _actualiser_scroll)

        def _molette(evt):
            if evt.delta:
                canvas_corps.yview_scroll(int(-1 * evt.delta / 120), "units")
            elif evt.num == 4:
                canvas_corps.yview_scroll(-1, "units")
            elif evt.num == 5:
                canvas_corps.yview_scroll(1, "units")
        canvas_corps.bind("<MouseWheel>", _molette)
        self.corps.bind("<MouseWheel>", _molette)
        canvas_corps.bind("<Button-4>", _molette)
        canvas_corps.bind("<Button-5>", _molette)

        self._construire_corps()

    def _construire_corps(self): pass

    def _valider(self):
        self.resultat = self._collecter()
        if self.resultat is not None:
            self.destroy()

    def _collecter(self): return {}

    # ── Assistants de construction d'interface ────────────────────────
    def _etiquette(self, parent, texte, gras=False):
        tk.Label(parent, text=texte,
                 font=POL_GRAS if gras else POL_NORMALE,
                 bg=COULEURS["fond"], fg=COULEURS["texte"]
                 ).pack(anchor="w", pady=(6, 1), padx=16)

    def _liste_choix(self, parent, valeurs, hauteur=6, mode="single"):
        cadre = tk.Frame(parent, bg=COULEURS["fond"])
        cadre.pack(fill="x", pady=2, padx=16)
        barre = ttk.Scrollbar(cadre, orient="vertical")
        liste = tk.Listbox(cadre, height=hauteur, font=POL_NORMALE,
                           selectmode=mode, yscrollcommand=barre.set,
                           exportselection=False,
                           bg="white", relief="solid", bd=1)
        barre.config(command=liste.yview)
        for v in valeurs:
            liste.insert("end", v)
        barre.pack(side="right", fill="y")
        liste.pack(fill="x")
        return liste

    def _compteur(self, parent, minimum, maximum, valeur_ini, etiquette=""):
        ligne = tk.Frame(parent, bg=COULEURS["fond"])
        ligne.pack(anchor="w", pady=2, padx=16)
        if etiquette:
            tk.Label(ligne, text=etiquette, font=POL_NORMALE,
                     bg=COULEURS["fond"]).pack(side="left", padx=(0, 6))
        var = tk.DoubleVar(value=valeur_ini)
        ttk.Spinbox(ligne, from_=minimum, to=maximum,
                    increment=0.01, textvariable=var, width=8).pack(side="left")
        return var

    def _case_a_cocher(self, parent, texte, par_defaut=True):
        var = tk.BooleanVar(value=par_defaut)
        tk.Checkbutton(parent, text=texte, variable=var,
                       bg=COULEURS["fond"], font=POL_NORMALE
                       ).pack(anchor="w", pady=1, padx=16)
        return var

    def _groupe_boutons_radio(self, parent, etiquette, options, par_defaut=None):
        tk.Label(parent, text=etiquette, font=POL_GRAS,
                 bg=COULEURS["fond"]).pack(anchor="w", pady=(6, 1), padx=16)
        var = tk.StringVar(value=par_defaut or options[0][1])
        for texte, valeur in options:
            tk.Radiobutton(parent, text=texte, variable=var, value=valeur,
                           bg=COULEURS["fond"], font=POL_NORMALE
                           ).pack(anchor="w", padx=28)
        return var


# ═══════════════════════════════════════════════════════════════
# DIALOGUES SPÉCIFIQUES
# ═══════════════════════════════════════════════════════════════

class DlgFrequences(DialogueBase):
    def __init__(self, parent, cols_cat, cols_num):
        self.cols_cat = cols_cat
        self.cols_num = cols_num
        super().__init__(parent, "Fréquences", 460, 360)

    def _construire_corps(self):
        self._etiquette(self.corps, "Variable à analyser :", gras=True)
        self.liste = self._liste_choix(
            self.corps, self.cols_cat + self.cols_num, hauteur=8
        )
        if self.cols_cat + self.cols_num:
            self.liste.selection_set(0)
        self._etiquette(self.corps, "Nombre de valeurs à afficher (top N) :")
        self.var_top = tk.IntVar(value=10)
        ttk.Spinbox(self.corps, from_=1, to=100,
                    textvariable=self.var_top, width=6).pack(anchor="w", padx=16)

    def _collecter(self):
        sel = self.liste.curselection()
        if not sel:
            messagebox.showwarning("Sélection requise",
                                   "Veuillez choisir une variable.", parent=self)
            return None
        toutes = self.cols_cat + self.cols_num
        return {"colonne": toutes[sel[0]], "top": self.var_top.get()}


class DlgStatistiquesDesc(DialogueBase):
    def __init__(self, parent, cols_num):
        self.cols_num = cols_num
        super().__init__(parent, "Statistiques descriptives", 500, 480)

    def _construire_corps(self):
        self._etiquette(self.corps,
                        "Variables numériques (sélection multiple) :", gras=True)
        self.liste = self._liste_choix(
            self.corps, self.cols_num, hauteur=6, mode="multiple"
        )
        for i in range(len(self.cols_num)):
            self.liste.selection_set(i)
        self._etiquette(self.corps, "Statistiques à calculer :", gras=True)
        self.chk_base      = self._case_a_cocher(
            self.corps, "Moyenne, Écart-type, Min, Max, Percentiles")
        self.chk_asym      = self._case_a_cocher(
            self.corps, "Asymétrie (Skewness) & Aplatissement (Kurtosis)")
        self.chk_manquants = self._case_a_cocher(
            self.corps, "Valeurs manquantes")
        self.chk_cv        = self._case_a_cocher(
            self.corps, "Coefficient de variation")
        self.chk_outliers  = self._case_a_cocher(
            self.corps, "Détection des valeurs aberrantes (Z-score & IQR)")

    def _collecter(self):
        sel = self.liste.curselection()
        colonnes = [self.cols_num[i] for i in sel] if sel else self.cols_num
        return {
            "colonnes":   colonnes,
            "base":       self.chk_base.get(),
            "asymetrie":  self.chk_asym.get(),
            "manquants":  self.chk_manquants.get(),
            "cv":         self.chk_cv.get(),
            "aberrantes": self.chk_outliers.get(),
        }


class DlgCorrelation(DialogueBase):
    def __init__(self, parent, cols_num):
        self.cols_num = cols_num
        super().__init__(parent, "Corrélations", 480, 380)

    def _construire_corps(self):
        self._etiquette(self.corps,
                        "Variables (sélection multiple) :", gras=True)
        self.liste = self._liste_choix(
            self.corps, self.cols_num, hauteur=7, mode="multiple"
        )
        for i in range(len(self.cols_num)):
            self.liste.selection_set(i)
        self.methode = self._groupe_boutons_radio(
            self.corps, "Méthode :",
            [("Pearson",  "pearson"),
             ("Spearman", "spearman"),
             ("Kendall",  "kendall")]
        )

    def _collecter(self):
        sel = self.liste.curselection()
        colonnes = [self.cols_num[i] for i in sel] if sel else self.cols_num
        if len(colonnes) < 2:
            messagebox.showwarning("Sélection insuffisante",
                                   "Sélectionnez au moins 2 variables.",
                                   parent=self)
            return None
        return {"colonnes": colonnes, "methode": self.methode.get()}


class DlgBivariee(DialogueBase):
    def __init__(self, parent, cols_num, cols_cat):
        self.cols_num = cols_num
        self.cols_cat = cols_cat
        super().__init__(parent, "Analyse bivariée", 540, 460)

    def _construire_corps(self):
        ligne = tk.Frame(self.corps, bg=COULEURS["fond"])
        ligne.pack(fill="x")
        c1 = tk.Frame(ligne, bg=COULEURS["fond"])
        c1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._etiquette(c1, "Variable X :")
        self.liste_x = self._liste_choix(
            c1, self.cols_num + self.cols_cat, hauteur=8
        )
        if self.cols_num:
            self.liste_x.selection_set(0)
        c2 = tk.Frame(ligne, bg=COULEURS["fond"])
        c2.pack(side="left", fill="both", expand=True)
        self._etiquette(c2, "Variable Y :")
        self.liste_y = self._liste_choix(
            c2, self.cols_num + self.cols_cat, hauteur=8
        )
        if len(self.cols_num) > 1:
            self.liste_y.selection_set(1)
        self.type_analyse = self._groupe_boutons_radio(
            self.corps, "Type d'analyse bivariée :",
            [
                ("Corrélation (X num, Y num)",               "correlation"),
                ("Test t indépendant (X catég. 2 grp, Y num)","test_t"),
                ("ANOVA (X catégorielle, Y numérique)",       "anova"),
                ("Chi² d'indépendance (X catég., Y catég.)", "chi2"),
                ("Tableau croisé (X catég., Y catég.)",      "tableau_croise"),
            ]
        )

    def _collecter(self):
        toutes = self.cols_num + self.cols_cat
        sx = self.liste_x.curselection()
        sy = self.liste_y.curselection()
        if not sx or not sy:
            messagebox.showwarning("Sélection requise",
                                   "Sélectionnez X et Y.", parent=self)
            return None
        return {
            "col_x": toutes[sx[0]],
            "col_y": toutes[sy[0]],
            "type":  self.type_analyse.get(),
        }


class DlgNormalite(DialogueBase):
    def __init__(self, parent, cols_num):
        self.cols_num = cols_num
        super().__init__(parent, "Test de normalité", 440, 360)

    def _construire_corps(self):
        self._etiquette(self.corps,
                        "Variables (sélection multiple) :", gras=True)
        self.liste = self._liste_choix(
            self.corps, self.cols_num, hauteur=7, mode="multiple"
        )
        for i in range(len(self.cols_num)):
            self.liste.selection_set(i)
        self.chk_sw = self._case_a_cocher(self.corps, "Shapiro-Wilk")
        self.chk_ks = self._case_a_cocher(self.corps, "Kolmogorov-Smirnov")
        self.chk_dp = self._case_a_cocher(self.corps, "D'Agostino-Pearson")
        self.var_seuil = self._compteur(
            self.corps, 0.001, 0.2, 0.05, "Seuil de signification α :"
        )

    def _collecter(self):
        sel = self.liste.curselection()
        colonnes = [self.cols_num[i] for i in sel] if sel else self.cols_num
        return {
            "colonnes": colonnes,
            "shapiro":  self.chk_sw.get(),
            "ks":       self.chk_ks.get(),
            "dagostino":self.chk_dp.get(),
            "seuil":    self.var_seuil.get(),
        }


class DlgTestT(DialogueBase):
    def __init__(self, parent, cols_num, cols_cat):
        self.cols_num = cols_num
        self.cols_cat = cols_cat
        super().__init__(parent, "Test t de Student / Wilcoxon", 480, 400)

    def _construire_corps(self):
        self.type_test = self._groupe_boutons_radio(
            self.corps, "Type de test :",
            [("1 échantillon (vs μ₀)",          "1_echantillon"),
             ("2 échantillons indépendants",      "2_echantillons"),
             ("Wilcoxon (non paramétrique)",      "wilcoxon")]
        )
        self._etiquette(self.corps, "Variable numérique :", gras=True)
        self.liste_num = self._liste_choix(self.corps, self.cols_num, hauteur=4)
        if self.cols_num:
            self.liste_num.selection_set(0)
        self._etiquette(self.corps, "Variable de groupes (catégorielle) :")
        self.liste_cat = self._liste_choix(self.corps, self.cols_cat, hauteur=3)
        if self.cols_cat:
            self.liste_cat.selection_set(0)
        self.var_mu0   = self._compteur(self.corps, -1e9, 1e9, 0, "μ₀ (1 éch.) :")
        self.var_seuil = self._compteur(self.corps, 0.001, 0.2, 0.05, "Seuil α :")

    def _collecter(self):
        sn = self.liste_num.curselection()
        if not sn:
            messagebox.showwarning("Sélection requise",
                                   "Choisissez une variable numérique.",
                                   parent=self)
            return None
        sc = self.liste_cat.curselection()
        return {
            "type":     self.type_test.get(),
            "col_num":  self.cols_num[sn[0]],
            "col_cat":  self.cols_cat[sc[0]] if sc else None,
            "mu0":      self.var_mu0.get(),
            "seuil":    self.var_seuil.get(),
        }


class DlgAnova(DialogueBase):
    def __init__(self, parent, cols_num, cols_cat):
        self.cols_num = cols_num
        self.cols_cat = cols_cat
        super().__init__(parent, "ANOVA / Kruskal-Wallis", 480, 360)

    def _construire_corps(self):
        self.type_test = self._groupe_boutons_radio(
            self.corps, "Test :",
            [("ANOVA paramétrique (F)",          "anova"),
             ("Kruskal-Wallis (non paramétrique)","kruskal")]
        )
        self._etiquette(self.corps, "Variable dépendante (numérique) :", gras=True)
        self.liste_dep = self._liste_choix(self.corps, self.cols_num, hauteur=3)
        if self.cols_num:
            self.liste_dep.selection_set(0)
        self._etiquette(self.corps, "Facteur (variable catégorielle) :", gras=True)
        self.liste_fac = self._liste_choix(self.corps, self.cols_cat, hauteur=3)
        if self.cols_cat:
            self.liste_fac.selection_set(0)
        self.var_seuil = self._compteur(self.corps, 0.001, 0.2, 0.05, "Seuil α :")

    def _collecter(self):
        sd = self.liste_dep.curselection()
        sf = self.liste_fac.curselection()
        if not sd:
            messagebox.showwarning("Sélection requise",
                                   "Choisissez la variable dépendante.",
                                   parent=self)
            return None
        return {
            "type":    self.type_test.get(),
            "col_dep": self.cols_num[sd[0]],
            "col_fac": self.cols_cat[sf[0]] if sf else None,
            "seuil":   self.var_seuil.get(),
        }


class DlgChi2(DialogueBase):
    def __init__(self, parent, cols_cat):
        self.cols_cat = cols_cat
        super().__init__(parent, "Test Chi² d'indépendance", 480, 320)

    def _construire_corps(self):
        ligne = tk.Frame(self.corps, bg=COULEURS["fond"])
        ligne.pack(fill="x")
        c1 = tk.Frame(ligne, bg=COULEURS["fond"])
        c1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._etiquette(c1, "Variable 1 :")
        self.liste1 = self._liste_choix(c1, self.cols_cat, hauteur=6)
        if self.cols_cat:
            self.liste1.selection_set(0)
        c2 = tk.Frame(ligne, bg=COULEURS["fond"])
        c2.pack(side="left", fill="both", expand=True)
        self._etiquette(c2, "Variable 2 :")
        self.liste2 = self._liste_choix(c2, self.cols_cat, hauteur=6)
        if len(self.cols_cat) > 1:
            self.liste2.selection_set(1)
        self.var_seuil = self._compteur(
            self.corps, 0.001, 0.2, 0.05, "Seuil α :"
        )

    def _collecter(self):
        s1 = self.liste1.curselection()
        s2 = self.liste2.curselection()
        if not s1 or not s2:
            messagebox.showwarning("Sélection requise",
                                   "Choisissez les 2 variables.", parent=self)
            return None
        return {
            "col1":  self.cols_cat[s1[0]],
            "col2":  self.cols_cat[s2[0]],
            "seuil": self.var_seuil.get(),
        }


class DlgACP(DialogueBase):
    def __init__(self, parent, cols_num):
        self.cols_num = cols_num
        super().__init__(parent, "Analyse en Composantes Principales (ACP)", 500, 380)

    def _construire_corps(self):
        self._etiquette(self.corps,
                        "Variables (sélection multiple) :", gras=True)
        self.liste = self._liste_choix(
            self.corps, self.cols_num, hauteur=7, mode="multiple"
        )
        for i in range(len(self.cols_num)):
            self.liste.selection_set(i)
        self._etiquette(self.corps, "Nombre de composantes à extraire :")
        self.var_nb_comp = tk.IntVar(value=min(3, len(self.cols_num)))
        ttk.Spinbox(self.corps, from_=1, to=len(self.cols_num),
                    textvariable=self.var_nb_comp,
                    width=6).pack(anchor="w", padx=16)
        self.chk_std = self._case_a_cocher(
            self.corps, "Standardiser les variables au préalable", True
        )

    def _collecter(self):
        sel = self.liste.curselection()
        colonnes = [self.cols_num[i] for i in sel] if sel else self.cols_num
        if len(colonnes) < 2:
            messagebox.showwarning("Sélection insuffisante",
                                   "Sélectionnez au moins 2 variables.",
                                   parent=self)
            return None
        return {
            "colonnes":     colonnes,
            "nb_composantes": self.var_nb_comp.get(),
            "standardiser": self.chk_std.get(),
        }


class DlgPartitionnement(DialogueBase):
    def __init__(self, parent, cols_num):
        self.cols_num = cols_num
        super().__init__(parent, "Partitionnement (Clustering)", 500, 440)

    def _construire_corps(self):
        self.algorithme = self._groupe_boutons_radio(
            self.corps, "Algorithme :",
            [("K-Means",                       "kmeans"),
             ("DBSCAN (densité)",               "dbscan"),
             ("Hiérarchique (agglomératif)",    "hierarchique")]
        )
        self._etiquette(self.corps,
                        "Variables (sélection multiple) :", gras=True)
        self.liste = self._liste_choix(
            self.corps, self.cols_num, hauteur=5, mode="multiple"
        )
        for i in range(len(self.cols_num)):
            self.liste.selection_set(i)
        self._etiquette(self.corps, "Nombre de groupes k (K-Means / Hiérar.) :")
        self.var_k = tk.IntVar(value=3)
        ttk.Spinbox(self.corps, from_=2, to=20,
                    textvariable=self.var_k, width=6).pack(anchor="w", padx=16)
        self._etiquette(self.corps, "Rayon eps (DBSCAN) :")
        self.var_eps = tk.DoubleVar(value=0.5)
        ttk.Spinbox(self.corps, from_=0.01, to=10, increment=0.05,
                    textvariable=self.var_eps, width=8).pack(anchor="w", padx=16)

    def _collecter(self):
        sel = self.liste.curselection()
        colonnes = [self.cols_num[i] for i in sel] if sel else self.cols_num
        return {
            "algorithme": self.algorithme.get(),
            "colonnes":   colonnes,
            "nb_groupes": self.var_k.get(),
            "eps":        self.var_eps.get(),
        }


class DlgRegression(DialogueBase):
    def __init__(self, parent, cols_num):
        self.cols_num = cols_num
        super().__init__(parent, "Régression", 540, 480)

    def _construire_corps(self):
        self.type_reg = self._groupe_boutons_radio(
            self.corps, "Type de régression :",
            [("Linéaire (MCO)",             "lineaire"),
             ("Ridge (régularisation L2)",  "ridge"),
             ("Lasso (régularisation L1)",  "lasso"),
             ("Forêt aléatoire",            "foret")]
        )
        ligne = tk.Frame(self.corps, bg=COULEURS["fond"])
        ligne.pack(fill="x", pady=4)
        c1 = tk.Frame(ligne, bg=COULEURS["fond"])
        c1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._etiquette(c1, "Variable cible (Y) :")
        self.liste_y = self._liste_choix(c1, self.cols_num, hauteur=6)
        if self.cols_num:
            self.liste_y.selection_set(len(self.cols_num) - 1)
        c2 = tk.Frame(ligne, bg=COULEURS["fond"])
        c2.pack(side="left", fill="both", expand=True)
        self._etiquette(c2, "Variables prédicteurs (X) :")
        self.liste_x = self._liste_choix(
            c2, self.cols_num, hauteur=6, mode="multiple"
        )
        for i in range(len(self.cols_num) - 1):
            self.liste_x.selection_set(i)
        self.chk_validation = self._case_a_cocher(
            self.corps, "Validation croisée 5 blocs"
        )
        self.var_alpha_reg = self._compteur(
            self.corps, 0.001, 100, 1.0, "Paramètre alpha (Ridge/Lasso) :"
        )

    def _collecter(self):
        sy = self.liste_y.curselection()
        sx = self.liste_x.curselection()
        if not sy:
            messagebox.showwarning("Sélection requise",
                                   "Choisissez la variable cible Y.",
                                   parent=self)
            return None
        col_y = self.cols_num[sy[0]]
        cols_x = (
            [self.cols_num[i] for i in sx]
            if sx
            else [c for c in self.cols_num if c != col_y]
        )
        return {
            "type":           self.type_reg.get(),
            "col_y":          col_y,
            "cols_x":         cols_x,
            "validation":     self.chk_validation.get(),
            "alpha_reg":      self.var_alpha_reg.get(),
        }


class DlgAnomalies(DialogueBase):
    def __init__(self, parent, cols_num):
        self.cols_num = cols_num
        super().__init__(parent, "Détection des anomalies", 480, 360)

    def _construire_corps(self):
        self.methode = self._groupe_boutons_radio(
            self.corps, "Méthode :",
            [("Isolation Forest",          "isolation_forest"),
             ("Z-score (|z| > seuil)",     "zscore"),
             ("IQR (règle de 1,5×IQR)",    "iqr")]
        )
        self._etiquette(self.corps,
                        "Variables (sélection multiple) :", gras=True)
        self.liste = self._liste_choix(
            self.corps, self.cols_num, hauteur=5, mode="multiple"
        )
        for i in range(len(self.cols_num)):
            self.liste.selection_set(i)
        self.var_contam = self._compteur(
            self.corps, 0.01, 0.5, 0.05, "Taux de contamination (Isolation Forest) :"
        )
        self.var_seuil_z = self._compteur(
            self.corps, 1.0, 5.0, 3.0, "Seuil Z-score :"
        )

    def _collecter(self):
        sel = self.liste.curselection()
        colonnes = [self.cols_num[i] for i in sel] if sel else self.cols_num
        return {
            "methode":       self.methode.get(),
            "colonnes":      colonnes,
            "contamination": self.var_contam.get(),
            "seuil_z":       self.var_seuil_z.get(),
        }


class DlgGraphique(DialogueBase):
    TYPES_GRAPHIQUES = [
        "Histogramme",
        "Boîtes à moustaches",
        "Nuage de points",
        "Diagramme en barres",
        "Camembert",
        "Carte de chaleur (corrélation)",
        "Violon",
        "Densité KDE",
        "Graphique Q-Q",
        "Série temporelle",
        "Matrice de dispersion",
        "Barres empilées",
        "Graphique à bulles",
        "Tableau de bord",
    ]

    def __init__(self, parent, cols_num, cols_cat):
        self.cols_num = cols_num
        self.cols_cat = cols_cat
        super().__init__(parent, "Créer un graphique", 580, 540)

    def _construire_corps(self):
        self._etiquette(self.corps, "Type de graphique :", gras=True)
        self.var_type = tk.StringVar(value="Histogramme")
        ttk.Combobox(self.corps, textvariable=self.var_type,
                     values=self.TYPES_GRAPHIQUES,
                     state="readonly", width=32).pack(anchor="w", pady=4, padx=16)

        ligne = tk.Frame(self.corps, bg=COULEURS["fond"])
        ligne.pack(fill="x", pady=4)

        c1 = tk.Frame(ligne, bg=COULEURS["fond"])
        c1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self._etiquette(c1, "Variable principale (X) :")
        self.liste_x = self._liste_choix(c1, self.cols_num, hauteur=6)
        if self.cols_num:
            self.liste_x.selection_set(0)

        c2 = tk.Frame(ligne, bg=COULEURS["fond"])
        c2.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self._etiquette(c2, "Variable secondaire (Y) :")
        self.liste_y = self._liste_choix(c2, self.cols_num, hauteur=6)
        if len(self.cols_num) > 1:
            self.liste_y.selection_set(1)

        c3 = tk.Frame(ligne, bg=COULEURS["fond"])
        c3.pack(side="left", fill="both", expand=True)
        self._etiquette(c3, "Groupes / Couleur :")
        self.liste_grp = self._liste_choix(
            c3, ["(aucun)"] + self.cols_cat, hauteur=6
        )
        self.liste_grp.selection_set(0)

        bas = tk.Frame(self.corps, bg=COULEURS["fond"])
        bas.pack(fill="x", pady=4)
        self._etiquette(bas, "Style :")
        self.var_style = tk.StringVar(value="seaborn-v0_8")
        ttk.Combobox(bas, textvariable=self.var_style, width=22,
                     values=["seaborn-v0_8", "ggplot", "bmh",
                             "fivethirtyeight", "dark_background"],
                     state="readonly").pack(side="left", padx=4)
        self._etiquette(bas, "  Palette :")
        self.var_palette = tk.StringVar(value="deep")
        ttk.Combobox(bas, textvariable=self.var_palette, width=14,
                     values=["deep", "muted", "bright", "pastel",
                             "Set2", "tab10", "viridis", "plasma"],
                     state="readonly").pack(side="left", padx=4)

    def _collecter(self):
        sx  = self.liste_x.curselection()
        sy  = self.liste_y.curselection()
        sg  = self.liste_grp.curselection()
        vals_grp = ["(aucun)"] + self.cols_cat
        col_grp = None if not sg or vals_grp[sg[0]] == "(aucun)" else vals_grp[sg[0]]
        return {
            "type":    self.var_type.get(),
            "col_x":   self.cols_num[sx[0]] if sx and self.cols_num else None,
            "col_y":   self.cols_num[sy[0]] if sy and self.cols_num else None,
            "col_grp": col_grp,
            "style":   self.var_style.get(),
            "palette": self.var_palette.get(),
        }


class DlgNettoyage(DialogueBase):
    def __init__(self, parent):
        super().__init__(parent, "Nettoyage des données", 400, 320)

    def _construire_corps(self):
        self.chk_doublons = self._case_a_cocher(
            self.corps, "Supprimer les doublons"
        )
        self.strategie_na = self._groupe_boutons_radio(
            self.corps, "Traitement des valeurs manquantes :",
            [("Ne rien faire",                  "aucune"),
             ("Supprimer les lignes incomplètes","supprimer"),
             ("Remplacer par la moyenne",        "moyenne"),
             ("Remplacer par la médiane",        "mediane"),
             ("Remplacer par le mode",           "mode")]
        )

    def _collecter(self):
        return {
            "doublons":   self.chk_doublons.get(),
            "strategie":  self.strategie_na.get(),
        }


# ═══════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════

class ApplicationPrincipale(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DataAnalyst Pro – Logiciel d'analyse de données")
        self.geometry("1300x820")
        self.minsize(1024, 640)
        self.configure(bg=COULEURS["fond"])

        self.jeu_donnees = JeuDonnees()
        self._figure_courante = None

        self._construire_interface()

    # ── Construction de l'interface ───────────────────────────────

    def _construire_interface(self):
        # Barre de titre
        barre_titre = tk.Frame(self, bg=COULEURS["menu_titre"], height=50)
        barre_titre.pack(fill="x")
        barre_titre.pack_propagate(False)
        tk.Label(barre_titre, text="📊  DataAnalyst Pro",
                 font=("Segoe UI", 15, "bold"),
                 fg="white", bg=COULEURS["menu_titre"]).pack(
                     side="left", padx=18, pady=8)
        self._lbl_fichier = tk.Label(
            barre_titre, text="Aucun fichier chargé",
            font=POL_PETITE, fg="#bee3f8", bg=COULEURS["menu_titre"]
        )
        self._lbl_fichier.pack(side="left", padx=8)

        # Corps principal
        corps = tk.Frame(self, bg=COULEURS["fond"])
        corps.pack(fill="both", expand=True)

        self._construire_barre_laterale(corps)

        # Zone de droite : onglets
        zone_droite = tk.Frame(corps, bg=COULEURS["fond"])
        zone_droite.pack(fill="both", expand=True)

        style_onglets = ttk.Style()
        style_onglets.theme_use("clam")
        style_onglets.configure("T.TNotebook", background=COULEURS["fond"],
                                borderwidth=0)
        style_onglets.configure("T.TNotebook.Tab", font=POL_NORMALE,
                                padding=[14, 5])
        style_onglets.map("T.TNotebook.Tab",
                          background=[("selected", COULEURS["accent"])],
                          foreground=[("selected", "white")])

        self.onglets = ttk.Notebook(zone_droite, style="T.TNotebook")
        self.onglets.pack(fill="both", expand=True, padx=10, pady=8)

        self.ong_donnees   = tk.Frame(self.onglets, bg=COULEURS["carte"])
        self.ong_resultats = tk.Frame(self.onglets, bg=COULEURS["carte"])
        self.ong_graphiques= tk.Frame(self.onglets, bg=COULEURS["carte"])

        self.onglets.add(self.ong_donnees,    text="  📋 Données  ")
        self.onglets.add(self.ong_resultats,  text="  📄 Résultats  ")
        self.onglets.add(self.ong_graphiques, text="  🎨 Graphiques  ")

        self._construire_ong_donnees()
        self._construire_ong_resultats()
        self._construire_ong_graphiques()

        # Barre de statut
        self._statut = tk.StringVar(value="Prêt.")
        tk.Label(self, textvariable=self._statut, font=POL_PETITE,
                 fg=COULEURS["discret"], bg=COULEURS["bordure"],
                 anchor="w", padx=10).pack(fill="x", side="bottom")

    # ── Barre latérale accordéon ──────────────────────────────────

    def _construire_barre_laterale(self, parent):
        LARGEUR_BARRE = 220
        conteneur = tk.Frame(parent, bg=COULEURS["barre_lat"], width=LARGEUR_BARRE)
        conteneur.pack(fill="y", side="left")
        conteneur.pack_propagate(False)

        # Scrollbar
        barre_defilement = tk.Scrollbar(conteneur, orient="vertical", width=12,
                                         troughcolor=COULEURS["barre_lat"],
                                         bg="#4a7fa5", activebackground="#63b3ed")
        barre_defilement.pack(side="right", fill="y")

        # Canvas
        cvs = tk.Canvas(conteneur, bg=COULEURS["barre_lat"],
                        highlightthickness=0,
                        yscrollcommand=barre_defilement.set)
        cvs.pack(side="left", fill="both", expand=True)
        barre_defilement.config(command=cvs.yview)

        # Frame intérieure
        interieur = tk.Frame(cvs, bg=COULEURS["barre_lat"])
        id_win = cvs.create_window((0, 0), window=interieur, anchor="nw")

        def _ajuster(evt):
            cvs.itemconfig(id_win, width=evt.width)
        cvs.bind("<Configure>", _ajuster)

        def _actualiser(evt=None):
            interieur.update_idletasks()
            cvs.configure(scrollregion=cvs.bbox("all"))
        interieur.bind("<Configure>", _actualiser)

        def _molette(evt):
            if evt.delta:
                cvs.yview_scroll(int(-1 * evt.delta / 120), "units")
            elif evt.num == 4:
                cvs.yview_scroll(-1, "units")
            elif evt.num == 5:
                cvs.yview_scroll(1, "units")
        for widget in (cvs, interieur):
            widget.bind("<MouseWheel>", _molette)
            widget.bind("<Button-4>", _molette)
            widget.bind("<Button-5>", _molette)

        # Helper : item de menu
        def _creer_item(conteneur_items, etiquette, commande, couleur_survol):
            b = tk.Button(
                conteneur_items, text=etiquette, command=commande,
                bg="#16304f", fg="white", font=("Segoe UI", 9),
                relief="flat", anchor="w", padx=20, pady=6,
                cursor="hand2", bd=0,
                activebackground=couleur_survol, activeforeground="white",
            )
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, w=b, c=couleur_survol: w.config(bg=c))
            b.bind("<Leave>", lambda e, w=b: w.config(bg="#16304f"))
            b.bind("<MouseWheel>", _molette)
            b.bind("<Button-4>", _molette)
            b.bind("<Button-5>", _molette)

        # Helper : section accordéon
        def _creer_section(titre, items_menu, depliee=False):
            etat = {"ouvert": depliee}
            var_fleche = tk.StringVar(
                value=f"{'▼' if depliee else '▶'}  {titre}"
            )
            # Cadre global de la section (titre + corps ensemble)
            cadre_section = tk.Frame(interieur, bg=COULEURS["barre_lat"])
            cadre_section.pack(fill="x", pady=(2, 0))
            for evt in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                cadre_section.bind(evt, _molette)

            # Bouton titre
            btn_titre = tk.Button(
                cadre_section, textvariable=var_fleche,
                bg=COULEURS["menu_titre"], fg="white",
                font=("Segoe UI", 9, "bold"),
                relief="flat", anchor="w", padx=10, pady=8,
                cursor="hand2", bd=0,
                activebackground="#2c5282", activeforeground="white",
            )
            btn_titre.pack(fill="x")
            btn_titre.bind("<MouseWheel>", _molette)
            btn_titre.bind("<Button-4>", _molette)
            btn_titre.bind("<Button-5>", _molette)

            # Corps des items (dans le même cadre_section)
            corps_items = tk.Frame(cadre_section, bg="#16304f")
            for (lbl, cmd, coul) in items_menu:
                _creer_item(corps_items, lbl, cmd, coul)

            # Séparateur
            tk.Frame(cadre_section, bg="#0f2340", height=1).pack(
                fill="x", side="bottom"
            )

            if depliee:
                corps_items.pack(fill="x")

            def _basculer():
                if etat["ouvert"]:
                    corps_items.pack_forget()
                    var_fleche.set(f"▶  {titre}")
                    etat["ouvert"] = False
                else:
                    corps_items.pack(fill="x")
                    var_fleche.set(f"▼  {titre}")
                    etat["ouvert"] = True
                _actualiser()

            btn_titre.config(command=_basculer)

        # Logo
        logo = tk.Label(interieur, text="📊  DataAnalyst Pro",
                        font=("Segoe UI", 10, "bold"),
                        fg="white", bg=COULEURS["barre_lat"], pady=10)
        logo.pack(fill="x")
        logo.bind("<MouseWheel>", _molette)
        tk.Frame(interieur, bg="#4a90d9", height=2).pack(fill="x")

        # ── Sections du menu ──────────────────────────────────────
        _creer_section("  DONNÉES", [
            ("📂  Ouvrir un fichier",     self._ouvrir_fichier,  COULEURS["accent"]),
            ("🔢  Données d'exemple",     self._charger_exemple, COULEURS["accent"]),
            ("🧹  Nettoyer les données",  self._nettoyer,        COULEURS["orange"]),
            ("📊  Aperçu et informations",self._apercu_info,     COULEURS["accent"]),
        ], depliee=True)

        _creer_section("  ANALYSES DESCRIPTIVES", [
            ("📋  Fréquences",            self._run_frequences,     COULEURS["vert"]),
            ("📈  Statistiques desc.",    self._run_stats_desc,     COULEURS["vert"]),
            ("🔗  Corrélations",          self._run_correlation,    COULEURS["vert"]),
            ("🔀  Analyse bivariée",      self._run_bivariee,       COULEURS["vert"]),
        ], depliee=True)

        _creer_section("  TESTS STATISTIQUES", [
            ("📐  Test de normalité",     self._run_normalite,   COULEURS["orange"]),
            ("🔬  Test t / Wilcoxon",     self._run_test_t,      COULEURS["orange"]),
            ("📊  ANOVA / Kruskal",       self._run_anova,       COULEURS["orange"]),
            ("🎲  Chi² / Tableau croisé", self._run_chi2,        COULEURS["orange"]),
        ], depliee=False)

        _creer_section("  MACHINE LEARNING", [
            ("🔵  ACP (composantes)",     self._run_acp,         COULEURS["accent"]),
            ("🟢  Partitionnement",       self._run_partitionnement, COULEURS["accent"]),
            ("📉  Régression",            self._run_regression,  COULEURS["accent"]),
            ("⚠   Détection anomalies",  self._run_anomalies,   COULEURS["accent"]),
        ], depliee=False)

        _creer_section("  GRAPHIQUES ET RAPPORT", [
            ("🎨  Créer un graphique",    self._run_graphique,       "#553C9A"),
            ("📄  Générer rapport HTML",  self._generer_rapport,     COULEURS["rouge"]),
        ], depliee=False)

        interieur.update_idletasks()
        cvs.configure(scrollregion=cvs.bbox("all"))

    # ── Onglet Données ────────────────────────────────────────────

    def _construire_ong_donnees(self):
        ong = self.ong_donnees
        entete = tk.Frame(ong, bg=COULEURS["carte"])
        entete.pack(fill="x", padx=12, pady=8)
        tk.Label(entete, text="Aperçu des données", font=POL_TITRE,
                 bg=COULEURS["carte"], fg=COULEURS["texte"]).pack(side="left")
        creer_bouton(entete, "📂 Ouvrir",
                     self._ouvrir_fichier).pack(side="right", padx=4)
        creer_bouton(entete, "🔢 Exemple",
                     self._charger_exemple,
                     couleur=COULEURS["vert"]).pack(side="right", padx=4)

        self._barre_info = tk.Frame(ong, bg=COULEURS["fond"])
        self._barre_info.pack(fill="x", padx=12, pady=(0, 6))

        cadre_tableau = tk.Frame(ong, bg=COULEURS["carte"])
        cadre_tableau.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.tableau_vue = ttk.Treeview(cadre_tableau, show="headings")
        barre_v = ttk.Scrollbar(cadre_tableau, orient="vertical",
                                 command=self.tableau_vue.yview)
        barre_h = ttk.Scrollbar(cadre_tableau, orient="horizontal",
                                 command=self.tableau_vue.xview)
        self.tableau_vue.configure(yscrollcommand=barre_v.set,
                                   xscrollcommand=barre_h.set)
        barre_v.pack(side="right",  fill="y")
        barre_h.pack(side="bottom", fill="x")
        self.tableau_vue.pack(fill="both", expand=True)
        s = ttk.Style()
        s.configure("Treeview", rowheight=24, font=POL_PETITE, background="white")
        s.configure("Treeview.Heading", font=POL_GRAS,
                    background=COULEURS["menu_titre"], foreground="white")
        s.map("Treeview", background=[("selected", COULEURS["accent"])])

    # ── Onglet Résultats ──────────────────────────────────────────

    def _construire_ong_resultats(self):
        ong = self.ong_resultats
        barre_actions = tk.Frame(ong, bg=COULEURS["carte"])
        barre_actions.pack(fill="x", padx=12, pady=8)
        tk.Label(barre_actions, text="Zone de résultats",
                 font=POL_TITRE, bg=COULEURS["carte"],
                 fg=COULEURS["texte"]).pack(side="left")
        creer_bouton(barre_actions, "🗑 Effacer",
                     self._effacer_resultats,
                     couleur=COULEURS["rouge"]).pack(side="right", padx=4)
        creer_bouton(barre_actions, "💾 Exporter en TXT",
                     self._exporter_txt,
                     couleur=COULEURS["vert"]).pack(side="right", padx=4)

        self.zone_sortie = scrolledtext.ScrolledText(
            ong, font=POL_CODE,
            bg=COULEURS["sortie_fond"], fg=COULEURS["sortie_txt"],
            insertbackground="white", wrap="none", state="normal"
        )
        self.zone_sortie.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    # ── Onglet Graphiques ─────────────────────────────────────────

    def _construire_ong_graphiques(self):
        ong = self.ong_graphiques
        entete = tk.Frame(ong, bg=COULEURS["carte"])
        entete.pack(fill="x", padx=12, pady=8)
        tk.Label(entete, text="Visualisations",
                 font=POL_TITRE, bg=COULEURS["carte"],
                 fg=COULEURS["texte"]).pack(side="left")
        creer_bouton(entete, "💾 Sauvegarder le graphique",
                     self._sauvegarder_graphique,
                     couleur=COULEURS["vert"]).pack(side="right", padx=4)

        self._zone_graphique = tk.Frame(ong, bg=COULEURS["carte"])
        self._zone_graphique.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        tk.Label(self._zone_graphique,
                 text="Utilisez « Créer un graphique » dans le menu de gauche.",
                 font=POL_NORMALE, fg=COULEURS["discret"],
                 bg=COULEURS["carte"]).pack(expand=True)

    # ── Gestion des données ───────────────────────────────────────

    def _ouvrir_fichier(self):
        chemin = filedialog.askopenfilename(
            title="Ouvrir un fichier de données",
            filetypes=[
                ("Tous les formats", "*.csv *.xlsx *.xls *.json *.parquet *.tsv"),
                ("CSV",     "*.csv"),
                ("Excel",   "*.xlsx *.xls"),
                ("JSON",    "*.json"),
                ("Parquet", "*.parquet"),
            ]
        )
        if chemin:
            self._statut.set(f"Chargement de {os.path.basename(chemin)}…")
            def _charger():
                try:
                    self.jeu_donnees.charger_fichier(chemin)
                    self.after(0, self._rafraichir_donnees)
                except Exception as err:
                    self.after(0, lambda: messagebox.showerror("Erreur", str(err)))
            threading.Thread(target=_charger, daemon=True).start()

    def _charger_exemple(self):
        fenetre = tk.Toplevel(self)
        fenetre.title("Choisir un exemple")
        fenetre.geometry("320x200")
        fenetre.configure(bg=COULEURS["fond"])
        fenetre.resizable(False, False)
        tk.Label(fenetre, text="Jeu de données d'exemple",
                 font=POL_TITRE, bg=COULEURS["fond"]).pack(pady=12)
        var_choix = tk.StringVar(value="iris")
        for nom, label in [("iris", "Iris (fleurs)"),
                            ("titanic", "Titanic (passagers)"),
                            ("pourboires", "Pourboires (restaurant)")]:
            tk.Radiobutton(fenetre, text=label, variable=var_choix, value=nom,
                           bg=COULEURS["fond"], font=POL_NORMALE).pack(anchor="w", padx=30)
        def _ok():
            fenetre.destroy()
            self._statut.set(f"Chargement de l'exemple {var_choix.get()}…")
            def _charger():
                self.jeu_donnees.charger_exemple(var_choix.get())
                self.after(0, self._rafraichir_donnees)
            threading.Thread(target=_charger, daemon=True).start()
        creer_bouton(fenetre, "✔ Charger", _ok).pack(pady=10)

    def _nettoyer(self):
        if not self._verifier_donnees(): return
        dlg = DlgNettoyage(self)
        self.wait_window(dlg)
        if dlg.resultat:
            self.jeu_donnees = self.jeu_donnees.nettoyer(
                supprimer_doublons=dlg.resultat["doublons"],
                strategie_na=dlg.resultat["strategie"]
            )
            self._rafraichir_donnees()
            info = self.jeu_donnees.info()
            self._afficher(
                f"{'═'*60}\n  NETTOYAGE EFFECTUÉ\n{'═'*60}\n"
                + "\n".join(f"  {k:<30} {v}" for k, v in info.items()) + "\n"
            )

    def _apercu_info(self):
        if not self._verifier_donnees(): return
        info = self.jeu_donnees.info()
        texte = (
            f"{'═'*60}\n"
            f"  INFORMATIONS – {info['nom']}\n"
            f"{'═'*60}\n"
        )
        for cle, val in info.items():
            texte += f"  {cle:<30} {val}\n"
        texte += "\n── Aperçu (5 premières lignes) ──\n"
        texte += self.jeu_donnees.apercu().to_string() + "\n"
        texte += "\n── Description statistique ──\n"
        texte += self.jeu_donnees.decrire().to_string() + "\n"
        self._afficher(texte)

    def _rafraichir_donnees(self):
        tableau = self.jeu_donnees.donnees
        if tableau is None: return
        # Remplir le Treeview
        self.tableau_vue.delete(*self.tableau_vue.get_children())
        self.tableau_vue["columns"] = list(tableau.columns)
        for col in tableau.columns:
            self.tableau_vue.heading(col, text=col)
            self.tableau_vue.column(col, width=110, minwidth=60, anchor="center")
        for _, ligne in tableau.head(200).iterrows():
            self.tableau_vue.insert(
                "", "end", values=[str(v)[:40] for v in ligne]
            )
        # Barre d'info
        for w in self._barre_info.winfo_children():
            w.destroy()
        info = self.jeu_donnees.info()
        self._lbl_fichier.config(
            text=f"📂 {info['nom']}  |  {info['nb_lignes']} × {info['nb_colonnes']}"
        )
        badges = [
            (f"🔢 {info['nb_lignes']} lignes",         COULEURS["accent"]),
            (f"🗂 {info['nb_colonnes']} colonnes",      COULEURS["vert"]),
            (f"⚠ {info['valeurs_manquantes']} manquants",COULEURS["orange"]),
            (f"♻ {info['doublons']} doublons",          COULEURS["rouge"]),
        ]
        for txt, coul in badges:
            tk.Label(self._barre_info, text=txt, font=POL_PETITE,
                     fg="white", bg=coul, padx=8, pady=3
                     ).pack(side="left", padx=4)
        self._statut.set(f"Données chargées : {info['nom']}")
        self.onglets.select(0)

    # ── Zone de sortie ────────────────────────────────────────────

    def _afficher(self, texte: str):
        self.zone_sortie.config(state="normal")
        self.zone_sortie.insert("end", texte + "\n")
        self.zone_sortie.see("end")
        self.onglets.select(1)

    def _effacer_resultats(self):
        self.zone_sortie.config(state="normal")
        self.zone_sortie.delete("1.0", "end")

    def _exporter_txt(self):
        chemin = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte", "*.txt")]
        )
        if chemin:
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(self.zone_sortie.get("1.0", "end"))
            messagebox.showinfo("Succès", f"Résultats exportés : {chemin}")

    def _sauvegarder_graphique(self):
        if self._figure_courante is None:
            messagebox.showwarning("Aucun graphique",
                                   "Aucun graphique à sauvegarder.")
            return
        chemin = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")]
        )
        if chemin:
            self._figure_courante.savefig(chemin, bbox_inches="tight", dpi=150)
            messagebox.showinfo("Succès", f"Graphique sauvegardé : {chemin}")

    def _verifier_donnees(self):
        if self.jeu_donnees.donnees is None:
            messagebox.showwarning(
                "Données manquantes",
                "Veuillez d'abord charger un jeu de données."
            )
            return False
        return True

    # ── Analyses descriptives ─────────────────────────────────────

    def _run_frequences(self):
        if not self._verifier_donnees(): return
        dlg = DlgFrequences(self,
                            self.jeu_donnees.colonnes_categorielles(),
                            self.jeu_donnees.colonnes_numeriques())
        self.wait_window(dlg)
        if dlg.resultat is None: return
        colonne = dlg.resultat["colonne"]
        top     = dlg.resultat["top"]
        frequences = self.jeu_donnees.donnees[colonne].value_counts().head(top)
        pourcentages = (frequences / len(self.jeu_donnees.donnees) * 100).round(2)
        tableau_freq = pd.DataFrame({
            "Effectif":      frequences,
            "Pourcentage (%)": pourcentages,
            "Cumulé (%)":    pourcentages.cumsum().round(2),
        })
        self._afficher(
            f"{'═'*60}\n  FRÉQUENCES – {colonne}\n{'═'*60}\n"
            + tableau_freq.to_string() + "\n"
        )

    def _run_stats_desc(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if not cols_num:
            messagebox.showwarning("Données", "Aucune variable numérique.")
            return
        dlg = DlgStatistiquesDesc(self, cols_num)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from scipy import stats as sp
        colonnes = dlg.resultat["colonnes"]
        tableau  = self.jeu_donnees.donnees[colonnes]
        texte    = f"{'═'*60}\n  STATISTIQUES DESCRIPTIVES\n{'═'*60}\n"

        if dlg.resultat["base"]:
            texte += "\n── Statistiques de base ──\n"
            texte += tableau.describe(
                percentiles=[.10, .25, .50, .75, .90]
            ).to_string() + "\n"

        if dlg.resultat["asymetrie"]:
            asym = pd.DataFrame({
                "Asymétrie (skewness)":     tableau.skew(),
                "Aplatissement (kurtosis)": tableau.kurtosis(),
            })
            texte += "\n── Asymétrie et aplatissement ──\n"
            texte += asym.to_string() + "\n"

        if dlg.resultat["manquants"]:
            manq = pd.DataFrame({
                "Valeurs manquantes": tableau.isnull().sum(),
                "Pourcentage (%)":    (tableau.isnull().mean() * 100).round(2),
            })
            texte += "\n── Valeurs manquantes ──\n"
            texte += manq.to_string() + "\n"

        if dlg.resultat["cv"]:
            cv = (tableau.std() / tableau.mean().abs() * 100).rename("CV (%)")
            texte += "\n── Coefficient de variation ──\n"
            texte += cv.to_frame().to_string() + "\n"

        if dlg.resultat["aberrantes"]:
            z = np.abs(sp.zscore(tableau.dropna()))
            nb_z = (z > 3).sum(axis=0)
            Q1, Q3 = tableau.quantile(.25), tableau.quantile(.75)
            IQR = Q3 - Q1
            nb_iqr = (
                (tableau < Q1 - 1.5 * IQR) | (tableau > Q3 + 1.5 * IQR)
            ).sum()
            aberrants = pd.DataFrame({
                "Nb aberrants Z>3": nb_z,
                "Nb aberrants IQR": nb_iqr,
            })
            texte += "\n── Détection des valeurs aberrantes ──\n"
            texte += aberrants.to_string() + "\n"

        self._afficher(texte)

    def _run_correlation(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if len(cols_num) < 2:
            messagebox.showwarning("Données",
                                   "Au moins 2 variables numériques requises.")
            return
        dlg = DlgCorrelation(self, cols_num)
        self.wait_window(dlg)
        if dlg.resultat is None: return
        matrice = self.jeu_donnees.donnees[
            dlg.resultat["colonnes"]
        ].corr(method=dlg.resultat["methode"])
        self._afficher(
            f"{'═'*60}\n"
            f"  CORRÉLATIONS ({dlg.resultat['methode'].upper()})\n"
            f"{'═'*60}\n"
            + matrice.round(4).to_string() + "\n"
        )

    def _run_bivariee(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        cols_cat = self.jeu_donnees.colonnes_categorielles()
        dlg = DlgBivariee(self, cols_num, cols_cat)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from scipy import stats as sp
        tableau = self.jeu_donnees.donnees
        col_x   = dlg.resultat["col_x"]
        col_y   = dlg.resultat["col_y"]
        type_   = dlg.resultat["type"]
        texte   = (
            f"{'═'*60}\n"
            f"  ANALYSE BIVARIÉE : {col_x}  ×  {col_y}\n"
            f"{'═'*60}\n"
        )

        if type_ == "correlation":
            r, p = sp.pearsonr(tableau[col_x].dropna(), tableau[col_y].dropna())
            rho, p2 = sp.spearmanr(tableau[col_x].dropna(), tableau[col_y].dropna())
            texte += (
                f"\n  Pearson   r={r:.4f}  p={p:.4f}\n"
                f"  Spearman ρ={rho:.4f}  p={p2:.4f}\n"
            )
        elif type_ == "test_t":
            groupes = tableau[col_x].dropna().unique()[:2]
            g1 = tableau[tableau[col_x] == groupes[0]][col_y].dropna()
            g2 = tableau[tableau[col_x] == groupes[1]][col_y].dropna()
            stat_t, p = sp.ttest_ind(g1, g2)
            texte += (
                f"\n  Test t indépendant – {col_y} selon {col_x}\n"
                f"  Groupe {groupes[0]} : n={len(g1)}, µ={g1.mean():.4f}\n"
                f"  Groupe {groupes[1]} : n={len(g2)}, µ={g2.mean():.4f}\n"
                f"  t={stat_t:.4f}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < .05 else 'Non significatif'}\n"
            )
        elif type_ == "anova":
            groupes_val = tableau[col_x].dropna().unique()
            donnees_grp = [
                tableau[tableau[col_x] == g][col_y].dropna().values
                for g in groupes_val
            ]
            F, p = sp.f_oneway(*donnees_grp)
            texte += (
                f"\n  ANOVA – {col_y} selon {col_x}\n"
                f"  F={F:.4f}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < .05 else 'Non significatif'}\n"
            )
        elif type_ == "chi2":
            tab_cont = pd.crosstab(tableau[col_x], tableau[col_y])
            chi2, p, ddl, _ = sp.chi2_contingency(tab_cont)
            texte += (
                f"\n  Chi² – {col_x} × {col_y}\n"
                f"  χ²={chi2:.4f}  ddl={ddl}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < .05 else 'Non significatif'}\n"
                f"\nTableau de contingence :\n{tab_cont.to_string()}\n"
            )
        elif type_ == "tableau_croise":
            tab_cont  = pd.crosstab(tableau[col_x], tableau[col_y],
                                    margins=True)
            tab_pct   = pd.crosstab(tableau[col_x], tableau[col_y],
                                    normalize="index") * 100
            texte += (
                f"\nTableau croisé :\n{tab_cont.to_string()}\n"
                f"\nTableau croisé (% lignes) :\n{tab_pct.round(1).to_string()}\n"
            )
        self._afficher(texte)

    # ── Tests statistiques ────────────────────────────────────────

    def _run_normalite(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if not cols_num: return
        dlg = DlgNormalite(self, cols_num)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from scipy import stats as sp
        tableau = self.jeu_donnees.donnees
        seuil   = dlg.resultat["seuil"]
        texte   = (
            f"{'═'*60}\n"
            f"  TESTS DE NORMALITÉ  (α={seuil})\n"
            f"{'═'*60}\n"
        )
        lignes = []
        for col in dlg.resultat["colonnes"]:
            serie = tableau[col].dropna()
            ligne = {"Variable": col, "n": len(serie)}
            if dlg.resultat["shapiro"] and len(serie) <= 5000:
                stat_w, p = sp.shapiro(serie)
                ligne["Shapiro W"] = round(stat_w, 4)
                ligne["Shapiro p"] = round(p, 4)
                ligne["Normale?"]  = "✓" if p > seuil else "✗"
            if dlg.resultat["ks"]:
                serie_std = (serie - serie.mean()) / serie.std()
                stat_s, p = sp.kstest(serie_std, "norm")
                ligne["KS stat"] = round(stat_s, 4)
                ligne["KS p"]    = round(p, 4)
            if dlg.resultat["dagostino"] and len(serie) >= 8:
                _, p = sp.normaltest(serie)
                ligne["D'Agostino p"] = round(p, 4)
            lignes.append(ligne)
        texte += pd.DataFrame(lignes).to_string(index=False) + "\n"
        self._afficher(texte)

    def _run_test_t(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        cols_cat = self.jeu_donnees.colonnes_categorielles()
        if not cols_num: return
        dlg = DlgTestT(self, cols_num, cols_cat)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from scipy import stats as sp
        tableau = self.jeu_donnees.donnees
        col     = dlg.resultat["col_num"]
        type_   = dlg.resultat["type"]
        mu0     = dlg.resultat["mu0"]
        seuil   = dlg.resultat["seuil"]
        texte   = f"{'═'*60}\n"

        if type_ == "1_echantillon":
            serie = tableau[col].dropna()
            stat_t, p = sp.ttest_1samp(serie, mu0)
            texte += (
                f"  TEST T – 1 ÉCHANTILLON – {col}  (μ₀={mu0})\n"
                f"{'═'*60}\n"
                f"  n={len(serie)}  moyenne={serie.mean():.4f}"
                f"  écart-type={serie.std():.4f}\n"
                f"  t={stat_t:.4f}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < seuil else 'Non significatif'}"
                f"  (α={seuil})\n"
            )
        elif type_ == "2_echantillons":
            col_cat = dlg.resultat["col_cat"]
            if not col_cat:
                messagebox.showwarning(
                    "Sélection manquante",
                    "Choisissez une variable catégorielle pour les groupes."
                )
                return
            groupes = tableau[col_cat].dropna().unique()
            if len(groupes) < 2:
                messagebox.showwarning(
                    "Données insuffisantes",
                    "La variable de groupes doit avoir au moins 2 modalités."
                )
                return
            g1 = tableau[tableau[col_cat] == groupes[0]][col].dropna()
            g2 = tableau[tableau[col_cat] == groupes[1]][col].dropna()
            stat_t, p = sp.ttest_ind(g1, g2)
            texte += (
                f"  TEST T – 2 ÉCHANTILLONS – {col}  par  {col_cat}\n"
                f"{'═'*60}\n"
                f"  {groupes[0]} : n={len(g1)}, µ={g1.mean():.4f}\n"
                f"  {groupes[1]} : n={len(g2)}, µ={g2.mean():.4f}\n"
                f"  t={stat_t:.4f}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < seuil else 'Non significatif'}"
                f"  (α={seuil})\n"
            )
        elif type_ == "wilcoxon":
            col_cat = dlg.resultat["col_cat"]
            if col_cat:
                groupes = tableau[col_cat].dropna().unique()
                g1 = tableau[tableau[col_cat] == groupes[0]][col].dropna()
                g2 = tableau[tableau[col_cat] == groupes[1]][col].dropna()
                nb = min(len(g1), len(g2))
                stat_w, p = sp.wilcoxon(g1.iloc[:nb].values, g2.iloc[:nb].values)
            else:
                serie = tableau[col].dropna()
                stat_w, p = sp.wilcoxon(serie - mu0)
            texte += (
                f"  TEST DE WILCOXON – {col}\n"
                f"{'═'*60}\n"
                f"  W={stat_w:.4f}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < seuil else 'Non significatif'}"
                f"  (α={seuil})\n"
            )
        self._afficher(texte)

    def _run_anova(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        cols_cat = self.jeu_donnees.colonnes_categorielles()
        dlg = DlgAnova(self, cols_num, cols_cat)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from scipy import stats as sp
        tableau = self.jeu_donnees.donnees
        col_dep = dlg.resultat["col_dep"]
        col_fac = dlg.resultat["col_fac"]
        seuil   = dlg.resultat["seuil"]

        if col_fac:
            valeurs_fac = tableau[col_fac].dropna().unique()
            groupes     = [
                tableau[tableau[col_fac] == g][col_dep].dropna().values
                for g in valeurs_fac
            ]
        else:
            valeurs_fac = cols_num
            groupes     = [tableau[c].dropna().values for c in cols_num]

        texte = (
            f"{'═'*60}\n"
            f"  {'ANOVA' if dlg.resultat['type'] == 'anova' else 'KRUSKAL-WALLIS'}"
            f" – {col_dep}\n"
            f"{'═'*60}\n"
            f"  Facteur : {col_fac or 'toutes colonnes numériques'}\n"
        )
        for g, donnees in zip(valeurs_fac, groupes):
            texte += (
                f"  {g} : n={len(donnees)}"
                f"  µ={np.mean(donnees):.4f}"
                f"  σ={np.std(donnees):.4f}\n"
            )
        if dlg.resultat["type"] == "anova":
            F, p = sp.f_oneway(*groupes)
            texte += (
                f"\n  F={F:.4f}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < seuil else 'Non significatif'}"
                f"  (α={seuil})\n"
            )
        else:
            H, p = sp.kruskal(*groupes)
            texte += (
                f"\n  H={H:.4f}  p={p:.4f}  "
                f"{'SIGNIFICATIF' if p < seuil else 'Non significatif'}"
                f"  (α={seuil})\n"
            )
        self._afficher(texte)

    def _run_chi2(self):
        if not self._verifier_donnees(): return
        cols_cat = self.jeu_donnees.colonnes_categorielles()
        if len(cols_cat) < 2:
            messagebox.showwarning("Données",
                                   "Au moins 2 variables catégorielles requises.")
            return
        dlg = DlgChi2(self, cols_cat)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from scipy import stats as sp
        tableau  = self.jeu_donnees.donnees
        col1     = dlg.resultat["col1"]
        col2     = dlg.resultat["col2"]
        seuil    = dlg.resultat["seuil"]
        tab_cont = pd.crosstab(tableau[col1], tableau[col2])
        chi2, p, ddl, esperees = sp.chi2_contingency(tab_cont)
        texte = (
            f"{'═'*60}\n"
            f"  CHI² D'INDÉPENDANCE – {col1}  ×  {col2}\n"
            f"{'═'*60}\n"
            f"  χ²={chi2:.4f}  ddl={ddl}  p={p:.4f}\n"
            f"  {'SIGNIFICATIF' if p < seuil else 'Non significatif'}"
            f"  (α={seuil})\n"
            f"\nEffectifs observés :\n{tab_cont.to_string()}\n"
            f"\nEffectifs attendus :\n"
            + pd.DataFrame(
                esperees.round(2),
                index=tab_cont.index,
                columns=tab_cont.columns
            ).to_string() + "\n"
        )
        self._afficher(texte)

    # ── Machine Learning ──────────────────────────────────────────

    def _run_acp(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if len(cols_num) < 2:
            messagebox.showwarning("Données",
                                   "Au moins 2 variables numériques requises.")
            return
        dlg = DlgACP(self, cols_num)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        colonnes     = dlg.resultat["colonnes"]
        nb_comp      = min(dlg.resultat["nb_composantes"], len(colonnes))
        X = self.jeu_donnees.donnees[colonnes].dropna().values
        if dlg.resultat["standardiser"]:
            X = StandardScaler().fit_transform(X)
        acp = PCA(n_components=nb_comp)
        acp.fit(X)
        variance     = acp.explained_variance_ratio_
        cumulee      = variance.cumsum()
        texte = (
            f"{'═'*60}\n"
            f"  ACP – {nb_comp} composantes principales\n"
            f"{'═'*60}\n"
            f"  Variables analysées : {colonnes}\n\n"
            f"  Variance expliquée par composante :\n"
        )
        for i, (v, c) in enumerate(zip(variance, cumulee)):
            texte += f"    CP{i+1} : {v*100:.2f}%  (cumulé : {c*100:.2f}%)\n"
        chargements = pd.DataFrame(
            acp.components_,
            columns=colonnes,
            index=[f"CP{i+1}" for i in range(nb_comp)]
        ).round(4)
        texte += "\nChargements (loadings) :\n" + chargements.to_string() + "\n"
        self._afficher(texte)

    def _run_partitionnement(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if len(cols_num) < 2: return
        dlg = DlgPartitionnement(self, cols_num)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
        from sklearn.metrics import (
            silhouette_score, calinski_harabasz_score, davies_bouldin_score
        )
        colonnes  = dlg.resultat["colonnes"]
        algo      = dlg.resultat["algorithme"]
        X = StandardScaler().fit_transform(
            self.jeu_donnees.donnees[colonnes].dropna().values
        )
        texte = (
            f"{'═'*60}\n"
            f"  PARTITIONNEMENT – {algo.upper()}\n"
            f"{'═'*60}\n"
        )
        if algo == "kmeans":
            k  = dlg.resultat["nb_groupes"]
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            etiquettes = km.fit_predict(X)
            texte += f"  Nombre de groupes k={k}  Inertie={km.inertia_:.4f}\n"
        elif algo == "dbscan":
            eps = dlg.resultat["eps"]
            db  = DBSCAN(eps=eps, min_samples=5)
            etiquettes = db.fit_predict(X)
            k   = len(set(etiquettes)) - (1 if -1 in etiquettes else 0)
            texte += (
                f"  eps={eps}  Groupes détectés={k}"
                f"  Points de bruit={(etiquettes == -1).sum()}\n"
            )
        else:
            k  = dlg.resultat["nb_groupes"]
            hc = AgglomerativeClustering(n_clusters=k)
            etiquettes = hc.fit_predict(X)
            texte += f"  Nombre de groupes k={k}  (hiérarchique agglomératif)\n"

        if len(set(etiquettes)) >= 2 and -1 not in set(etiquettes):
            texte += (
                f"  Silhouette              = {silhouette_score(X, etiquettes):.4f}\n"
                f"  Calinski-Harabasz       = {calinski_harabasz_score(X, etiquettes):.4f}\n"
                f"  Davies-Bouldin          = {davies_bouldin_score(X, etiquettes):.4f}\n"
            )
        comptage = pd.Series(etiquettes).value_counts().sort_index()
        texte += "\nDistribution des groupes :\n" + comptage.to_string() + "\n"
        self._afficher(texte)

    def _run_regression(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if len(cols_num) < 2: return
        dlg = DlgRegression(self, cols_num)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        from sklearn.model_selection import cross_val_score

        col_y      = dlg.resultat["col_y"]
        cols_x     = dlg.resultat["cols_x"]
        type_reg   = dlg.resultat["type"]
        alpha_reg  = dlg.resultat["alpha_reg"]
        tableau_ml = self.jeu_donnees.donnees[cols_x + [col_y]].dropna()
        y = tableau_ml[col_y].values
        X = StandardScaler().fit_transform(tableau_ml[cols_x].values)

        texte = (
            f"{'═'*60}\n"
            f"  RÉGRESSION {type_reg.upper()} – Variable cible : {col_y}\n"
            f"{'═'*60}\n"
            f"  Prédicteurs : {cols_x}\n"
            f"  n = {len(y)}\n\n"
        )

        if type_reg == "lineaire":
            from sklearn.linear_model import LinearRegression
            modele = LinearRegression()
        elif type_reg == "ridge":
            from sklearn.linear_model import Ridge
            modele = Ridge(alpha=alpha_reg)
        elif type_reg == "lasso":
            from sklearn.linear_model import Lasso
            modele = Lasso(alpha=alpha_reg)
        elif type_reg == "foret":
            from sklearn.ensemble import RandomForestRegressor
            modele = RandomForestRegressor(n_estimators=100, random_state=42)

        modele.fit(X, y)
        y_pred = modele.predict(X)
        texte += (
            f"  R²   = {r2_score(y, y_pred):.4f}\n"
            f"  ECM  = {mean_squared_error(y, y_pred):.4f}\n"
            f"  RECM = {mean_squared_error(y, y_pred)**.5:.4f}\n"
            f"  EAM  = {mean_absolute_error(y, y_pred):.4f}\n"
        )
        if dlg.resultat["validation"]:
            cv = cross_val_score(modele, X, y, cv=5, scoring="r2")
            texte += (
                f"\n  R² validation croisée (5 blocs) :\n"
                f"  {cv.round(4)}\n"
                f"  Moyenne = {cv.mean():.4f}  (±{cv.std():.4f})\n"
            )
        if type_reg in ("lineaire", "ridge", "lasso") and hasattr(modele, "coef_"):
            texte += "\n  Coefficients :\n"
            for var, coef in zip(cols_x, modele.coef_):
                texte += f"    {var:<35} {coef:.6f}\n"
            texte += f"    Constante{' '*27} {modele.intercept_:.6f}\n"
        if type_reg == "foret" and hasattr(modele, "feature_importances_"):
            texte += "\n  Importance des variables :\n"
            importance = sorted(
                zip(cols_x, modele.feature_importances_),
                key=lambda x: -x[1]
            )
            for var, imp in importance:
                texte += f"    {var:<35} {imp:.4f}\n"
        self._afficher(texte)

    def _run_anomalies(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if not cols_num: return
        dlg = DlgAnomalies(self, cols_num)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        from sklearn.preprocessing import StandardScaler
        from scipy import stats as sp
        colonnes = dlg.resultat["colonnes"]
        methode  = dlg.resultat["methode"]
        tableau  = self.jeu_donnees.donnees[colonnes].dropna()
        X = StandardScaler().fit_transform(tableau.values)
        texte = (
            f"{'═'*60}\n"
            f"  DÉTECTION DES ANOMALIES – {methode.upper()}\n"
            f"{'═'*60}\n"
        )

        if methode == "isolation_forest":
            from sklearn.ensemble import IsolationForest
            contam = dlg.resultat["contamination"]
            iso    = IsolationForest(contamination=contam, random_state=42)
            etiquettes = iso.fit_predict(X)
            nb_an = (etiquettes == -1).sum()
            texte += (
                f"  Taux de contamination = {contam}\n"
                f"  Anomalies détectées : {nb_an} / {len(tableau)}"
                f"  ({nb_an/len(tableau)*100:.1f}%)\n"
                f"  Indices (10 premiers) : "
                f"{tableau.index[etiquettes == -1].tolist()[:10]}\n"
            )
        elif methode == "zscore":
            seuil_z = dlg.resultat["seuil_z"]
            z_scores = np.abs(sp.zscore(tableau))
            masque   = (z_scores > seuil_z).any(axis=1)
            nb_an    = masque.sum()
            texte += (
                f"  Seuil Z = {seuil_z}\n"
                f"  Anomalies détectées : {nb_an} / {len(tableau)}"
                f"  ({nb_an/len(tableau)*100:.1f}%)\n"
                f"\n  Par variable :\n"
            )
            for col, cnt in zip(colonnes, (z_scores > seuil_z).sum(axis=0)):
                texte += f"    {col:<35} {cnt} anomalie(s)\n"
        elif methode == "iqr":
            Q1, Q3 = tableau.quantile(.25), tableau.quantile(.75)
            IQR    = Q3 - Q1
            masque = (
                (tableau < Q1 - 1.5 * IQR) | (tableau > Q3 + 1.5 * IQR)
            ).any(axis=1)
            nb_an = masque.sum()
            texte += (
                f"  Anomalies détectées (IQR) : {nb_an} / {len(tableau)}"
                f"  ({nb_an/len(tableau)*100:.1f}%)\n"
                f"\n  Par variable :\n"
            )
            for col in colonnes:
                cnt = (
                    (tableau[col] < Q1[col] - 1.5 * IQR[col]) |
                    (tableau[col] > Q3[col] + 1.5 * IQR[col])
                ).sum()
                texte += f"    {col:<35} {cnt} anomalie(s)\n"
        self._afficher(texte)

    # ── Graphiques ────────────────────────────────────────────────

    def _run_graphique(self):
        if not self._verifier_donnees(): return
        cols_num = self.jeu_donnees.colonnes_numeriques()
        cols_cat = self.jeu_donnees.colonnes_categorielles()
        dlg = DlgGraphique(self, cols_num, cols_cat)
        self.wait_window(dlg)
        if dlg.resultat is None: return

        def _tracer():
            try:
                vis = Visualisation(
                    self.jeu_donnees,
                    style=dlg.resultat["style"],
                    palette=dlg.resultat["palette"]
                )
                type_g = dlg.resultat["type"]
                col_x  = dlg.resultat["col_x"]
                col_y  = dlg.resultat["col_y"]
                col_g  = dlg.resultat["col_grp"]
                fig    = None

                if type_g == "Histogramme":
                    fig = vis.histogramme(col_x)
                elif type_g == "Boîtes à moustaches":
                    fig = vis.boite_moustaches(grouper_par=col_g)
                elif type_g == "Nuage de points":
                    if col_y:
                        fig = vis.nuage_points(col_x, col_y, couleur_par=col_g)
                elif type_g == "Diagramme en barres":
                    cible = col_g or (cols_cat[0] if cols_cat else col_x)
                    fig = vis.diagramme_barres(cible)
                elif type_g == "Camembert":
                    cible = col_g or (cols_cat[0] if cols_cat else None)
                    if cible:
                        fig = vis.camembert(cible)
                elif type_g == "Carte de chaleur (corrélation)":
                    fig = vis.carte_chaleur()
                elif type_g == "Violon":
                    fig = vis.violon(col_x, col_x=col_g)
                elif type_g == "Densité KDE":
                    fig = vis.densite_kde()
                elif type_g == "Graphique Q-Q":
                    fig = vis.graphique_qq(col_x)
                elif type_g == "Série temporelle":
                    fig = vis.serie_temporelle(col_x)
                elif type_g == "Matrice de dispersion":
                    fig = vis.matrice_dispersion(teinte=col_g)
                elif type_g == "Barres empilées":
                    if len(cols_cat) >= 2:
                        fig = vis.barres_empilees(cols_cat[0], cols_cat[1])
                elif type_g == "Graphique à bulles":
                    if col_x and col_y:
                        col_z = [c for c in cols_num
                                  if c not in [col_x, col_y]]
                        if col_z:
                            fig = vis.graphique_bulles(
                                col_x, col_y, col_z[0], col_couleur=col_z[0]
                            )
                elif type_g == "Tableau de bord":
                    fig = vis.tableau_de_bord()

                if fig:
                    self.after(0, lambda f=fig: self._afficher_graphique(f))
            except Exception as err:
                self.after(0, lambda: messagebox.showerror(
                    "Erreur graphique", str(err)
                ))

        threading.Thread(target=_tracer, daemon=True).start()

    def _afficher_graphique(self, fig):
        for w in self._zone_graphique.winfo_children():
            w.destroy()
        self._figure_courante = fig
        canvas = FigureCanvasTkAgg(fig, master=self._zone_graphique)
        canvas.draw()
        barre_outils = NavigationToolbar2Tk(canvas, self._zone_graphique)
        barre_outils.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.onglets.select(2)
        self._statut.set("Graphique affiché.")

    # ── Rapport ───────────────────────────────────────────────────

    def _generer_rapport(self):
        if not self._verifier_donnees(): return
        chemin = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html")],
            initialfile="rapport_analyse.html"
        )
        if not chemin: return
        rapport = Rapport("Rapport d'analyse – DataAnalyst Pro")
        vis = Visualisation(self.jeu_donnees)
        cols_num = self.jeu_donnees.colonnes_numeriques()
        if cols_num:
            rapport.ajouter_visualisation(
                vis, "histogramme", {"colonne": cols_num[0]}
            )
        if len(cols_num) >= 2:
            rapport.ajouter_visualisation(vis, "carte_chaleur", {})
        rapport.ajouter_visualisation(vis, "tableau_de_bord", {})
        rapport.generer_html(chemin)
        messagebox.showinfo("Rapport généré",
                            f"Rapport HTML sauvegardé :\n{chemin}")


# ─────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationPrincipale()
    app.mainloop()
