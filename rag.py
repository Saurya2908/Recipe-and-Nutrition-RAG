import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

DB_PATH = os.path.join(os.path.dirname(__file__), "db")
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "recipes_sample.jsonl")

class RAGPipeline:
    def __init__(self):
        self.embedder = SentenceTransformer("./models/all-MiniLM-L6-v2",device="cpu")
        self.client = chromadb.PersistentClient(path=DB_PATH)
        self.col = self.client.get_or_create_collection(name="recipes", metadata={"hnsw:space":"cosine"})

    def build_index(self):
        # clear existing for idempotency in demo
        try:
            self.client.delete_collection("recipes")
        except Exception:
            pass
        self.col = self.client.get_or_create_collection(name="recipes", metadata={"hnsw:space":"cosine"})
        
        docs, ids, metas = [], [], []
        with open(DATA_PATH) as f:
            for line in f:
                r = json.loads(line)
                doc = self._to_doc(r)
                docs.append(doc)
                ids.append(r["id"])
                metas.append(self._sanitize_meta(r))   # ✅ sanitize metadata

        embeds = self.embedder.encode(docs, normalize_embeddings=True).tolist()
        self.col.add(embeddings=embeds, documents=docs, metadatas=metas, ids=ids)
        return len(ids)

    def _to_doc(self, r):
        n = r.get("nutrition_per_serving", {})
        as_text = f"""Title: {r.get('title','')}
Cuisine: {r.get('cuisine','')}
Ingredients: {', '.join(r.get('ingredients',[]))}
Tags: {', '.join(r.get('tags',[]))}
Nutrition per serving: calories {n.get('calories',0)}, protein {n.get('protein_g',0)} g, carbs {n.get('carbs_g',0)} g, fat {n.get('fat_g',0)} g, sodium {n.get('sodium_mg',0)} mg
Instructions: {r.get('instructions','')}
"""
        return as_text

    def _sanitize_meta(self, r):
        """Convert list values in metadata into comma-separated strings"""
        clean_meta = {}
        for k, v in r.items():
            if isinstance(v, list):
                clean_meta[k] = ", ".join(map(str, v))
            elif isinstance(v, dict):
                clean_meta[k] = json.dumps(v)  # keep dicts as JSON strings
            else:
                clean_meta[k] = v
        return clean_meta

    def search(self, query, top_k=5):
        if not query.strip():
            query = "simple healthy meal"
        q_embed = self.embedder.encode([query], normalize_embeddings=True).tolist()
        res = self.col.query(query_embeddings=q_embed, n_results=top_k*3)  # retrieve extra; filter later

        hits = []
        for doc, meta, id_ in zip(res["documents"][0], res["metadatas"][0], res["ids"][0]):
            meta = dict(meta)  # ensure json-serializable
            meta["id"] = id_
            hits.append(meta)
        return hits
