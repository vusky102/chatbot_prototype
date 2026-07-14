from openai import OpenAI
from os import getenv
from dotenv import load_dotenv
from scipy.spatial.distance import cosine
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

load_dotenv()

client = OpenAI(
    api_key=getenv("OPENAI_API_KEY"),
    base_url=getenv("OPENAI_API_BASEURL")
)

def embedding(texts):
    response = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    response_dict = response.model_dump()
    return [data['embedding'] for data in response_dict['data']]


def visualize_embeddings(a, b=None):
    """
    Visualize high-dimensional embeddings using t-SNE in a 2D scatter plot.
    
    Parameters:
    - a (list of str): Knowledge base text elements.
    - b (str, optional): Search query text. Defaults to None.
    """
    if not a:
        print("Knowledge base list 'a' cannot be empty.")
        return

    # Compute embeddings
    kb_embeddings = embedding(a)
    all_texts = list(a)
    all_embeddings = list(kb_embeddings)

    has_search = b is not None
    if has_search:
        search_emb = embedding([b])[0]
        # Insert search query at position 0
        all_texts = [b] + all_texts
        all_embeddings = [search_emb] + all_embeddings

    all_embeddings = np.array(all_embeddings)

    # Perform t-SNE reduction
    n_samples = len(all_texts)
    if n_samples < 2:
        print("Need at least 2 items to visualize relationships.")
        return

    perplexity = min(5, n_samples - 1)
    if perplexity < 1:
        perplexity = 1

    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42, init='pca', max_iter=1000)
    embeddings_2d = tsne.fit_transform(all_embeddings)

    # Create the scatter plot
    plt.figure(figsize=(10, 8))
    
    if has_search:
        # Plot database points (excluding index 0 which is the query point)
        plt.scatter(embeddings_2d[1:, 0], embeddings_2d[1:, 1], color='blue', label='Knowledge Base', s=100)
        # Plot search query point (index 0)
        plt.scatter(embeddings_2d[0, 0], embeddings_2d[0, 1], color='red', label=f'Search Query ("{b}")', marker='*', s=250)
    else:
        # Plot all knowledge base points
        plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], color='blue', label='Knowledge Base', s=100)

    # Annotate points with their query/database values
    for i, txt in enumerate(all_texts):
        plt.annotate(
            txt, 
            (embeddings_2d[i, 0], embeddings_2d[i, 1]), 
            xytext=(5, 3), 
            textcoords='offset points',
            fontsize=10
        )

    plt.title("t-SNE Embedding Relationships Visualization")
    plt.xlabel("t-SNE Dimension 1")
    plt.ylabel("t-SNE Dimension 2")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()


def visualize_embeddings_3d(a, b=None):
    """
    Visualize high-dimensional embeddings using PCA in a 3D scatter plot.
    
    Parameters:
    - a (list of str): Knowledge base text elements.
    - b (str, optional): Search query text. Defaults to None.
    """
    if not a:
        print("Knowledge base list 'a' cannot be empty.")
        return

    # Compute embeddings
    kb_embeddings = embedding(a)
    all_texts = list(a)
    all_embeddings = list(kb_embeddings)

    has_search = b is not None
    if has_search:
        search_emb = embedding([b])[0]
        # Insert search query at position 0
        all_texts = [b] + all_texts
        all_embeddings = [search_emb] + all_embeddings

    all_embeddings = np.array(all_embeddings)

    # Perform PCA reduction
    n_samples = len(all_texts)
    if n_samples < 3:
        print("Need at least 3 items to visualize relationships in 3D.")
        return

    pca = PCA(n_components=3, random_state=42)
    embeddings_3d = pca.fit_transform(all_embeddings)

    # Create the 3D scatter plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    if has_search:
        # Plot database points (excluding index 0 which is the query point)
        ax.scatter(embeddings_3d[1:, 0], embeddings_3d[1:, 1], embeddings_3d[1:, 2], 
                   color='blue', label='Knowledge Base', s=100, alpha=0.8)
        # Plot search query point (index 0)
        ax.scatter(embeddings_3d[0, 0], embeddings_3d[0, 1], embeddings_3d[0, 2], 
                   color='red', label=f'Search Query ("{b}")', marker='*', s=250)
    else:
        # Plot all knowledge base points
        ax.scatter(embeddings_3d[:, 0], embeddings_3d[:, 1], embeddings_3d[:, 2], 
                   color='blue', label='Knowledge Base', s=100, alpha=0.8)

    # Annotate points with their query/database values
    for i, txt in enumerate(all_texts):
        ax.text(
            embeddings_3d[i, 0], 
            embeddings_3d[i, 1], 
            embeddings_3d[i, 2], 
            txt, 
            fontsize=10
        )

    ax.set_title("3D PCA Embedding Relationships Visualization")
    ax.set_xlabel("PCA Dimension 1")
    ax.set_ylabel("PCA Dimension 2")
    ax.set_zlabel("PCA Dimension 3")
    ax.legend()
    plt.show()


if __name__ == "__main__":
    with open("docs/Training_data_GD4/output/Public_035/Public_035.txt", "r", encoding="utf-8") as f:
        text = f.read()

    #datacamp example
    search_text = "iphone 16 pro"
    search_embedding = embedding([search_text])[0]

    kb= ["technology","biology","chemistry","physics","math","chip","apple","mobile","essential stuff","test"]
    kb_embedding = embedding(kb)

    distances = [cosine(search_embedding, kb_emb) for kb_emb in kb_embedding]
    

    # Visualise the relationships using the new function
    visualize_embeddings(kb)
    visualize_embeddings(kb, search_text)

    # Visualise the relationships in 3D
    visualize_embeddings_3d(kb)
    visualize_embeddings_3d(kb, search_text)
    
    min_distance = np.argmin(distances)
    print(distances)
    print(min_distance)
    print(kb[min_distance])
