import pandas as pd
import ast
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# Step 1: Load the CSV
df = pd.read_csv("car_data.csv")

# Step 2: Convert perbedaan column from string to dict
df["perbedaan"] = df["perbedaan"].apply(ast.literal_eval)

# Step 3: Prepare embedding text
texts = []
metadata = []

for _, row in df.iterrows():
    perbedaan_dict = row["perbedaan"]
    perbedaan_str = "\n".join([f"- {k}: {v}" for k, v in perbedaan_dict.items()])

    text = f"""
Nama Mobil: {row['nama']}
Mobil {row['nama']} adalah kendaraan dari Isuzu yang memiliki spesifikasi dan keunggulan sebagai berikut.
Spesifikasi: {row['spesifikasi']}
Keunggulan: {row['keunggulan']}
Perbedaan:\n{perbedaan_str}
Link Brosur: {row['url brosur']}
"""
    texts.append(text)
    metadata.append(row.to_dict())

# Step 4: Create embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts, normalize_embeddings=True)

# Step 5: Save FAISS index
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(np.array(embeddings))

faiss.write_index(index, "car_index.bin")

# Step 6: Save metadata
with open("car_metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

print("✅ FAISS index and metadata saved successfully.")
