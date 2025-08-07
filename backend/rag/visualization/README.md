# Vector Visualization Tools

This directory contains tools for visualizing the embedded vectors from your RAG system in 3D space.

## Overview

The visualization tools help you understand:
- How your documents are distributed in vector space
- The relationship between NHS and Cancer Research UK content
- Clustering patterns in your medical knowledge base
- The effectiveness of your embedding model

## Files

### `quick_visualizer.py`
A simplified visualizer for immediate use. Creates basic 3D and 2D scatter plots.

### `vector_visualizer.py`
A comprehensive visualization tool with advanced features:
- Multiple dimensionality reduction methods (PCA, t-SNE, UMAP)
- Cluster analysis
- Statistics dashboard
- Interactive plots

### `requirements.txt`
Dependencies needed for visualization.

## Quick Start

### 1. Install Dependencies
```bash
cd backend/rag/visualization
pip install -r requirements.txt
```

### 2. Run Quick Visualizer
```bash
python quick_visualizer.py
```

This will create:
- `outputs/quick_3d_visualization.html` - Interactive 3D scatter plot
- `outputs/quick_2d_visualization.html` - Interactive 2D scatter plot

### 3. Run Advanced Visualizer
```bash
python vector_visualizer.py
```

This will create comprehensive visualizations including:
- 3D scatter plots with different reduction methods
- 2D scatter plots
- Statistics dashboard
- Cluster analysis
- Detailed statistics JSON file

## Understanding the Visualizations

### Color Coding
- **Blue points**: NHS documents
- **Red points**: Cancer Research UK documents

### What You Can Learn

1. **Document Distribution**
   - Are NHS and Cancer Research UK documents well-separated?
   - Are there clear clusters of related content?

2. **Content Overlap**
   - Do similar topics from different sources cluster together?
   - Are there gaps in your knowledge base?

3. **Embedding Quality**
   - Are similar documents close together?
   - Are different topics well-separated?

### Interacting with Plots

1. **3D Plots**:
   - Rotate by dragging
   - Zoom with scroll wheel
   - Hover for document details

2. **2D Plots**:
   - Zoom and pan
   - Click legend items to show/hide collections
   - Hover for document information

## Dimensionality Reduction Methods

### PCA (Principal Component Analysis)
- **Pros**: Fast, preserves global structure
- **Cons**: May miss local patterns
- **Best for**: Quick overview, large datasets

### t-SNE (t-Distributed Stochastic Neighbor Embedding)
- **Pros**: Preserves local structure, good for clustering
- **Cons**: Slower, doesn't preserve global structure
- **Best for**: Finding clusters, smaller datasets

### UMAP (Uniform Manifold Approximation and Projection)
- **Pros**: Fast, preserves both local and global structure
- **Cons**: More parameters to tune
- **Best for**: General purpose, medium to large datasets

## Output Files

### HTML Files
- Interactive plots you can open in any web browser
- Include hover information and zoom/pan controls
- Can be shared or embedded in web applications

### JSON Files
- Statistics and metadata for further analysis
- Can be used for custom visualizations

## Troubleshooting

### Common Issues

1. **No collections found**
   ```
   ⚠️ Could not load nhs_docs: Collection not found
   ```
   **Solution**: Make sure you've run the indexing process first.

2. **Memory errors**
   ```
   MemoryError: Unable to allocate array
   ```
   **Solution**: Use the quick visualizer or reduce the number of documents.

3. **Missing dependencies**
   ```
   ModuleNotFoundError: No module named 'plotly'
   ```
   **Solution**: Install dependencies with `pip install -r requirements.txt`

### Performance Tips

1. **For large datasets**: Use PCA instead of t-SNE
2. **For quick preview**: Use the quick visualizer
3. **For detailed analysis**: Use the full visualizer

## Customization

### Modifying Colors
Edit the colors in `quick_visualizer.py`:
```python
colors = {'nhs_docs': 'blue', 'cancer_research_docs': 'red'}
```

### Adding New Collections
Add new collection names to the list:
```python
for collection_name in ["nhs_docs", "cancer_research_docs", "new_collection"]:
```

### Changing Plot Styles
Modify the plot parameters in the visualization functions:
```python
marker=dict(
    size=4,  # Change point size
    color=color,
    opacity=0.7  # Change transparency
)
```

## Advanced Usage

### Custom Analysis
You can import the visualizer classes for custom analysis:

```python
from vector_visualizer import VectorVisualizer

visualizer = VectorVisualizer()
visualizer.load_collections()
visualizer.extract_embeddings_and_metadata()
# ... custom analysis
```

### Batch Processing
Create scripts to generate visualizations for different subsets of your data:

```python
# Analyze only cancer-related documents
cancer_only = df[df['source'] == 'cancer_research_docs']
# ... create custom visualization
```

## Future Enhancements

Potential improvements:
1. **Real-time visualization**: Live updates as new documents are indexed
2. **Query visualization**: Show where user queries fall in vector space
3. **Similarity networks**: Graph-based visualization of document relationships
4. **Topic modeling**: Color points by discovered topics
5. **Temporal analysis**: Show how knowledge base evolves over time

The visualization tools help you understand and optimize your RAG system's knowledge representation! 