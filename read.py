import pandas as pd
df = pd.read_csv(r"C:\Projets_Data\ProjetFinal\vente\Person.csv",
                  sep=r"\+\|", header=None, engine="python", nrows=5)
print(df.shape)
print(df)