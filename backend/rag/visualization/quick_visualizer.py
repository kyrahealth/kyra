#!/usr/bin/env python3
"""
Quick Vector Visualizer
A simplified version for quick 3D visualization of RAG vectors.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from chromadb import PersistentClient
import plotly.graph_objects as go
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

def quick_visualize():
    """Quick 3D visualization of RAG vectors."""
    print("🎨 Quick Vector Visualizer")
    print("=" * 30)
    
    # Setup paths
    rag_dir = Path(__file__).parent.parent
    chroma_dir = rag_dir / "chroma_db"
    output_dir = rag_dir / "visualization" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize ChromaDB client
    client = PersistentClient(path=str(chroma_dir))
    
    # Load collections
    collections_data = {}
    
    for collection_name in ["nhs_docs", "cancer_research_docs"]:
        try:
            collection = client.get_collection(collection_name)
            results = collection.get(include=['embeddings', 'metadatas', 'documents'])
            
            collections_data[collection_name] = {
                'embeddings': np.array(results['embeddings']),
                'metadatas': results['metadatas'],
                'documents': results['documents'],
                'ids': results['ids']
            }
            print(f"✅ Loaded {collection_name}: {len(results['embeddings'])} documents")
        except Exception as e:
            print(f"⚠️  Could not load {collection_name}: {e}")
    
    if not collections_data:
        print("❌ No collections found!")
        return
    
    # Combine all data
    all_embeddings = []
    all_sources = []
    all_titles = []
    all_urls = []
    
    for collection_name, data in collections_data.items():
        all_embeddings.extend(data['embeddings'])
        all_sources.extend([collection_name] * len(data['embeddings']))
        
        for metadata in data['metadatas']:
            all_titles.append(metadata.get('title', 'Unknown') if metadata else 'Unknown')
            all_urls.append(metadata.get('source', 'Unknown') if metadata else 'Unknown')
    
    embeddings_array = np.array(all_embeddings)
    print(f"📊 Total embeddings: {len(embeddings_array)}")
    
    # Reduce to 3D using PCA
    print("🔧 Reducing dimensions with PCA...")
    pca = PCA(n_components=3, random_state=42)
    reduced_embeddings = pca.fit_transform(embeddings_array)
    
    # Create DataFrame
    df = pd.DataFrame({
        'x': reduced_embeddings[:, 0],
        'y': reduced_embeddings[:, 1],
        'z': reduced_embeddings[:, 2],
        'source': all_sources,
        'title': all_titles,
        'url': all_urls
    })
    
    # Create 3D scatter plot
    print("📊 Creating 3D scatter plot...")
    fig = go.Figure()
    
    # Add points for each collection
    colors = {'nhs_docs': 'blue', 'cancer_research_docs': 'red'}
    
    for source in df['source'].unique():
        source_df = df[df['source'] == source]
        color = colors.get(source, 'gray')
        
        fig.add_trace(go.Scatter3d(
            x=source_df['x'],
            y=source_df['y'],
            z=source_df['z'],
            mode='markers',
            name=source.replace('_', ' ').title(),
            marker=dict(
                size=4,
                color=color,
                opacity=0.7
            ),
            text=source_df['title'],
            hovertemplate='<b>%{text}</b><br>Source: %{fullData.name}<br>URL: %{customdata}<extra></extra>',
            customdata=source_df['url']
        ))
    
    # Update layout
    fig.update_layout(
        title='3D Vector Visualization - NHS vs Cancer Research UK',
        scene=dict(
            xaxis_title='PCA Component 1',
            yaxis_title='PCA Component 2',
            zaxis_title='PCA Component 3'
        ),
        width=1000,
        height=800
    )
    
    # Save the plot
    output_file = output_dir / "quick_3d_visualization.html"
    fig.write_html(str(output_file))
    print(f"💾 Saved 3D visualization to: {output_file}")
    
    # Create 2D version
    print("📊 Creating 2D scatter plot...")
    pca_2d = PCA(n_components=2, random_state=42)
    reduced_2d = pca_2d.fit_transform(embeddings_array)
    
    df_2d = pd.DataFrame({
        'x': reduced_2d[:, 0],
        'y': reduced_2d[:, 1],
        'source': all_sources,
        'title': all_titles
    })
    
    fig_2d = px.scatter(
        df_2d,
        x='x',
        y='y',
        color='source',
        title='2D Vector Visualization - NHS vs Cancer Research UK',
        labels={'x': 'PCA Component 1', 'y': 'PCA Component 2'},
        hover_data=['title']
    )
    
    output_file_2d = output_dir / "quick_2d_visualization.html"
    fig_2d.write_html(str(output_file_2d))
    print(f"💾 Saved 2D visualization to: {output_file_2d}")
    
    # Print statistics
    print("\n📈 Statistics:")
    for source in df['source'].unique():
        count = len(df[df['source'] == source])
        print(f"  {source.replace('_', ' ').title()}: {count} documents")
    
    print(f"\n✅ Visualization complete!")
    print(f"📁 Check outputs in: {output_dir}")

if __name__ == "__main__":
    quick_visualize() 