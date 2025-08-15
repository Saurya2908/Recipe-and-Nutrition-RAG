from rag import RAGPipeline

if __name__ == "__main__":
    rag = RAGPipeline()
    total = rag.build_index()
    print(f"Indexed {total} recipes.")
