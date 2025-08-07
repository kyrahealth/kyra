"""RAG helper functions with hybrid GPT-4o conversation system."""
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import openai
from chromadb import PersistentClient
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from dotenv import load_dotenv
load_dotenv(override=True)
# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SIM_THRESHOLD: float = 0.30  # minimum similarity to use RAG knowledge

INDEX_DIR = (
    Path(__file__)
    .resolve()
    .parent.parent  # → backend/app/
    / "../rag/chroma_db"  # backend/rag/chroma_db
).resolve()

# --------------------------------------------------------------------------- #
# Initialise Chroma-powered query engine (loads once per worker)
# --------------------------------------------------------------------------- #
chroma_client = PersistentClient(path=str(INDEX_DIR))

# Try to get both collections - NHS and Cancer Research UK
nhs_collection = chroma_client.get_or_create_collection("nhs_docs")
cancer_collection = chroma_client.get_or_create_collection("cancer_research_docs")

# Create vector stores for both collections
nhs_store = ChromaVectorStore(chroma_collection=nhs_collection, stores_text=True)
cancer_store = ChromaVectorStore(chroma_collection=cancer_collection, stores_text=True)

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)  # Keep for RAG retrieval

# Create indices for both collections
nhs_index = VectorStoreIndex.from_vector_store(nhs_store)
cancer_index = VectorStoreIndex.from_vector_store(cancer_store)

# Create query engines for both collections
nhs_query_engine = nhs_index.as_query_engine(similarity_top_k=3)
cancer_query_engine = cancer_index.as_query_engine(similarity_top_k=3)

# --------------------------------------------------------------------------- #
# Medical question classifier
# --------------------------------------------------------------------------- #
MEDICAL_CLASSIFIER_PROMPT = """
You are a classifier that determines if a question is medical/health-related or general conversation.

Return only "MEDICAL" or "GENERAL".

Examples:
"Hello" -> GENERAL
"How are you?" -> GENERAL  
"What's the weather like?" -> GENERAL
"Tell me a joke" -> GENERAL
"What is diabetes?" -> MEDICAL
"I have a headache, what should I do?" -> MEDICAL
"How to treat high blood pressure?" -> MEDICAL
"What are the symptoms of flu?" -> MEDICAL
"My medication side effects" -> MEDICAL
"Cancer treatment options" -> MEDICAL

Question: "{question}"
Classification:"""

def is_medical_question(question: str) -> bool:
    """Classify if a question is medical/health-related using GPT-4o"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": MEDICAL_CLASSIFIER_PROMPT.format(question=question)}
            ],
            max_tokens=10,
            temperature=0
        )
        
        classification = response.choices[0].message.content.strip().upper()
        return classification == "MEDICAL"
    except Exception as e:
        print(f"[DEBUG] Classification error: {e}")
        # Default to medical if classifier fails - safer approach
        return True

# --------------------------------------------------------------------------- #
# RAG retrieval function
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# RAG retrieval function with exponential weighting
# --------------------------------------------------------------------------- #
def get_rag_context_weighted(
    current_query: str, 
    conversation_history: Optional[List[Dict[str, str]]] = None,
    primary_weight: float = 0.8,
    context_weight: float = 0.2
) -> Tuple[Optional[str], float, List[str]]:
    """
    Get RAG context using exponentially weighted queries from both NHS and Cancer Research UK collections.
    Prioritizes the current question while considering recent context.
    
    Args:
        current_query: The current user question
        conversation_history: Recent conversation messages
        primary_weight: Weight for current query (0.8 = 80% focus on current question)
        context_weight: Weight for context query (0.2 = 20% focus on context)
    
    Returns:
        (context_text | None, similarity_score, sources)
    """
    print(f"[DEBUG] RAG: Using weighted approach - primary: {primary_weight}, context: {context_weight}")
    
    # Search both collections with current query
    all_results = []
    best_score = 0.0
    
    # Search NHS collection
    try:
        nhs_res = nhs_query_engine.query(current_query)
        if nhs_res.source_nodes:
            for node in nhs_res.source_nodes:
                if node.score:
                    all_results.append({
                        'text': node.node.text,
                        'score': node.score,
                        'source': node.node.metadata.get("source", ""),
                        'collection': 'nhs'
                    })
                    best_score = max(best_score, node.score)
        print(f"[DEBUG] RAG: NHS search found {len(nhs_res.source_nodes)} results")
    except Exception as exc:
        print(f"[DEBUG] RAG: NHS search error: {exc}")
    
    # Search Cancer Research UK collection
    try:
        cancer_res = cancer_query_engine.query(current_query)
        if cancer_res.source_nodes:
            for node in cancer_res.source_nodes:
                if node.score:
                    all_results.append({
                        'text': node.node.text,
                        'score': node.score,
                        'source': node.node.metadata.get("source", ""),
                        'collection': 'cancer_research'
                    })
                    best_score = max(best_score, node.score)
        print(f"[DEBUG] RAG: Cancer Research search found {len(cancer_res.source_nodes)} results")
    except Exception as exc:
        print(f"[DEBUG] RAG: Cancer Research search error: {exc}")
    
    # If nothing retrieved from either collection
    if not all_results:
        print(f"[DEBUG] RAG: No results from either collection")
        return None, 0.0, []
    
    # Sort results by score and take top results
    all_results.sort(key=lambda x: x['score'], reverse=True)
    top_results = all_results[:6]  # Take top 6 results total
    
    # Build contextual query if we have conversation history
    contextual_score = 0.0
    if conversation_history and len(conversation_history) > 0:
        try:
            # Build lightweight contextual query (last 2 messages max)
            recent_context = []
            for msg in conversation_history[-2:]:  # Only last 2 messages for context
                recent_context.append(f"{msg['role']}: {msg['content']}")
            
            contextual_query = f"Context: {' | '.join(recent_context)} | Current: {current_query}"
            print(f"[DEBUG] RAG: Contextual search with recent history")
            
            # Search both collections with contextual query
            context_results = []
            
            try:
                nhs_context_res = nhs_query_engine.query(contextual_query)
                if nhs_context_res.source_nodes:
                    context_results.extend([node.score or 0.0 for node in nhs_context_res.source_nodes])
            except:
                pass
            
            try:
                cancer_context_res = cancer_query_engine.query(contextual_query)
                if cancer_context_res.source_nodes:
                    context_results.extend([node.score or 0.0 for node in cancer_context_res.source_nodes])
            except:
                pass
            
            if context_results:
                contextual_score = max(context_results)
                print(f"[DEBUG] RAG: Contextual similarity = {contextual_score:.3f}")
        except Exception as exc:
            print(f"[DEBUG] RAG: Contextual search failed: {exc}")
            contextual_score = 0.0
    
    # Calculate weighted similarity score
    final_score = (primary_weight * best_score) + (context_weight * contextual_score)
    print(f"[DEBUG] RAG: Weighted similarity = {final_score:.3f} (primary: {best_score:.3f}, context: {contextual_score:.3f})")
    
    # Extract sources from top results
    links: List[str] = [
        result['source'] for result in top_results 
        if result['source'] and (("nhs.uk" in result['source']) or ("cancerresearchuk.org" in result['source']))
    ]
    
    # Domain filter: only NHS / Cancer Research pages
    if not any(("nhs.uk" in url) or ("cancerresearchuk.org" in url) for url in links):
        print(f"[DEBUG] RAG: No NHS/Cancer Research sources found")
        return None, 0.0, links
    
    # Check if weighted similarity is high enough
    if final_score < SIM_THRESHOLD:
        print(f"[DEBUG] RAG: Weighted similarity {final_score:.3f} below threshold {SIM_THRESHOLD}")
        return None, final_score, links
    
    # Extract context from top results
    context_parts = []
    for result in top_results:
        if result['score'] >= (SIM_THRESHOLD * 0.8):  # Slightly lower threshold for individual nodes
            context_parts.append(result['text'])
    
    context_text = "\n\n".join(context_parts) if context_parts else None
    return context_text, final_score, links

def get_rag_context(query: str) -> Tuple[Optional[str], float, List[str]]:
    """
    Legacy function - now just calls the weighted version with current query only
    """
    # For backwards compatibility, extract just the current question if it's a contextual query
    if "Current question:" in query:
        # Extract just the current question part
        parts = query.split("Current question:")
        if len(parts) > 1:
            current_query = parts[-1].strip()
        else:
            current_query = query
    else:
        current_query = query
    
    return get_rag_context_weighted(current_query)

# --------------------------------------------------------------------------- #
# GPT-4o conversation with optional RAG enhancement
# --------------------------------------------------------------------------- #
def generate_response_with_gpt4o(
    messages: List[Dict[str, str]], 
    current_message: str,
    rag_context: Optional[str] = None,
    sources: Optional[List[str]] = None,
    is_medical: bool = False,
    user_context: Optional[str] = None,
) -> str:
    """
    Generate response using GPT-4o, optionally enhanced with RAG context and user context
    """
    
    # Build system prompt
    system_prompt = """You are **Kyra**, an AI health assistant.  
Your mission: deliver clear, empathetic, evidence‑based health information
while sounding friendly and conversational.

**Context awareness**  
• Read the entire conversation thread before replying.  
• If the user follows up with “Is this serious?” etc., use prior messages to
  understand what they mean.

**General chat**  
• Respond warmly, keep things light, avoid unnecessary jargon.

**Anything non-medical that is not conversational**
• Respond with saying "I'm sorry, I can't help with that. I'm here to help with health questions."


**Health questions**  
• Always in the frist couple sentences mention the source of the information but 
in a smooth conversational way e.g. "I'm using the NHS/CDC/WHO websites to answer this question."
• Provide up‑to‑date, evidence‑based information (NHS, CDC, WHO, peer‑reviewed
  studies).  
• State your limits: you’re not a replacement for professional diagnosis or
  treatment. Encourage consulting a qualified clinician for personalised care.  
• Flag any red‑flag or emergency symptoms (e.g. chest pain, sudden vision loss)
  and advise calling local emergency services or seeing a doctor urgently.  
• Keep explanations in plain language; define unfamiliar medical terms.  
• Do **not** prescribe specific drugs/doses or create treatment plans.  
• If there is user context, use it to tailor your response.
• If user shows self‑harm intent, respond with compassion and give crisis
  hotline info for their region.
"""
    # ---------- Retrieved medical context ----------
    if rag_context:
        system_prompt += f"""

**Trusted reference material**  
Below are vetted excerpts (primarily NHS and Cancer Research UK).  
Use them to support your answer and cite them explicitly when quoted.

{rag_context}

Blend these passages with your broader medical knowledge; do not rely on them
exclusively.
"""
    # ---------- Medical query but no RAG ----------
    elif is_medical:
        system_prompt += """
No additional NHS documents were provided for this question. Rely on your
general medical knowledge **and** finish with a “Sources:” section listing
2‑3 authoritative, publicly accessible sites relevant to the topic, e.g.:

Sources:
- NHS.uk – [Condition overview]
- Mayo Clinic – [Condition overview]
- WHO – [Condition overview]
"""
    # Always inject user context for medical queries
    if is_medical and user_context:
        system_prompt += f"\n\n**User background/context:**\n{user_context}\n"

    # Prepare messages for GPT-4o - include conversation history + current message
    gpt_messages = [{"role": "system", "content": system_prompt}]
    gpt_messages.extend(messages)  # Add conversation history
    gpt_messages.append({"role": "user", "content": current_message})  # Add current message
    
    print(f"[DEBUG] Sending {len(gpt_messages)} messages to GPT-4o")
    print(f"[DEBUG] Full conversation context being sent:")
    for i, msg in enumerate(gpt_messages):
        print(f"  {i}. {msg['role']}: {msg['content'][:150]}...")
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=gpt_messages,
            temperature=0.7,  # Slightly more conversational
            max_tokens=1200  # Increased for sources
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"[DEBUG] GPT-4o error: {e}")
        return "I'm having trouble responding right now. Please try again in a moment."

# --------------------------------------------------------------------------- #
# Response formatting with sources
# --------------------------------------------------------------------------- #
def format_response_with_sources(
    response: str, 
    sources: List[str], 
    metadata: Dict[str, Any]
) -> Tuple[str, List[str]]:
    """
    Format the response with appropriate source information
    """
    if not metadata.get("is_medical", False):
        # Non-medical questions don't need source formatting
        return response, sources
    
    if metadata.get("used_rag", False) and sources:
        # RAG was used - show NHS/Cancer Research sources in response text
        unique_sources = list(dict.fromkeys(sources))  # Remove duplicates while preserving order
        
        # Add source section to response text
        if unique_sources:
            response += f"\n\n**Sources (Kyra's Knowledge Base):**\n"
            for source in unique_sources:
                if source.startswith('http://') or source.startswith('https://'):
                    # Make URLs clickable in markdown
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(source)
                        display_text = f"{parsed.netloc}{parsed.path}"
                        if len(display_text) > 60:
                            display_text = display_text[:57] + "..."
                        response += f"- [{display_text}]({source})\n"
                    except:
                        response += f"- {source}\n"
                else:
                    response += f"- {source}\n"
        
        return response, unique_sources
    else:
        # No RAG used - GPT-4o should have included general sources
        gpt_sources = []
        
        # Try to extract sources from GPT-4o response and convert to clickable links
        if "Sources:" in response or "sources:" in response.lower():
            lines = response.split('\n')
            in_sources = False
            source_replacements = []
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped.lower().startswith('sources:'):
                    in_sources = True
                    continue
                if in_sources and line_stripped.startswith('-'):
                    source_text = line_stripped[1:].strip()
                    gpt_sources.append(source_text)
                    
                    # Try to convert text sources to clickable links
                    clickable_link = convert_text_source_to_link(source_text)
                    if clickable_link != source_text:
                        # Replace the original line with a clickable link
                        source_replacements.append((line, f"- {clickable_link}"))
                elif in_sources and line_stripped and not line_stripped.startswith('-'):
                    break
            
            # Apply source replacements to make them clickable
            for old_line, new_line in source_replacements:
                response = response.replace(old_line, new_line)
        
        # Remove duplicates from GPT-4o sources
        unique_gpt_sources = list(dict.fromkeys(gpt_sources)) if gpt_sources else []
        
        # Add clear attribution for GPT-4o responses
        if unique_gpt_sources:
            # Replace the Sources section with clearer attribution
            response = response.replace("Sources:", "**Sources (General Medical Knowledge - GPT-4o):**")
        else:
            response += f"\n\n\n**Note:** This response is based on general medical knowledge (GPT-4o AI), not our internal knowledge base. For official NHS guidance, please visit NHS.uk or consult your healthcare provider."
        
        return response, unique_gpt_sources if unique_gpt_sources else sources

def convert_text_source_to_link(source_text: str) -> str:
    """
    Convert text-based sources like 'NHS.uk - Leptospirosis' to clickable markdown links
    """
    source_lower = source_text.lower()
    
    # NHS sources
    if 'nhs.uk' in source_lower:
        if '-' in source_text:
            parts = source_text.split('-', 1)
            topic = parts[1].strip() if len(parts) > 1 else ''
            # Convert topic to URL-friendly format
            topic_slug = topic.lower().replace(' ', '-').replace(',', '').replace('(', '').replace(')', '')
            nhs_url = f"https://www.nhs.uk/conditions/{topic_slug}/"
            return f"[{source_text}]({nhs_url})"
        else:
            return f"[{source_text}](https://www.nhs.uk/)"
    
    # Mayo Clinic sources
    elif 'mayo clinic' in source_lower:
        if '-' in source_text:
            parts = source_text.split('-', 1)
            topic = parts[1].strip() if len(parts) > 1 else ''
            # Convert topic to URL-friendly format
            topic_slug = topic.lower().replace(' ', '-').replace(',', '').replace('(', '').replace(')', '')
            mayo_url = f"https://www.mayoclinic.org/diseases-conditions/{topic_slug}/symptoms-causes/syc-20354349"
            return f"[{source_text}]({mayo_url})"
        else:
            return f"[{source_text}](https://www.mayoclinic.org/)"
    
    # CDC sources
    elif 'cdc' in source_lower:
        if '-' in source_text:
            parts = source_text.split('-', 1)
            topic = parts[1].strip() if len(parts) > 1 else ''
            # Convert topic to URL-friendly format
            topic_slug = topic.lower().replace(' ', '-').replace(',', '').replace('(', '').replace(')', '')
            cdc_url = f"https://www.cdc.gov/"
            return f"[{source_text}]({cdc_url})"
        else:
            return f"[{source_text}](https://www.cdc.gov/)"
    
    # WebMD sources
    elif 'webmd' in source_lower:
        if '-' in source_text:
            parts = source_text.split('-', 1)
            topic = parts[1].strip() if len(parts) > 1 else ''
            topic_slug = topic.lower().replace(' ', '-').replace(',', '').replace('(', '').replace(')', '')
            webmd_url = f"https://www.webmd.com/a-to-z-guides/{topic_slug}"
            return f"[{source_text}]({webmd_url})"
        else:
            return f"[{source_text}](https://www.webmd.com/)"
    
    # MedlinePlus sources
    elif 'medlineplus' in source_lower:
        if '-' in source_text:
            parts = source_text.split('-', 1)
            topic = parts[1].strip() if len(parts) > 1 else ''
            topic_slug = topic.lower().replace(' ', '').replace(',', '').replace('(', '').replace(')', '')
            medline_url = f"https://medlineplus.gov/{topic_slug}.html"
            return f"[{source_text}]({medline_url})"
        else:
            return f"[{source_text}](https://medlineplus.gov/)"
    
    # Cancer Research UK sources
    elif 'cancer research' in source_lower or 'cancerresearchuk' in source_lower:
        if '-' in source_text:
            parts = source_text.split('-', 1)
            topic = parts[1].strip() if len(parts) > 1 else ''
            topic_slug = topic.lower().replace(' ', '-').replace(',', '').replace('(', '').replace(')', '')
            cruk_url = f"https://www.cancerresearchuk.org/about-cancer/{topic_slug}"
            return f"[{source_text}]({cruk_url})"
        else:
            return f"[{source_text}](https://www.cancerresearchuk.org/)"
    
    # If no pattern matches, return original text
    return source_text

# --------------------------------------------------------------------------- #
# Main answer function
# --------------------------------------------------------------------------- #
def answer(
    query: str, 
    conversation_history: Optional[List[Dict[str, str]]] = None,
    original_query: Optional[str] = None,
    user_context: Optional[str] = None,
) -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Main answer function that handles both general and medical questions.
    
    Args:
        query: Current user question (may include context)
        conversation_history: List of {"role": "user/assistant", "content": "..."}
        original_query: Original query without conversation context
    
    Returns:
        (response_text, sources, metadata)
    """
    
    print(f"[DEBUG] === ANSWER FUNCTION CALLED ===")
    print(f"[DEBUG] Query: {query[:200]}...")
    print(f"[DEBUG] Original query: {original_query}")
    print(f"[DEBUG] Conversation history length: {len(conversation_history) if conversation_history else 0}")
    
    if conversation_history:
        print(f"[DEBUG] Conversation history:")
        for i, msg in enumerate(conversation_history):
            print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")
    
    # Use original query for classification if available, otherwise use full query
    classify_query = original_query if original_query else query
    current_message = original_query if original_query else query
    
    # Determine if this is a medical question
    is_medical = is_medical_question(classify_query)
    print(f"[DEBUG] Question classified as: {'MEDICAL' if is_medical else 'GENERAL'}")
    print(f"[DEBUG] Classify query: {classify_query}")
    
    # Prepare conversation messages (don't include current message yet)
    messages = conversation_history or []
    print(f"[DEBUG] Messages to send to GPT-4o: {len(messages)} history messages")
    
    rag_context = None
    sources = []
    rag_score = 0.0
    
    # For medical questions, try to get RAG context
    if is_medical:
        print(f"[DEBUG] Getting RAG context for medical question...")
        try:
            # Use weighted RAG search - prioritize current question over context
            rag_context, rag_score, sources = get_rag_context_weighted(
                current_message, 
                conversation_history
            )
            if rag_context:
                print(f"[DEBUG] Using RAG context (weighted score: {rag_score:.3f})")
                print(f"[DEBUG] RAG context preview: {rag_context[:200]}...")
                print(f"[DEBUG] Sources: {sources}")
            else:
                print(f"[DEBUG] No suitable RAG context found (weighted score: {rag_score:.3f})")
        except Exception as e:
            print(f"[DEBUG] RAG context error: {e}")
            # Continue without RAG context
    else:
        print(f"[DEBUG] Skipping RAG for general conversation")
    
    print(f"[DEBUG] Calling GPT-4o with {len(messages)} conversation messages")
    
    # Generate response with GPT-4o (with or without RAG enhancement)
    response = generate_response_with_gpt4o(messages, current_message, rag_context, sources, is_medical, user_context)
    
    print(f"[DEBUG] GPT-4o response: {response[:200]}...")
    
    # Format response with appropriate sources
    formatted_response, final_sources = format_response_with_sources(response, sources, {
        "is_medical": is_medical,
        "used_rag": rag_context is not None,
        "rag_score": rag_score,
        "model_used": "gpt-4o",
        "conversation_length": len(messages)
    })
    
    # Metadata for debugging/analytics
    metadata = {
        "is_medical": is_medical,
        "used_rag": rag_context is not None,
        "rag_score": rag_score,
        "model_used": "gpt-4o",
        "conversation_length": len(messages),
        "sources_count": len(final_sources)
    }
    
    print(f"[DEBUG] Final metadata: {metadata}")
    
    return formatted_response, final_sources, metadata

# --------------------------------------------------------------------------- #
# Backward compatibility function
# --------------------------------------------------------------------------- #
def answer_legacy(query: str) -> Tuple[Optional[str], float, List[str]]:
    """
    Legacy function signature for backward compatibility.
    Returns (response | None, score, sources) - None means fallback needed
    
    NOTE: This is deprecated. New code should use answer() function.
    """
    response, sources, metadata = answer(query)
    
    # For legacy compatibility, never return None (always have GPT-4o fallback)
    # But we'll simulate the old behavior for any calling code that expects it
    if not metadata["used_rag"]:
        # If no RAG was used, return None to trigger fallback in old code
        return None, metadata["rag_score"], sources
    
    return response, metadata["rag_score"], sources