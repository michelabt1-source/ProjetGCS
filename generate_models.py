import pandas as pd
import os
import re

DOSSIER_TABLES = "tables"

TYPE_MAPPING = {
    "int64": "models.IntegerField",
    "float64": "models.FloatField",
    "object": "models.CharField",
    "bool": "models.BooleanField"
}


def nettoyer_nom(nom):
    nom = nom.replace(" ", "_")
    nom = nom.replace("-", "_")
    nom = re.sub(r'[^a-zA-Z0-9_]', '', nom)
    return nom

models_code = """
from django.db import models

"""

for fichier in os.listdir(DOSSIER_TABLES):

    if fichier.endswith(".XLS") or fichier.endswith(".xls"):

        chemin = os.path.join(DOSSIER_TABLES, fichier)

        try:
            df = pd.read_excel(chemin)

            nom_modele = nettoyer_nom(
                os.path.splitext(fichier)[0]
            )

            models_code += f"\n\nclass {nom_modele}(models.Model):\n"

            for col in df.columns:

                col_clean = nettoyer_nom(col)

                dtype = str(df[col].dtype)

                field_type = TYPE_MAPPING.get(
                    dtype,
                    "models.CharField"
                )

                if field_type == "models.CharField":
                    models_code += f"    {col_clean} = {field_type}(max_length=255, blank=True, null=True)\n"
                else:
                    models_code += f"    {col_clean} = {field_type}(blank=True, null=True)\n"

            models_code += """
    class Meta:
        managed = True

"""

        except Exception as e:
            print(f"Erreur sur {fichier}: {e}")

with open("generated_models.py", "w", encoding="utf-8") as f:
    f.write(models_code)

print("Modèles générés avec succès.")