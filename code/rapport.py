"""
rapport.py
==========
Classe Rapport – agrège des Analyse (agrégation) et compose des Visualisation (composition).
Génère des exports HTML.

Relations UML :
  Rapport 1 ◇── 1..* Analyse       (agrégation)
  Rapport 1 ◆── 1..* Visualisation  (composition)
"""

from __future__ import annotations
import base64
import datetime
import io
import os
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd

from analyse import Analyse
from visualisation import Visualisation


class Rapport:
    """
    Génère un rapport HTML complet à partir d'analyses et de graphiques.
    """

    def __init__(self, titre: str = "Rapport d'analyse de données"):
        self.titre: str = titre
        self.analyses: List[Analyse] = []           # agrégation
        self.visualisations: List[Visualisation] = []   # composition
        self._sections: List[dict] = []
        self._date_creation = datetime.datetime.now()

    # ── Ajout de contenu ──────────────────────────────────────────

    def ajouter_analyse(self, analyse: Analyse) -> None:
        """Ajoute une analyse au rapport (agrégation)."""
        self.analyses.append(analyse)
        self._sections.append({"type": "analyse", "contenu": analyse})

    def ajouter_visualisation(self, visualisation: Visualisation,
                               methode: str,
                               parametres: Optional[dict] = None) -> None:
        """Ajoute une visualisation au rapport (composition)."""
        self.visualisations.append(visualisation)
        self._sections.append({
            "type":       "visualisation",
            "contenu":    visualisation,
            "methode":    methode,
            "parametres": parametres or {},
        })

    def ajouter_section(self, titre: str, texte: str) -> None:
        """Ajoute une section texte libre."""
        self._sections.append({"type": "texte", "titre": titre, "texte": texte})

    # ── Génération HTML ───────────────────────────────────────────

    def generer_html(self, chemin: str = "rapport.html") -> str:
        """Génère le rapport complet au format HTML."""
        corps_html = ""

        for section in self._sections:
            if section["type"] == "texte":
                corps_html += (
                    f"<h2>{section['titre']}</h2>"
                    f"<p>{section['texte']}</p>"
                )

            elif section["type"] == "analyse":
                analyse = section["contenu"]
                corps_html += f"<h2>📊 {analyse.nom}</h2>"
                corps_html += (
                    f"<p><em>Exécuté le {analyse.date_execution}</em></p>"
                )
                for cle, valeur in analyse.resultats.items():
                    corps_html += f"<h3>{cle}</h3>"
                    if isinstance(valeur, pd.DataFrame):
                        corps_html += valeur.to_html(
                            classes="tableau", border=0,
                            float_format="%.4f"
                        )
                    elif isinstance(valeur, dict):
                        corps_html += "<ul>"
                        for k, v in valeur.items():
                            corps_html += f"<li><b>{k}</b> : {v}</li>"
                        corps_html += "</ul>"
                    else:
                        corps_html += f"<p>{valeur}</p>"

            elif section["type"] == "visualisation":
                vis = section["contenu"]
                methode = section["methode"]
                parametres = section["parametres"]
                try:
                    fig = getattr(vis, methode)(**parametres)
                    tampon = io.BytesIO()
                    fig.savefig(tampon, format="png",
                                bbox_inches="tight", dpi=100)
                    tampon.seek(0)
                    img_b64 = base64.b64encode(tampon.read()).decode()
                    plt.close(fig)
                    corps_html += (
                        f'<img src="data:image/png;base64,{img_b64}" '
                        f'style="max-width:100%;margin:16px 0;'
                        f'border-radius:8px;'
                        f'box-shadow:0 2px 8px rgba(0,0,0,.1)"/>'
                    )
                except Exception as erreur:
                    corps_html += (
                        f"<p style='color:red'>Erreur graphique : {erreur}</p>"
                    )

        contenu_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{self.titre}</title>
<style>
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    margin: 0;
    background: #f4f6f9;
    color: #2d3748;
  }}
  .entete {{
    background: linear-gradient(135deg, #2b6cb0, #4299e1);
    color: #fff;
    padding: 40px;
    text-align: center;
  }}
  .entete h1 {{ margin: 0; font-size: 2rem; }}
  .entete p  {{ margin: 8px 0 0; opacity: .85; }}
  .contenu {{
    max-width: 960px;
    margin: 32px auto;
    padding: 0 24px 60px;
  }}
  h2 {{
    color: #2b6cb0;
    border-bottom: 2px solid #bee3f8;
    padding-bottom: 6px;
    margin-top: 40px;
  }}
  h3 {{ color: #4a5568; margin-top: 24px; }}
  .tableau {{
    width: 100%;
    border-collapse: collapse;
    font-size: .85rem;
  }}
  .tableau th {{
    background: #ebf8ff;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 2px solid #90cdf4;
  }}
  .tableau td {{
    padding: 6px 12px;
    border-bottom: 1px solid #e2e8f0;
  }}
  .tableau tr:hover td {{ background: #f0f4f8; }}
  img {{ border-radius: 8px; }}
  ul {{ padding-left: 24px; line-height: 1.9; }}
  footer {{
    text-align: center;
    padding: 24px;
    color: #718096;
    font-size: .8rem;
  }}
</style>
</head>
<body>
<div class="entete">
  <h1>{self.titre}</h1>
  <p>Généré le {self._date_creation.strftime('%d/%m/%Y à %H:%M')}</p>
</div>
<div class="contenu">
{corps_html}
</div>
<footer>
  DataAnalyst Pro – Logiciel d'analyse de données – Master 1 IFOAD
</footer>
</body>
</html>"""

        os.makedirs(
            os.path.dirname(chemin) if os.path.dirname(chemin) else ".",
            exist_ok=True
        )
        with open(chemin, "w", encoding="utf-8") as fichier:
            fichier.write(contenu_html)
        return chemin

    def __repr__(self) -> str:
        return (
            f"Rapport('{self.titre}', "
            f"{len(self.analyses)} analyses, "
            f"{len(self.visualisations)} visualisations)"
        )
