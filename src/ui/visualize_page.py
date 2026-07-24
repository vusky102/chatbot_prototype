import streamlit as st
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import plotly.graph_objects as go
from streamlit_agraph import agraph, Node, Edge, Config
from scipy.spatial.distance import cosine

from src.rag import RAGService

def render_visualize_page(service: RAGService):
    st.markdown("""
        <div class="admin-page-marker"></div>
        <div class="hero-section">
            <h1 class="hero-title">Visual Embeddings</h1>
            <p class="hero-subtitle" style="text-align: center; color: var(--text-secondary);">
                Explore the semantic high-dimensional space of your knowledge base.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="e.g. iphone 16 pro",
            label_visibility="collapsed",
        )
    
    with col2:
        k_val = st.number_input("Top K Matches", min_value=5, max_value=200, value=50, step=5)
        
    if not query:
        st.info("Enter a query above to visualize semantic relationships.")
        return
        
    with st.spinner("Fetching high-dimensional embeddings..."):
        # 1. Fetch vectors for the query and Top K chunks
        try:
            # Note: Langchain pinecone wrapper needs actual values.
            # We already have an interface to get include_values=True in PineconeVectorStore.
            # Our custom LangChainPineconeVectorStore calls it and injects it into _vector metadata.
            results = service.retriever.vectorstore.similarity_search_with_score(query, k=k_val, include_values=True)
        except Exception as e:
            st.error(f"Error fetching vectors: {e}")
            return
            
        if not results:
            st.warning("No matches found for query.")
            return

        # 2. Extract vectors and text
        query_vector = service.retriever.embeddings.embed_query(query)
        
        all_texts = [f'Query: "{query}"']
        all_embeddings = [query_vector]
        all_scores = [1.0] # Query to itself
        
        valid_results = []
        for doc, score in results:
            vec = doc.metadata.get("_vector")
            if vec is None:
                continue
            all_texts.append(doc.page_content[:200] + "...") # truncate for display
            all_embeddings.append(vec)
            all_scores.append(score)
            valid_results.append((doc, score))
            
        if len(all_embeddings) < 4:
            st.warning("Not enough valid vectors found to perform PCA/t-SNE or Network mapping. (Need at least 3).")
            return
            
        X = np.array(all_embeddings)

    st.markdown("---")
    
    view_mode = st.radio("Visualization Mode", ["3D PCA (Galaxy View)", "2D t-SNE", "Network Graph"], horizontal=True)
    
    # --- Sidebar Insights Panel ---
    with st.sidebar:
        st.subheader("Top Matches")
        for i, (doc, score) in enumerate(valid_results[:5]):
            st.markdown(f"**{i+1}.** Distance: `{1-score:.3f}`")
            st.caption(f"{doc.page_content[:100]}...")
            st.markdown("<hr style='margin: 0.5em 0'/>", unsafe_allow_html=True)
            
    # --- Main Visualization Arena ---
    if view_mode == "3D PCA (Galaxy View)":
        with st.spinner("Calculating PCA..."):
            pca = PCA(n_components=3, random_state=42)
            coords = pca.fit_transform(X)
            
        fig = go.Figure()
        
        # Add KB nodes
        fig.add_trace(go.Scatter3d(
            x=coords[1:, 0], y=coords[1:, 1], z=coords[1:, 2],
            mode='markers',
            marker=dict(
                size=8,
                color=all_scores[1:], # color by semantic similarity to query
                colorscale='Plasma', # vibrant cyan/magenta theme
                opacity=0.8,
                showscale=True,
                colorbar=dict(title="Similarity")
            ),
            text=all_texts[1:],
            hoverinfo='text',
            name='Knowledge Base'
        ))
        
        # Add Query Node (Index 0)
        fig.add_trace(go.Scatter3d(
            x=[coords[0, 0]], y=[coords[0, 1]], z=[coords[0, 2]],
            mode='markers',
            marker=dict(
                size=18,
                color='red',
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            text=[all_texts[0]],
            hoverinfo='text',
            name='Search Query'
        ))
        
        # Add Faint lines from query to top 3 matches
        for i in range(1, min(4, len(coords))):
            fig.add_trace(go.Scatter3d(
                x=[coords[0, 0], coords[i, 0]],
                y=[coords[0, 1], coords[i, 1]],
                z=[coords[0, 2], coords[i, 2]],
                mode='lines',
                line=dict(color='rgba(255,0,0,0.4)', width=2),
                hoverinfo='none',
                showlegend=False
            ))
            
        fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            scene=dict(
                xaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
                zaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
            ),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig, width="stretch")

    elif view_mode == "2D t-SNE":
        with st.spinner("Calculating t-SNE..."):
            perplexity = min(30, len(X) - 1)
            tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
            coords = tsne.fit_transform(X)
            
        fig = go.Figure()
        
        # Add KB nodes
        fig.add_trace(go.Scatter(
            x=coords[1:, 0], y=coords[1:, 1],
            mode='markers',
            marker=dict(
                size=12,
                color=all_scores[1:],
                colorscale='Plasma', 
                opacity=0.8,
                showscale=True
            ),
            text=all_texts[1:],
            hoverinfo='text',
            name='Knowledge Base'
        ))
        
        # Add Query Node (Index 0)
        fig.add_trace(go.Scatter(
            x=[coords[0, 0]], y=[coords[0, 1]],
            mode='markers',
            marker=dict(
                size=24,
                color='red',
                symbol='star'
            ),
            text=[all_texts[0]],
            hoverinfo='text',
            name='Search Query'
        ))
        
        fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        st.plotly_chart(fig, width="stretch")
        
    elif view_mode == "Network Graph":
        with st.spinner("Building Network Graph..."):
            nodes = []
            edges = []
            
            # Distance threshold for graph connections
            threshold = 0.8
            
            # Query Node
            nodes.append(Node(
                id="query",
                label="Search Query",
                size=30,
                color="red"
            ))
            
            # Add KB Nodes
            for i in range(1, len(all_texts)):
                nodes.append(Node(
                    id=str(i),
                    label=all_texts[i][:15] + "...",
                    title=all_texts[i], # Tooltip
                    size=15,
                    color="#00D2FF"
                ))
                
                # Check distance to query
                dist_to_query = cosine(all_embeddings[0], all_embeddings[i])
                if dist_to_query < threshold:
                    edges.append(Edge(
                        source="query",
                        target=str(i),
                        weight=1.0 - dist_to_query,
                        color="red"
                    ))
            
            # Check pairwise distance among top KB nodes to build clusters
            # For performance, only do pairwise on top 20
            cluster_limit = min(20, len(all_texts))
            for i in range(1, cluster_limit):
                for j in range(i + 1, cluster_limit):
                    dist = cosine(all_embeddings[i], all_embeddings[j])
                    if dist < (threshold - 0.1): # Stricter threshold for intra-KB edges
                        edges.append(Edge(
                            source=str(i),
                            target=str(j),
                            weight=1.0 - dist,
                            color="#333333"
                        ))
            
            config = Config(
                width="100%",
                height=600,
                directed=False,
                physics=True,
                hierarchical=False,
            )
            
            agraph(nodes=nodes, edges=edges, config=config)
