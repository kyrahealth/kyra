#!/usr/bin/env python3
"""
3D Vector Visualization Tool
Visualizes embedded vectors from NHS and Cancer Research UK collections in 3D space.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from chromadb import PersistentClient
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

class VectorVisualizer:
    """3D Vector Visualization for RAG Collections"""
    
    def __init__(self, rag_dir: str = None):
        """Initialize the visualizer with RAG directory path."""
        if rag_dir is None:
            rag_dir = Path(__file__).parent.parent
        
        self.rag_dir = Path(rag_dir)
        self.chroma_dir = self.rag_dir / "chroma_db"
        self.output_dir = self.rag_dir / "visualization" / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = PersistentClient(path=str(self.chroma_dir))
        
        # Collections
        self.nhs_collection = None
        self.cancer_collection = None
        
        # Data storage
        self.nhs_data = None
        self.cancer_data = None
        self.combined_data = None
        
    def load_collections(self):
        """Load both NHS and Cancer Research UK collections."""
        print("🔍 Loading collections...")
        
        try:
            self.nhs_collection = self.client.get_collection("nhs_docs")
            nhs_count = self.nhs_collection.count()
            print(f"✅ NHS collection loaded: {nhs_count} documents")
        except Exception as e:
            print(f"⚠️  NHS collection not found: {e}")
            self.nhs_collection = None
        
        try:
            self.cancer_collection = self.client.get_collection("cancer_research_docs")
            cancer_count = self.cancer_collection.count()
            print(f"✅ Cancer Research UK collection loaded: {cancer_count} documents")
        except Exception as e:
            print(f"⚠️  Cancer Research UK collection not found: {e}")
            self.cancer_collection = None
    
    def extract_embeddings_and_metadata(self):
        """Extract embeddings and metadata from collections."""
        print("📊 Extracting embeddings and metadata...")
        
        # Extract NHS data
        if self.nhs_collection:
            nhs_results = self.nhs_collection.get(include=['embeddings', 'metadatas', 'documents'])
            self.nhs_data = {
                'embeddings': np.array(nhs_results['embeddings']),
                'metadatas': nhs_results['metadatas'],
                'documents': nhs_results['documents'],
                'ids': nhs_results['ids']
            }
            print(f"📈 NHS: {len(self.nhs_data['embeddings'])} embeddings extracted")
        
        # Extract Cancer Research UK data
        if self.cancer_collection:
            cancer_results = self.cancer_collection.get(include=['embeddings', 'metadatas', 'documents'])
            self.cancer_data = {
                'embeddings': np.array(cancer_results['embeddings']),
                'metadatas': cancer_results['metadatas'],
                'documents': cancer_results['documents'],
                'ids': cancer_results['ids']
            }
            print(f"📈 Cancer Research UK: {len(self.cancer_data['embeddings'])} embeddings extracted")
    
    def combine_data(self):
        """Combine data from both collections for visualization."""
        print("🔄 Combining data...")
        
        combined_embeddings = []
        combined_metadatas = []
        combined_documents = []
        combined_ids = []
        combined_sources = []
        
        # Add NHS data
        if self.nhs_data:
            combined_embeddings.extend(self.nhs_data['embeddings'])
            combined_metadatas.extend(self.nhs_data['metadatas'])
            combined_documents.extend(self.nhs_data['documents'])
            combined_ids.extend(self.nhs_data['ids'])
            combined_sources.extend(['NHS'] * len(self.nhs_data['embeddings']))
        
        # Add Cancer Research UK data
        if self.cancer_data:
            combined_embeddings.extend(self.cancer_data['embeddings'])
            combined_metadatas.extend(self.cancer_data['metadatas'])
            combined_documents.extend(self.cancer_data['documents'])
            combined_ids.extend(self.cancer_data['ids'])
            combined_sources.extend(['Cancer Research UK'] * len(self.cancer_data['embeddings']))
        
        self.combined_data = {
            'embeddings': np.array(combined_embeddings),
            'metadatas': combined_metadatas,
            'documents': combined_documents,
            'ids': combined_ids,
            'sources': combined_sources
        }
        
        print(f"📊 Combined: {len(self.combined_data['embeddings'])} total embeddings")
    
    def reduce_dimensions(self, method: str = 'pca', n_components: int = 3):
        """Reduce high-dimensional embeddings to 3D for visualization."""
        print(f"🔧 Reducing dimensions using {method.upper()}...")
        
        embeddings = self.combined_data['embeddings']
        
        if method.lower() == 'pca':
            reducer = PCA(n_components=n_components, random_state=42)
        elif method.lower() == 'tsne':
            reducer = TSNE(n_components=n_components, random_state=42, perplexity=min(30, len(embeddings)-1))
        elif method.lower() == 'umap':
            reducer = umap.UMAP(n_components=n_components, random_state=42)
        else:
            raise ValueError(f"Unknown reduction method: {method}")
        
        reduced_embeddings = reducer.fit_transform(embeddings)
        
        # Add reduced coordinates to combined data
        self.combined_data['reduced_embeddings'] = reduced_embeddings
        self.combined_data['reduction_method'] = method
        
        print(f"✅ Reduced to {n_components}D using {method.upper()}")
        return reduced_embeddings
    
    def create_3d_scatter_plot(self, method: str = 'pca'):
        """Create an interactive 3D scatter plot."""
        print(f"📊 Creating 3D scatter plot with {method.upper()}...")
        
        # Reduce dimensions
        reduced_embeddings = self.reduce_dimensions(method)
        
        # Create DataFrame for plotting
        df = pd.DataFrame({
            'x': reduced_embeddings[:, 0],
            'y': reduced_embeddings[:, 1],
            'z': reduced_embeddings[:, 2],
            'source': self.combined_data['sources'],
            'title': [meta.get('title', 'Unknown') if meta else 'Unknown' for meta in self.combined_data['metadatas']],
            'url': [meta.get('source', 'Unknown') if meta else 'Unknown' for meta in self.combined_data['metadatas']]
        })
        
        # Create 3D scatter plot
        fig = go.Figure()
        
        # Add NHS points
        nhs_df = df[df['source'] == 'NHS']
        if not nhs_df.empty:
            fig.add_trace(go.Scatter3d(
                x=nhs_df['x'],
                y=nhs_df['y'],
                z=nhs_df['z'],
                mode='markers',
                name='NHS',
                marker=dict(
                    size=4,
                    color='blue',
                    opacity=0.7
                ),
                text=nhs_df['title'],
                hovertemplate='<b>%{text}</b><br>Source: NHS<br>URL: %{customdata}<extra></extra>',
                customdata=nhs_df['url']
            ))
        
        # Add Cancer Research UK points
        cancer_df = df[df['source'] == 'Cancer Research UK']
        if not cancer_df.empty:
            fig.add_trace(go.Scatter3d(
                x=cancer_df['x'],
                y=cancer_df['y'],
                z=cancer_df['z'],
                mode='markers',
                name='Cancer Research UK',
                marker=dict(
                    size=4,
                    color='red',
                    opacity=0.7
                ),
                text=cancer_df['title'],
                hovertemplate='<b>%{text}</b><br>Source: Cancer Research UK<br>URL: %{customdata}<extra></extra>',
                customdata=cancer_df['url']
            ))
        
        # Update layout
        fig.update_layout(
            title=f'3D Vector Visualization ({method.upper()}) - NHS vs Cancer Research UK',
            scene=dict(
                xaxis_title=f'{method.upper()} Component 1',
                yaxis_title=f'{method.upper()} Component 2',
                zaxis_title=f'{method.upper()} Component 3'
            ),
            width=1000,
            height=800
        )
        
        # Save the plot
        output_file = self.output_dir / f"3d_scatter_{method}.html"
        fig.write_html(str(output_file))
        print(f"💾 Saved 3D scatter plot to: {output_file}")
        
        return fig
    
    def create_2d_scatter_plot(self, method: str = 'pca'):
        """Create a 2D scatter plot for better overview."""
        print(f"📊 Creating 2D scatter plot with {method.upper()}...")
        
        # Reduce dimensions to 2D
        reduced_embeddings = self.reduce_dimensions(method, n_components=2)
        
        # Create DataFrame
        df = pd.DataFrame({
            'x': reduced_embeddings[:, 0],
            'y': reduced_embeddings[:, 1],
            'source': self.combined_data['sources'],
            'title': [meta.get('title', 'Unknown') if meta else 'Unknown' for meta in self.combined_data['metadatas']],
            'url': [meta.get('source', 'Unknown') if meta else 'Unknown' for meta in self.combined_data['metadatas']]
        })
        
        # Create 2D scatter plot
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color='source',
            title=f'2D Vector Visualization ({method.upper()}) - NHS vs Cancer Research UK',
            labels={'x': f'{method.upper()} Component 1', 'y': f'{method.upper()} Component 2'},
            hover_data=['title', 'url']
        )
        
        # Update layout
        fig.update_layout(
            width=1000,
            height=600
        )
        
        # Save the plot
        output_file = self.output_dir / f"2d_scatter_{method}.html"
        fig.write_html(str(output_file))
        print(f"💾 Saved 2D scatter plot to: {output_file}")
        
        return fig
    
    def create_comparison_plots(self):
        """Create comparison plots using different reduction methods."""
        print("📊 Creating comparison plots...")
        
        methods = ['pca', 'tsne', 'umap']
        figs = []
        
        for method in methods:
            try:
                # 3D plot
                fig_3d = self.create_3d_scatter_plot(method)
                figs.append(fig_3d)
                
                # 2D plot
                fig_2d = self.create_2d_scatter_plot(method)
                figs.append(fig_2d)
                
            except Exception as e:
                print(f"⚠️  Error creating {method.upper()} plot: {e}")
        
        return figs
    
    def create_statistics_dashboard(self):
        """Create a statistics dashboard."""
        print("📊 Creating statistics dashboard...")
        
        # Calculate statistics
        stats = {
            'total_documents': len(self.combined_data['embeddings']),
            'nhs_documents': sum(1 for source in self.combined_data['sources'] if source == 'NHS'),
            'cancer_documents': sum(1 for source in self.combined_data['sources'] if source == 'Cancer Research UK'),
            'embedding_dimensions': self.combined_data['embeddings'].shape[1],
            'unique_titles': len(set(meta.get('title', 'Unknown') for meta in self.combined_data['metadatas'] if meta))
        }
        
        # Create statistics visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Document Distribution', 'Collection Sizes', 'Embedding Dimensions', 'Unique Titles'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # Pie chart for document distribution
        fig.add_trace(
            go.Pie(
                labels=['NHS', 'Cancer Research UK'],
                values=[stats['nhs_documents'], stats['cancer_documents']],
                name="Document Distribution"
            ),
            row=1, col=1
        )
        
        # Bar chart for collection sizes
        fig.add_trace(
            go.Bar(
                x=['NHS', 'Cancer Research UK'],
                y=[stats['nhs_documents'], stats['cancer_documents']],
                name="Collection Sizes"
            ),
            row=1, col=2
        )
        
        # Indicator for embedding dimensions
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=stats['embedding_dimensions'],
                title={"text": "Embedding Dimensions"},
                domain={'row': 0, 'column': 0}
            ),
            row=2, col=1
        )
        
        # Indicator for unique titles
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=stats['unique_titles'],
                title={"text": "Unique Titles"},
                domain={'row': 0, 'column': 1}
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="RAG Collections Statistics Dashboard",
            height=800
        )
        
        # Save dashboard
        output_file = self.output_dir / "statistics_dashboard.html"
        fig.write_html(str(output_file))
        print(f"💾 Saved statistics dashboard to: {output_file}")
        
        # Save statistics as JSON
        stats_file = self.output_dir / "statistics.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"💾 Saved statistics to: {stats_file}")
        
        return fig, stats
    
    def create_cluster_analysis(self):
        """Perform and visualize cluster analysis."""
        print("🔍 Performing cluster analysis...")
        
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        
        # Use PCA for clustering
        reduced_embeddings = self.reduce_dimensions('pca', n_components=10)
        
        # Try different numbers of clusters
        n_clusters_range = range(2, min(11, len(reduced_embeddings)))
        silhouette_scores = []
        
        for n_clusters in n_clusters_range:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(reduced_embeddings)
            score = silhouette_score(reduced_embeddings, cluster_labels)
            silhouette_scores.append(score)
        
        # Find optimal number of clusters
        optimal_clusters = n_clusters_range[np.argmax(silhouette_scores)]
        
        # Perform clustering with optimal number
        kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(reduced_embeddings)
        
        # Add cluster labels to data
        self.combined_data['cluster_labels'] = cluster_labels
        
        # Create cluster visualization
        df = pd.DataFrame({
            'x': reduced_embeddings[:, 0],
            'y': reduced_embeddings[:, 1],
            'z': reduced_embeddings[:, 2],
            'cluster': cluster_labels,
            'source': self.combined_data['sources'],
            'title': [meta.get('title', 'Unknown') if meta else 'Unknown' for meta in self.combined_data['metadatas']]
        })
        
        # Create 3D cluster plot
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            color='cluster',
            title=f'Cluster Analysis (Optimal Clusters: {optimal_clusters})',
            labels={'x': 'PCA Component 1', 'y': 'PCA Component 2', 'z': 'PCA Component 3'},
            hover_data=['title', 'source']
        )
        
        # Save cluster plot
        output_file = self.output_dir / "cluster_analysis.html"
        fig.write_html(str(output_file))
        print(f"💾 Saved cluster analysis to: {output_file}")
        
        return fig, optimal_clusters
    
    def generate_all_visualizations(self):
        """Generate all visualizations."""
        print("🎨 Generating all visualizations...")
        
        # Load and prepare data
        self.load_collections()
        self.extract_embeddings_and_metadata()
        self.combine_data()
        
        # Generate all plots
        self.create_comparison_plots()
        self.create_statistics_dashboard()
        self.create_cluster_analysis()
        
        print("✅ All visualizations generated!")
        print(f"📁 Output directory: {self.output_dir}")

def main():
    """Main function to run the visualizer."""
    print("🎨 3D Vector Visualizer for RAG Collections")
    print("=" * 50)
    
    # Initialize visualizer
    visualizer = VectorVisualizer()
    
    # Generate all visualizations
    visualizer.generate_all_visualizations()
    
    print("\n🎉 Visualization complete!")
    print("📊 Check the output directory for interactive HTML files:")

if __name__ == "__main__":
    main() 