import streamlit as st
import pandas as pd
import time
import openpyxl  # Explicit import to ensure it's available
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Product Content Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# GLOBAL STYLING - Modern, Clean UI
# =============================================================================
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global font and background */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Main container spacing */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Hide default Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom header styling */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}

.main-header h1 {
    color: white;
    font-size: 2.25rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.02em;
}

.main-header p {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.1rem;
    margin: 0;
    font-weight: 400;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #f8f9fa;
    padding: 8px;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}

.stTabs [data-baseweb="tab"] {
    height: 48px;
    padding: 0 24px;
    background-color: transparent;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.95rem;
    color: #64748b;
    border: none;
}

.stTabs [aria-selected="true"] {
    background-color: white !important;
    color: #667eea !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Card component */
.ui-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
    border: 1px solid #e2e8f0;
    margin-bottom: 1rem;
}

.ui-card-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #f1f5f9;
}

/* Section headers */
.section-header {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #667eea;
    display: inline-block;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    border: 1px solid #e2e8f0;
}

.metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.25rem;
}

.metric-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
}

/* Status badges */
.status-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.375rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
}

.status-success {
    background-color: #dcfce7;
    color: #166534;
}

.status-error {
    background-color: #fee2e2;
    color: #991b1b;
}

.status-warning {
    background-color: #fef3c7;
    color: #92400e;
}

.status-info {
    background-color: #dbeafe;
    color: #1e40af;
}

/* File uploader styling */
[data-testid="stFileUploader"] {
    background: #f8fafc;
    border-radius: 12px;
    padding: 1rem;
    border: 2px dashed #cbd5e1;
}

[data-testid="stFileUploader"]:hover {
    border-color: #667eea;
    background: #f1f5f9;
}

/* Input styling */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    border-radius: 8px !important;
    border: 1.5px solid #e2e8f0 !important;
    padding: 0.75rem !important;
    font-size: 0.95rem !important;
}

.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Button styling */
.stButton button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.625rem 1.25rem;
    transition: all 0.2s ease;
    border: none;
}

.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
}

.stButton button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45);
}

.stButton button[kind="secondary"] {
    background: white;
    border: 1.5px solid #e2e8f0;
    color: #475569;
}

.stButton button[kind="secondary"]:hover {
    background: #f8fafc;
    border-color: #667eea;
    color: #667eea;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: #f8fafc;
    border-radius: 8px;
    font-weight: 600;
    color: #334155;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    border-radius: 999px;
}

/* Dataframe styling */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}

/* Divider */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    margin: 2rem 0;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: #f8fafc;
    border-radius: 16px;
    border: 2px dashed #e2e8f0;
}

.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.empty-state-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0.5rem;
}

.empty-state-text {
    color: #64748b;
    font-size: 0.95rem;
}

/* Review product card */
.product-review-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid #e2e8f0;
}

.product-title-display {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 12px;
    padding: 1.25rem;
    border-left: 4px solid #667eea;
    margin: 1rem 0;
}

.product-title-text {
    font-size: 1.1rem;
    color: #1e293b;
    font-weight: 500;
    line-height: 1.5;
}

.char-count {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 0.5rem;
}

/* Image gallery */
.image-gallery {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}

/* Action button colors (Review tab) */
div[data-testid="stHorizontalBlock"]:has(.stColumn:nth-child(1) button):has(.stColumn:nth-child(2) button):has(.stColumn:nth-child(3) button) .stColumn:nth-child(1) button {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(34, 197, 94, 0.35) !important;
}

div[data-testid="stHorizontalBlock"]:has(.stColumn:nth-child(1) button):has(.stColumn:nth-child(2) button):has(.stColumn:nth-child(3) button) .stColumn:nth-child(2) button {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35) !important;
}

div[data-testid="stHorizontalBlock"]:has(.stColumn:nth-child(1) button):has(.stColumn:nth-child(2) button):has(.stColumn:nth-child(3) button) .stColumn:nth-child(3) button {
    background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(100, 116, 139, 0.35) !important;
}

/* Success/Error/Info/Warning alerts */
.stAlert {
    border-radius: 10px;
    border: none;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #f8fafc;
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}

[data-testid="stMetricValue"] {
    font-weight: 700;
}

/* Download button */
.stDownloadButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
}

/* =============================================================================
   GENERATION PROGRESS COMPONENTS
   ============================================================================= */

/* Timeline container */
.timeline-container {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 12px;
    overflow-x: auto;
    margin-bottom: 1rem;
}

/* Timeline dot base style */
.timeline-dot {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 600;
    transition: all 0.3s ease;
}

/* Timeline dot states */
.timeline-dot.pending {
    background: #e2e8f0;
    color: #94a3b8;
}

.timeline-dot.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.3);
    animation: pulse 2s infinite;
}

.timeline-dot.completed {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    color: white;
}

.timeline-dot.warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
}

.timeline-dot.error {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.3); }
    50% { box-shadow: 0 0 0 8px rgba(102, 126, 234, 0.1); }
}

/* Current product card */
.current-product-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid #e2e8f0;
    margin-bottom: 1rem;
}

/* Step indicator */
.step-indicator {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: #f8fafc;
    border-radius: 8px;
    margin-bottom: 0.5rem;
}

.step-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}

.step-icon.pending {
    background: #e2e8f0;
    color: #94a3b8;
}

.step-icon.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    animation: spin 1.5s linear infinite;
}

.step-icon.completed {
    background: #dcfce7;
    color: #166534;
}

.step-icon.retry {
    background: #fef3c7;
    color: #92400e;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.step-content {
    flex: 1;
}

.step-title {
    font-weight: 600;
    color: #1e293b;
    font-size: 0.95rem;
}

.step-subtitle {
    font-size: 0.8rem;
    color: #64748b;
}

/* Live stats row */
.live-stats {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.live-stat-card {
    flex: 1;
    background: #f8fafc;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    border: 1px solid #e2e8f0;
}

.live-stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
}

.live-stat-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Control buttons */
.control-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

/* Paused/Stopped state banner */
.state-banner {
    padding: 1rem;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
}

.state-banner.paused {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 1px solid #fbbf24;
}

.state-banner.stopped {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border: 1px solid #f87171;
}

.state-banner-icon {
    font-size: 1.5rem;
}

.state-banner-text {
    flex: 1;
}

.state-banner-title {
    font-weight: 600;
    color: #1e293b;
}

.state-banner-subtitle {
    font-size: 0.85rem;
    color: #64748b;
}
</style>
""", unsafe_allow_html=True)

# Default prompts
DEFAULT_SYSTEM_PROMPT = """You are a well seasoned product copywriter. You are very precise with word and character count."""

DEFAULT_TASK1_PROMPT = """Craft a product title using relevant keywords from the list above and following on the following format: "Existing Product Name | Relevant Keyword #1 | Relevant Keyword #2" (e.g., "Octopus Figurine | Antique Brass Figure | Miniature Display")"""

DEFAULT_TASK2_PROMPT = """Craft a product description based on the product title above following this format for product "Octopus Figurine | Antique Brass Figure | Miniature Display":

1. 160-character hook that captures the product's overall essence and value (e.g., "Bring a touch of ocean-inspired charm to any space with the Antique Brass Octopus Figurine, a brass figure that captures nature's beauty in miniature form.")

2. 2-sentence description of the product that sums up what it is, how it was created, and what it is used for (e.g., "The Octopus Figurine is carefully sculpted using brass and given an antique finish to elevate modern interiors with a hint of nautical allure. Each detail, from the textured tentacles to the vintage metallic finish, is meticulously crafted to highlight the artistry and craftsmanship behind Kiyo Home's nature-inspired creations.")

3. 1-sentence comprehensive use-case for the product, start the sentence with this phrase: "Perfect as (a/an) [usage] for [target consumers/users]" (e.g., "Perfect as a desk ornament, console tables, workspace displays, shelf accent, giftable keepsake, or just to generally add a coastal charm anywhere one can think of.")

4. List of key features (make them concise, readable, and digestible) - (e.g., "Key Features:

* Antique brass finish with detailed tentacle design

* Compact and lightweight for easy placement and styling

* Doubles as a collectible or conversation piece

* Smooth base ensures safe placement on surface)

5. List of construction materials used ("Made In:," "Materials Used:," etc.) - (e.g., "Construction & Materials:

* Dimensions: 1.89 in x 2.17 in (4.8 cm x 5.5 cm)

* Weight: 30 g

* Material: Solid brass

* Finish: Antique-style polish for an aged look")

6. List of style guide ("Colors:," "Style:," Theme:," "Occasion:," "Seasonality,: etc.) - (e.g., "Style Guide:

* Colors: Antique brass

* Style: Nautical, vintage, and artisanal

* Theme: Ocean-inspired, nature-focused, and tranquil

* Occasion: Everyday décor, gifting, or display use

* Seasonality: Year-round collectible suitable for timeless interiors)

7. List of eco-friendly information (ONLY ADD THIS WHEN RELEVANT! REMOVE OTHERWISE!)

8. List of retailer information ("Why We Made This:," "Why You'll Love This:," "Pairs Well With:," "Suitable for Retailers Such As:") - I want this section to be retailer-focused, as in it should align with the goals of a retailer who will stock up on the product, which is TO SELL

9. Brand story (e.g., "Kiyo Home was founded on the belief that your home should be as unique as you are, a place that inspires and nurtures. Rooted in a love for nature and timeless design, the brand curates décor and lighting that bring warmth and tranquility into your space.")

10. Punchy CTA to encourage retailers to stock up on the product so they can sell (e.g., "Add the Octopus Figurine to your retail collection and offer your customers a sustainable, artful accent that enhances every space with charm and sophistication.")



Additional Notes:



#1 Create the product description copy seamless and continuous that I can simply copy and paste

#2 Don't add heading categories to your generated except for the following sections: Key Features, Construction & Materials, Style Guide, Eco-friendly Information, and Retailer Information, and add bullet points for these sections

#3 Make the prose less stylistic and keep it straightforward while still demonstrating the value that retailers (and their customers) will get when they stock up on the item

#4 Use proper noun when addressing the item to sell

#5 No bold letters! No em dashes!"""

# Token pricing for GPT-4o
INPUT_TOKEN_COST = 2.50 / 1_000_000
OUTPUT_TOKEN_COST = 10.00 / 1_000_000


def get_image_urls(image_urls_str):
    """Parse image URLs and return list of URLs."""
    if pd.isna(image_urls_str) or not image_urls_str:
        return []

    text = str(image_urls_str).replace("\n", " ")
    return [url.strip() for url in text.split() if url.strip().startswith("http")]


def create_image_content(urls):
    """Create content list for vision model from URLs."""
    return [{"type": "image_url", "image_url": {"url": url}} for url in urls]


def create_prompt_content(row, task_prompt, general_info):
    """Create the text content for the prompt."""
    return f"""Input English Language to be used: {general_info['language']}
Brand Name: {general_info['brand_name']}
Brand Story: {general_info['brand_story']}
Product Name: {row['Product Name']}
Product Category: {row['Product Category']}
Existing Product Description: {row['Product Description']}
SEO Key words input list: {row['SEO Details']}
Made in Country: {row['Made In']}

{task_prompt}"""


def invoke_agent(llm, row, task_prompt, system_prompt, general_info, include_images=True):
    """Invoke the agent with text and images. Retries without images if image download fails.

    Returns: (content, input_tokens, output_tokens, cost, image_info)
    where image_info is a dict with 'available', 'used', and 'status' keys.
    """
    text_content = create_prompt_content(row, task_prompt, general_info)

    # Get all available image URLs
    all_image_urls = get_image_urls(row.get('Images', ''))
    total_available = len(all_image_urls)

    if include_images and all_image_urls:
        image_content = create_image_content(all_image_urls)
        images_used = len(all_image_urls)
    else:
        image_content = []
        images_used = 0

    content = [{"type": "text", "text": text_content}]
    content.extend(image_content)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=content)
    ]

    try:
        response = llm.invoke(messages)
        image_status = "success" if images_used > 0 else ("no_images" if total_available == 0 else "skipped")
    except Exception as e:
        error_str = str(e).lower()
        # If image-related error, retry without images
        if include_images and ('image' in error_str or 'timeout' in error_str or 'download' in error_str):
            result = invoke_agent(llm, row, task_prompt, system_prompt, general_info, include_images=False)
            # Update image info to show failure
            result_list = list(result)
            result_list[4] = {
                'available': total_available,
                'used': 0,
                'status': 'failed'
            }
            return tuple(result_list)
        raise  # Re-raise if not an image error or already tried without images

    usage = response.usage_metadata
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost = (input_tokens * INPUT_TOKEN_COST) + (output_tokens * OUTPUT_TOKEN_COST)

    image_info = {
        'available': total_available,
        'used': images_used,
        'status': image_status
    }

    return response.content, input_tokens, output_tokens, cost, image_info


def invoke_retry(llm, previous_output, char_min, char_max, char_target, content_type="text"):
    """Lightweight retry for rewriting to meet character limits."""
    retry_prompt = f"""Rewrite the following {content_type} to be between {char_min}-{char_max} characters (aim for approximately {char_target} characters).

Current {content_type} ({len(previous_output)} characters):
{previous_output}

CRITICAL REQUIREMENTS:
- Output ONLY the rewritten {content_type}, nothing else
- DO NOT change the format or structure in any way
- Keep the exact same formatting (HTML tags, line breaks, bullet points, etc.)
- Only adjust the length by adding or removing content
- Preserve all key information and meaning"""

    messages = [
        SystemMessage(content="You are a helpful assistant that rewrites text to meet character limits while preserving meaning."),
        HumanMessage(content=retry_prompt)
    ]

    response = llm.invoke(messages)

    usage = response.usage_metadata
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost = (input_tokens * INPUT_TOKEN_COST) + (output_tokens * OUTPUT_TOKEN_COST)

    return response.content, input_tokens, output_tokens, cost


def update_live_stats_ui(ui_containers, total_products):
    """Helper to update the live stats UI with current session state values."""
    if ui_containers and 'stats' in ui_containers:
        start_time = st.session_state.get('gen_start_time', time.time())
        completed = len(st.session_state.get('gen_results', []))
        cost = st.session_state.get('gen_total_cost', 0)
        ui_containers['stats'].markdown(
            render_live_stats(completed, total_products, cost, start_time),
            unsafe_allow_html=True
        )


def process_single_product(llm, row, prompts, char_limits, general_info, ui_containers, total_products):
    """Process a single product and return the result with detailed progress updates.

    Args:
        llm: The language model instance
        row: DataFrame row with product data
        prompts: Dict with 'system', 'task1', 'task2' prompts
        char_limits: Dict with character limits
        general_info: General brand/language info
        ui_containers: Dict with 'timeline', 'status', 'steps' containers for UI updates
        total_products: Total number of products (for stats display)

    Returns:
        Tuple of (result_dict, tokens_in, tokens_out, cost, image_status, had_retries)
    """
    product_name = row['Product Name']
    total_in_tokens = 0
    total_out_tokens = 0
    total_cost = 0.0
    had_retries = False

    system_prompt = prompts['system']
    if prompts.get('brand'):
        system_prompt += f"\n\nBrand Guidelines:\n{prompts['brand']}"

    title_prompt = prompts['task1'] + f"\n\nSTRICT CHARACTER LIMIT: Your response MUST be between {char_limits['title_min']}-{char_limits['title_max']} characters. Aim for approximately {char_limits['title_target']} characters."
    desc_prompt = prompts['task2'] + f"\n\nSTRICT CHARACTER LIMIT: Your response MUST be between {char_limits['desc_min']}-{char_limits['desc_max']} characters. Aim for approximately {char_limits['desc_target']} characters."

    # Update UI - generating title
    if ui_containers and 'steps' in ui_containers:
        ui_containers['steps'].markdown(
            render_step_indicator("Generating Title", "active", f"Processing: {product_name[:40]}...") +
            render_step_indicator("Generating Description", "pending"),
            unsafe_allow_html=True
        )

    # Generate title
    product_title, in_tok, out_tok, cost, title_img_info = invoke_agent(
        llm, row, title_prompt, system_prompt, general_info
    )
    total_in_tokens += in_tok
    total_out_tokens += out_tok
    total_cost += cost

    # Update running totals in session state for real-time stats
    st.session_state['gen_total_cost'] = st.session_state.get('gen_total_cost', 0) + cost
    update_live_stats_ui(ui_containers, total_products)

    product_title = product_title.strip().strip('"').strip("'")
    title_char_count = len(product_title)

    # Retry title if needed
    title_retry_count = 0
    while (title_char_count < char_limits['title_min'] or title_char_count > char_limits['title_max']) and title_retry_count < 3:
        title_retry_count += 1
        had_retries = True

        if ui_containers and 'steps' in ui_containers:
            ui_containers['steps'].markdown(
                render_step_indicator("Generating Title", "retry", f"Retry {title_retry_count}/3 - adjusting length ({title_char_count} chars)") +
                render_step_indicator("Generating Description", "pending"),
                unsafe_allow_html=True
            )

        product_title, in_tok, out_tok, cost = invoke_retry(
            llm, product_title, char_limits['title_min'], char_limits['title_max'],
            char_limits['title_target'], "product title"
        )
        total_in_tokens += in_tok
        total_out_tokens += out_tok
        total_cost += cost

        # Update running totals for real-time stats
        st.session_state['gen_total_cost'] = st.session_state.get('gen_total_cost', 0) + cost
        update_live_stats_ui(ui_containers, total_products)

        product_title = product_title.strip().strip('"').strip("'")
        title_char_count = len(product_title)

    # Update UI - generating description
    title_status = "completed" if char_limits['title_min'] <= title_char_count <= char_limits['title_max'] else "warning"
    if ui_containers and 'steps' in ui_containers:
        ui_containers['steps'].markdown(
            render_step_indicator("Generating Title", title_status, f"{title_char_count} characters") +
            render_step_indicator("Generating Description", "active", "Processing..."),
            unsafe_allow_html=True
        )

    # Generate description
    product_description, in_tok, out_tok, cost, desc_img_info = invoke_agent(
        llm, row, desc_prompt, system_prompt, general_info
    )
    total_in_tokens += in_tok
    total_out_tokens += out_tok
    total_cost += cost

    # Update running totals for real-time stats
    st.session_state['gen_total_cost'] = st.session_state.get('gen_total_cost', 0) + cost
    update_live_stats_ui(ui_containers, total_products)

    desc_char_count = len(product_description)

    # Retry description if needed
    desc_retry_count = 0
    while (desc_char_count < char_limits['desc_min'] or desc_char_count > char_limits['desc_max']) and desc_retry_count < 3:
        desc_retry_count += 1
        had_retries = True

        if ui_containers and 'steps' in ui_containers:
            ui_containers['steps'].markdown(
                render_step_indicator("Generating Title", title_status, f"{title_char_count} characters") +
                render_step_indicator("Generating Description", "retry", f"Retry {desc_retry_count}/3 - adjusting length ({desc_char_count} chars)"),
                unsafe_allow_html=True
            )

        product_description, in_tok, out_tok, cost = invoke_retry(
            llm, product_description, char_limits['desc_min'], char_limits['desc_max'],
            char_limits['desc_target'], "product description"
        )
        total_in_tokens += in_tok
        total_out_tokens += out_tok
        total_cost += cost

        # Update running totals for real-time stats
        st.session_state['gen_total_cost'] = st.session_state.get('gen_total_cost', 0) + cost
        update_live_stats_ui(ui_containers, total_products)

        desc_char_count = len(product_description)

    # Extract review images
    image_urls_str = row.get('Images', '')
    if pd.isna(image_urls_str) or not image_urls_str:
        review_images = ""
    else:
        text = str(image_urls_str).replace("\n", " ")
        urls = [url.strip() for url in text.split() if url.strip().startswith("http")]
        review_images = "\n".join(urls[:3])

    # Determine image status for this product
    img_status_str = f"{title_img_info['used']}/{title_img_info['available']}"
    if title_img_info['status'] == 'failed':
        img_status_str += " (failed)"
    elif title_img_info['status'] == 'no_images':
        img_status_str = "No images"

    result = {
        "Product Token": row["Product Token"],
        "Product Name": product_name,
        "Product Title": product_title,
        "Product Description": product_description,
        "Images Status": img_status_str,
        "Review Images": review_images
    }

    return result, total_in_tokens, total_out_tokens, total_cost, title_img_info['status'], had_retries


def run_generation(llm, product_data, general_info, prompts, char_limits, ui_containers, start_index=0):
    """Run the generation process with pause/stop support.

    This function updates session_state directly for progress tracking.

    Args:
        llm: Language model instance
        product_data: DataFrame with product data
        general_info: Brand/language info
        prompts: Prompt configuration
        char_limits: Character limit configuration
        ui_containers: Dict with UI containers for updates
        start_index: Index to start/resume from

    Returns:
        True if completed, False if stopped/paused
    """
    total_products = len(product_data)

    # Initialize or retrieve generation state from session
    if 'gen_results' not in st.session_state:
        st.session_state['gen_results'] = []
    if 'gen_product_statuses' not in st.session_state:
        st.session_state['gen_product_statuses'] = {}
    if 'gen_total_cost' not in st.session_state:
        st.session_state['gen_total_cost'] = 0.0
    if 'gen_total_input' not in st.session_state:
        st.session_state['gen_total_input'] = 0
    if 'gen_total_output' not in st.session_state:
        st.session_state['gen_total_output'] = 0
    if 'gen_image_stats' not in st.session_state:
        st.session_state['gen_image_stats'] = {'success': 0, 'failed': 0, 'no_images': 0}
    if 'gen_start_time' not in st.session_state:
        st.session_state['gen_start_time'] = time.time()

    for idx in range(start_index, total_products):
        # Check for stop/pause
        if st.session_state.get('gen_stop_requested', False):
            st.session_state['gen_state'] = 'stopped'
            st.session_state['gen_current_index'] = idx
            return False

        if st.session_state.get('gen_pause_requested', False):
            st.session_state['gen_state'] = 'paused'
            st.session_state['gen_current_index'] = idx
            st.session_state['gen_pause_requested'] = False
            return False

        # Update current index
        st.session_state['gen_current_index'] = idx

        row = product_data.iloc[idx]
        product_name = row['Product Name']

        # Update timeline
        if ui_containers and 'timeline' in ui_containers:
            ui_containers['timeline'].markdown(
                render_timeline(total_products, idx, st.session_state['gen_product_statuses']),
                unsafe_allow_html=True
            )

        # Update live stats (pass start_time for JS-based real-time timer)
        if ui_containers and 'stats' in ui_containers:
            ui_containers['stats'].markdown(
                render_live_stats(
                    len(st.session_state['gen_results']),
                    total_products,
                    st.session_state['gen_total_cost'],
                    st.session_state['gen_start_time']
                ),
                unsafe_allow_html=True
            )

        # Update current product info
        if ui_containers and 'current_product' in ui_containers:
            # Get first image URL for preview if available
            image_urls_str = row.get('Images', '')
            preview_img = ""
            if pd.notna(image_urls_str) and image_urls_str:
                urls = [url.strip() for url in str(image_urls_str).replace("\n", " ").split() if url.strip().startswith("http")]
                if urls:
                    preview_img = f'<img src="{urls[0]}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; margin-right: 1rem;">'

            ui_containers['current_product'].markdown(f'''
            <div style="display: flex; align-items: center; padding: 1rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; margin-bottom: 1rem;">
                {preview_img}
                <div>
                    <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase;">Now Processing</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #1e293b;">{product_name}</div>
                    <div style="font-size: 0.85rem; color: #64748b;">Product {idx + 1} of {total_products}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # Process the product
        try:
            result, in_tok, out_tok, _, img_status, had_retries = process_single_product(
                llm, row, prompts, char_limits, general_info, ui_containers, total_products
            )

            # Update totals (cost is already updated in real-time inside process_single_product)
            st.session_state['gen_results'].append(result)
            st.session_state['gen_total_input'] += in_tok
            st.session_state['gen_total_output'] += out_tok
            st.session_state['gen_image_stats'][img_status] = st.session_state['gen_image_stats'].get(img_status, 0) + 1

            # Update product status
            if had_retries:
                st.session_state['gen_product_statuses'][idx] = 'warning'
            else:
                st.session_state['gen_product_statuses'][idx] = 'completed'

        except Exception as e:
            st.session_state['gen_product_statuses'][idx] = 'error'
            st.error(f"Error processing product {idx + 1}: {str(e)}")
            # Continue to next product instead of stopping
            continue

    # Generation complete
    st.session_state['gen_state'] = 'completed'
    st.session_state['gen_current_index'] = total_products

    # Final timeline update
    if ui_containers and 'timeline' in ui_containers:
        ui_containers['timeline'].markdown(
            render_timeline(total_products, total_products, st.session_state['gen_product_statuses']),
            unsafe_allow_html=True
        )

    return True


def render_timeline(total_products, current_index, product_statuses):
    """Render a horizontal timeline showing product processing status.

    Args:
        total_products: Total number of products
        current_index: Index of currently processing product (-1 if not processing)
        product_statuses: Dict mapping index to status ('completed', 'warning', 'error')
    """
    dots = []
    for i in range(total_products):
        if i < current_index:
            status = product_statuses.get(i, 'completed')
            icon = '✓' if status == 'completed' else ('!' if status == 'warning' else '✗')
            dots.append(f'<div class="timeline-dot {status}" title="Product {i+1}">{icon}</div>')
        elif i == current_index:
            dots.append(f'<div class="timeline-dot active" title="Product {i+1} (Processing)">{i+1}</div>')
        else:
            dots.append(f'<div class="timeline-dot pending" title="Product {i+1}">{i+1}</div>')

    return f'<div class="timeline-container">{"".join(dots)}</div>'


def render_step_indicator(step_name, status, subtitle=""):
    """Render a step indicator with icon and text.

    Args:
        step_name: Name of the step (e.g., "Generating Title")
        status: 'pending', 'active', 'completed', 'retry'
        subtitle: Optional subtitle text
    """
    icons = {
        'pending': '○',
        'active': '◐',
        'completed': '✓',
        'retry': '↻'
    }
    icon = icons.get(status, '○')

    return f'''
    <div class="step-indicator">
        <div class="step-icon {status}">{icon}</div>
        <div class="step-content">
            <div class="step-title">{step_name}</div>
            {f'<div class="step-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
    </div>
    '''


def render_live_stats(completed, total, cost, start_timestamp):
    """Render live statistics cards with JavaScript-powered real-time timer.

    Args:
        completed: Number of completed products
        total: Total number of products
        cost: Total cost so far
        start_timestamp: Unix timestamp when generation started (time.time())
    """
    # Calculate average time per product for ETA calculation
    elapsed_so_far = time.time() - start_timestamp
    if completed > 0 and elapsed_so_far > 0:
        avg_time_per_product = elapsed_so_far / completed
    else:
        avg_time_per_product = 0

    return f'''
    <div class="live-stats">
        <div class="live-stat-card">
            <div class="live-stat-value" id="stat-products">{completed}/{total}</div>
            <div class="live-stat-label">Products</div>
        </div>
        <div class="live-stat-card">
            <div class="live-stat-value" id="stat-cost">${cost:.4f}</div>
            <div class="live-stat-label">Cost</div>
        </div>
        <div class="live-stat-card">
            <div class="live-stat-value" id="stat-elapsed">0s</div>
            <div class="live-stat-label">Elapsed</div>
        </div>
        <div class="live-stat-card">
            <div class="live-stat-value" id="stat-eta">--</div>
            <div class="live-stat-label">ETA</div>
        </div>
    </div>
    <script>
        (function() {{
            const startTime = {start_timestamp * 1000};  // Convert to milliseconds
            const completed = {completed};
            const total = {total};
            const avgTimePerProduct = {avg_time_per_product * 1000};  // Convert to milliseconds

            function formatTime(ms) {{
                const seconds = Math.floor(ms / 1000);
                if (seconds < 60) return seconds + 's';
                if (seconds < 3600) return Math.floor(seconds / 60) + 'm ' + (seconds % 60) + 's';
                return Math.floor(seconds / 3600) + 'h ' + Math.floor((seconds % 3600) / 60) + 'm';
            }}

            function updateTimer() {{
                const now = Date.now();
                const elapsed = now - startTime;

                // Update elapsed time
                const elapsedEl = document.getElementById('stat-elapsed');
                if (elapsedEl) elapsedEl.textContent = formatTime(elapsed);

                // Update ETA based on average time per product
                const etaEl = document.getElementById('stat-eta');
                if (etaEl) {{
                    if (completed > 0 && avgTimePerProduct > 0) {{
                        const remaining = total - completed;
                        const etaMs = remaining * avgTimePerProduct;
                        // Subtract time elapsed since last completion
                        const adjustedEta = Math.max(0, etaMs - (elapsed - (completed * avgTimePerProduct)));
                        etaEl.textContent = formatTime(adjustedEta);
                    }} else {{
                        etaEl.textContent = '--';
                    }}
                }}
            }}

            // Update immediately and then every second
            updateTimer();
            const intervalId = setInterval(updateTimer, 1000);

            // Clean up when element is removed (Streamlit re-renders)
            const observer = new MutationObserver(function(mutations) {{
                if (!document.getElementById('stat-elapsed')) {{
                    clearInterval(intervalId);
                    observer.disconnect();
                }}
            }});
            observer.observe(document.body, {{ childList: true, subtree: true }});
        }})();
    </script>
    '''


def render_progress_ring(reviewed_count, total_count, approved_count, rejected_count):
    """Render a segmented progress ring showing approved (green), rejected (red), and un-reviewed (grey)."""
    if total_count == 0:
        approved_pct = 0
        rejected_pct = 0
        unreviewed_pct = 1
    else:
        approved_pct = approved_count / total_count
        rejected_pct = rejected_count / total_count
        unreviewed_pct = (total_count - approved_count - rejected_count) / total_count

    # SVG progress ring with three segments
    radius = 45
    circumference = 2 * 3.14159 * radius

    # Calculate arc lengths for each segment
    approved_arc = circumference * approved_pct
    rejected_arc = circumference * rejected_pct
    unreviewed_arc = circumference * unreviewed_pct

    # Calculate rotation angles (cumulative)
    # Start with approved (green)
    approved_rotation = -90
    # Then rejected (red)
    rejected_rotation = -90 + (approved_pct * 360)
    # Then unreviewed (grey)
    unreviewed_rotation = -90 + ((approved_pct + rejected_pct) * 360)

    svg = f'''<div style="display: flex; flex-direction: column; align-items: center;"><svg width="120" height="120" viewBox="0 0 120 120"><circle cx="60" cy="60" r="{radius}" fill="none" stroke="#e9ecef" stroke-width="10"/><circle cx="60" cy="60" r="{radius}" fill="none" stroke="#28a745" stroke-width="10" stroke-dasharray="{approved_arc} {circumference - approved_arc}" transform="rotate({approved_rotation} 60 60)"/><circle cx="60" cy="60" r="{radius}" fill="none" stroke="#dc3545" stroke-width="10" stroke-dasharray="{rejected_arc} {circumference - rejected_arc}" transform="rotate({rejected_rotation} 60 60)"/><circle cx="60" cy="60" r="{radius}" fill="none" stroke="#6c757d" stroke-width="10" stroke-dasharray="{unreviewed_arc} {circumference - unreviewed_arc}" transform="rotate({unreviewed_rotation} 60 60)"/><text x="60" y="55" text-anchor="middle" font-size="20" font-weight="bold" fill="#495057">{reviewed_count}</text><text x="60" y="75" text-anchor="middle" font-size="12" fill="#6c757d">of {total_count}</text></svg><div style="display: flex; gap: 15px; margin-top: 5px; font-size: 12px;"><span style="color: #28a745;">✓ {approved_count}</span><span style="color: #dc3545;">✗ {rejected_count}</span></div></div>'''
    return svg


def main():
    # Custom header
    st.markdown("""
    <div class="main-header">
        <h1>✨ Product Content Generator</h1>
        <p>Transform your product data into compelling titles and descriptions with AI</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize review session state
    if 'review_data' not in st.session_state:
        st.session_state['review_data'] = None
    if 'review_statuses' not in st.session_state:
        st.session_state['review_statuses'] = {}  # {index: 'approved'|'rejected'|None}
    if 'current_review_index' not in st.session_state:
        st.session_state['current_review_index'] = 0
    if 'review_in_progress' not in st.session_state:
        st.session_state['review_in_progress'] = False

    # Main content area - Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📁 Upload", "📝 Prompts", "⚙️ Settings", "🚀 Generate", "👁️ Review"])

    # Tab 1: Data Upload
    with tab1:
        st.markdown('<p class="section-header">Upload Your Data</p>', unsafe_allow_html=True)

        # Check if data already loaded
        if 'product_data' in st.session_state:
            st.markdown(f"""
            <div class="ui-card">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-radius: 12px; padding: 1rem; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 1.5rem;">✓</span>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #166534; font-size: 1.1rem;">Data Loaded Successfully</div>
                        <div style="color: #64748b; font-size: 0.9rem;">{len(st.session_state['product_data'])} products ready for processing</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "Drop your Excel file here or click to browse",
                type=['xlsx', 'xls'],
                help="Excel file should have 'Products' and 'General Details' sheets"
            )

        with col2:
            with st.container(border=True):
                st.markdown("**📋 Template Preview**")

                # Create template tabs
                template_tab1, template_tab2 = st.tabs(["Products", "General Details"])

                with template_tab1:
                    # Sample Products template
                    products_template = pd.DataFrame({
                        'Product Token': ['SKU001', 'SKU002'],
                        'Product Name': ['Product A', 'Product B'],
                        'Product Category': ['Category 1', 'Category 2'],
                        'Product Description': ['Description...', 'Description...'],
                        'SEO Details': ['keyword1, keyword2', 'keyword3, keyword4'],
                        'Images': ['https://...', 'https://...'],
                        'Made In': ['Country', 'Country']
                    })
                    st.dataframe(products_template, use_container_width=True, hide_index=True, height=108)

                with template_tab2:
                    # Sample General Details template
                    general_template = pd.DataFrame({
                        'Field': ['Language', 'Brand', 'Story'],
                        'Value': ['English', 'Your Brand', 'Brand story...']
                    })
                    st.dataframe(general_template, use_container_width=True, hide_index=True, height=143)

        # Demo button to load test data
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("🧪 Use Test Data", help="Load sample data for demo purposes", type="secondary"):
            try:
                import os
                test_file_path = os.path.join(os.path.dirname(__file__), 'test_data.xlsx')
                product_data = pd.read_excel(test_file_path, sheet_name="Products", engine='openpyxl')
                general_data = pd.read_excel(test_file_path, sheet_name="General Details", header=None, engine='openpyxl')

                st.session_state['product_data'] = product_data
                st.session_state['general_data'] = general_data

                general_dict = dict(zip(general_data[0], general_data[1]))
                st.session_state['general_info'] = {
                    'language': general_dict.get("Language", "English"),
                    'brand_name': general_dict.get("Brand", ""),
                    'brand_story': general_dict.get("Story", "")
                }
                st.rerun()
            except Exception as e:
                st.error(f"Error loading test data: {str(e)}")

        if uploaded_file:
            try:
                product_data = pd.read_excel(uploaded_file, sheet_name="Products", engine='openpyxl')
                general_data = pd.read_excel(uploaded_file, sheet_name="General Details", header=None, engine='openpyxl')

                # Store in session state
                st.session_state['product_data'] = product_data
                st.session_state['general_data'] = general_data

                # Parse general details
                general_dict = dict(zip(general_data[0], general_data[1]))
                st.session_state['general_info'] = {
                    'language': general_dict.get("Language", "English"),
                    'brand_name': general_dict.get("Brand", ""),
                    'brand_story': general_dict.get("Story", "")
                }

                st.success(f"✓ Successfully loaded {len(product_data)} products")

                # Product preview in a card
                with st.expander("📊 Preview Product Data", expanded=True):
                    st.dataframe(product_data.head(10), use_container_width=True)

                # Brand details in styled cards
                st.markdown("#### Brand Information")
                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.markdown(f"""
                    <div class="ui-card">
                        <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.25rem;">LANGUAGE</div>
                        <div style="font-weight: 600; color: #1e293b;">{st.session_state['general_info']['language']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with info_col2:
                    st.markdown(f"""
                    <div class="ui-card">
                        <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.25rem;">BRAND</div>
                        <div style="font-weight: 600; color: #1e293b;">{st.session_state['general_info']['brand_name'] or 'Not specified'}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with info_col3:
                    st.markdown(f"""
                    <div class="ui-card">
                        <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.25rem;">PRODUCTS</div>
                        <div style="font-weight: 600; color: #1e293b;">{len(product_data)}</div>
                    </div>
                    """, unsafe_allow_html=True)

                if st.session_state['general_info']['brand_story']:
                    with st.expander("📖 Brand Story"):
                        st.write(st.session_state['general_info']['brand_story'])

            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
        elif 'product_data' not in st.session_state:
            # Empty state
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <div class="empty-state-title">No data uploaded yet</div>
                <div class="empty-state-text">Upload an Excel file with your product data to get started</div>
            </div>
            """, unsafe_allow_html=True)

    # Tab 2: Prompts
    with tab2:
        st.markdown('<p class="section-header">Configure Prompts</p>', unsafe_allow_html=True)

        st.markdown("""
        <div class="ui-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-color: #fbbf24;">
            <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                <span style="font-size: 1.25rem;">💡</span>
                <div style="font-size: 0.9rem; color: #92400e;">
                    <strong>Pro tip:</strong> You can upload .txt files to quickly load your prompts, or edit them directly below. Changes are saved automatically for this session.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # System Prompt
        with st.expander("🤖 System Prompt", expanded=False):
            system_upload = st.file_uploader("Upload system prompt (optional)", type=['txt'], key="system_upload")
            if system_upload:
                st.session_state['system_prompt'] = system_upload.read().decode('utf-8')
            if 'system_prompt' not in st.session_state:
                st.session_state['system_prompt'] = DEFAULT_SYSTEM_PROMPT
            system_prompt = st.text_area(
                "System prompt",
                value=st.session_state['system_prompt'],
                height=100,
                key="system_prompt_input",
                label_visibility="collapsed"
            )
            st.session_state['system_prompt'] = system_prompt

        # Brand Prompt (Optional)
        with st.expander("🎨 Brand Guidelines (Optional)", expanded=False):
            st.caption("This will be appended to the system prompt if provided")
            brand_upload = st.file_uploader("Upload brand guidelines (optional)", type=['txt'], key="brand_upload")
            if brand_upload:
                st.session_state['brand_prompt'] = brand_upload.read().decode('utf-8')
            if 'brand_prompt' not in st.session_state:
                st.session_state['brand_prompt'] = ""
            brand_prompt = st.text_area(
                "Brand tone of voice and guidelines",
                value=st.session_state['brand_prompt'],
                height=150,
                placeholder="Enter brand guidelines, tone of voice, style preferences...",
                key="brand_prompt_input",
                label_visibility="collapsed"
            )
            st.session_state['brand_prompt'] = brand_prompt

        # Task 1 Prompt
        with st.expander("📌 Task 1: Product Title Prompt", expanded=False):
            task1_upload = st.file_uploader("Upload title prompt (optional)", type=['txt'], key="task1_upload")
            if task1_upload:
                st.session_state['task1_prompt'] = task1_upload.read().decode('utf-8')
            if 'task1_prompt' not in st.session_state:
                st.session_state['task1_prompt'] = DEFAULT_TASK1_PROMPT
            task1_prompt = st.text_area(
                "Title generation prompt",
                value=st.session_state['task1_prompt'],
                height=150,
                key="task1_prompt_input",
                label_visibility="collapsed"
            )
            st.session_state['task1_prompt'] = task1_prompt

        # Task 2 Prompt
        with st.expander("📝 Task 2: Product Description Prompt", expanded=False):
            task2_upload = st.file_uploader("Upload description prompt (optional)", type=['txt'], key="task2_upload")
            if task2_upload:
                st.session_state['task2_prompt'] = task2_upload.read().decode('utf-8')
            if 'task2_prompt' not in st.session_state:
                st.session_state['task2_prompt'] = DEFAULT_TASK2_PROMPT
            task2_prompt = st.text_area(
                "Description generation prompt",
                value=st.session_state['task2_prompt'],
                height=400,
                key="task2_prompt_input",
                label_visibility="collapsed"
            )
            st.session_state['task2_prompt'] = task2_prompt

    # Tab 3: Settings
    with tab3:
        st.markdown('<p class="section-header">Settings</p>', unsafe_allow_html=True)

        # API Key Section
        with st.container(border=True):
            st.markdown("**🔑 OpenAI API Key**")

            # Check if API key is already in session state
            if 'api_key' not in st.session_state:
                st.session_state['api_key'] = ""

            api_key = st.text_input(
                "Enter your API key",
                value=st.session_state.get('api_key', ''),
                type="password",
                help="Your API key is stored in your browser session only",
                key="api_key_input",
                label_visibility="collapsed",
                placeholder="sk-..."
            )

            # Store in session state
            st.session_state['api_key'] = api_key

            if api_key:
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; background: #dcfce7; border-radius: 8px; margin-top: 0.5rem;">
                    <span style="color: #166534;">✓</span>
                    <span style="color: #166534; font-size: 0.9rem;">API key configured for this session</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; background: #fef3c7; border-radius: 8px; margin-top: 0.5rem;">
                    <span style="color: #92400e;">⚠</span>
                    <span style="color: #92400e; font-size: 0.9rem;">Please enter your OpenAI API key to continue</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Character Limits Section
        with st.container(border=True):
            st.markdown("**📏 Character Limits**")
            st.caption("Set the minimum, target, and maximum character counts for generated content")

            st.markdown("**Product Title**")
            col1, col2, col3 = st.columns(3)
            with col1:
                title_min = st.number_input("Minimum", value=30, key="title_min", help="Minimum characters for title")
            with col2:
                title_target = st.number_input("Target", value=50, key="title_target", help="Target characters for title")
            with col3:
                title_max = st.number_input("Maximum", value=60, key="title_max", help="Maximum characters for title")

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

            st.markdown("**Product Description**")
            col1, col2, col3 = st.columns(3)
            with col1:
                desc_min = st.number_input("Minimum", value=2000, key="desc_min", help="Minimum characters for description")
            with col2:
                desc_target = st.number_input("Target", value=2500, key="desc_target", help="Target characters for description")
            with col3:
                desc_max = st.number_input("Maximum", value=3000, key="desc_max", help="Maximum characters for description")

    # Tab 4: Generate
    with tab4:
        st.markdown('<p class="section-header">Generate Content</p>', unsafe_allow_html=True)

        # Get API key from session state
        api_key = st.session_state.get('api_key', '')

        # Check prerequisites with styled cards
        ready = True
        checklist_items = []

        if api_key:
            checklist_items.append(('✓', 'API Key', 'Configured', 'success'))
        else:
            checklist_items.append(('!', 'API Key', 'Not configured', 'error'))
            ready = False

        if 'product_data' in st.session_state:
            checklist_items.append(('✓', 'Product Data', f'{len(st.session_state["product_data"])} products loaded', 'success'))
        else:
            checklist_items.append(('!', 'Product Data', 'Not uploaded', 'error'))
            ready = False

        # Readiness checklist
        with st.container(border=True):
            st.markdown("**📋 Pre-flight Checklist**")

            for icon, label, status, state in checklist_items:
                color = '#166534' if state == 'success' else '#dc2626'
                bg = '#dcfce7' if state == 'success' else '#fee2e2'
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem; background: {bg}; border-radius: 8px; margin-bottom: 0.5rem;">
                    <span style="color: {color}; font-weight: 600;">{icon}</span>
                    <span style="color: {color}; font-weight: 500;">{label}:</span>
                    <span style="color: {color};">{status}</span>
                </div>
                """, unsafe_allow_html=True)

        if ready:
            num_products = len(st.session_state['product_data'])
            est_cost = num_products * 0.05

            # Initialize generation state if not exists
            if 'gen_state' not in st.session_state:
                st.session_state['gen_state'] = 'idle'  # idle, running, paused, stopped, completed

            gen_state = st.session_state.get('gen_state', 'idle')

            # Show different UI based on generation state
            if gen_state == 'idle':
                # Ready to start - show cost estimate and start button
                st.markdown(f"""
                <div class="ui-card" style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-color: #3b82f6;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #1e40af; font-size: 1.1rem;">Ready to Generate</div>
                            <div style="color: #1e40af; font-size: 0.9rem; margin-top: 0.25rem;">Estimated cost: ~${est_cost:.2f} (varies based on content)</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 2rem; font-weight: 700; color: #1e40af;">{num_products}</div>
                            <div style="font-size: 0.8rem; color: #1e40af;">products</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🚀 Start Generation", type="primary", use_container_width=True):
                    # Reset generation state
                    st.session_state['gen_state'] = 'running'
                    st.session_state['gen_results'] = []
                    st.session_state['gen_product_statuses'] = {}
                    st.session_state['gen_total_cost'] = 0.0
                    st.session_state['gen_total_input'] = 0
                    st.session_state['gen_total_output'] = 0
                    st.session_state['gen_image_stats'] = {'success': 0, 'failed': 0, 'no_images': 0}
                    st.session_state['gen_current_index'] = 0
                    st.session_state['gen_start_time'] = time.time()
                    st.session_state['gen_pause_requested'] = False
                    st.session_state['gen_stop_requested'] = False
                    st.rerun()

            elif gen_state in ['running', 'paused', 'stopped']:
                # Show progress UI
                current_idx = st.session_state.get('gen_current_index', 0)
                completed_count = len(st.session_state.get('gen_results', []))

                # State banner for paused/stopped
                if gen_state == 'paused':
                    st.markdown(f'''
                    <div class="state-banner paused">
                        <div class="state-banner-icon">⏸️</div>
                        <div class="state-banner-text">
                            <div class="state-banner-title">Generation Paused</div>
                            <div class="state-banner-subtitle">{completed_count} of {num_products} products completed</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                elif gen_state == 'stopped':
                    st.markdown(f'''
                    <div class="state-banner stopped">
                        <div class="state-banner-icon">⏹️</div>
                        <div class="state-banner-text">
                            <div class="state-banner-title">Generation Stopped</div>
                            <div class="state-banner-subtitle">{completed_count} of {num_products} products completed - partial results available</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                # Timeline
                timeline_container = st.empty()
                timeline_container.markdown(
                    render_timeline(num_products, current_idx, st.session_state.get('gen_product_statuses', {})),
                    unsafe_allow_html=True
                )

                # Live stats (pass start_time for JS-based real-time timer)
                stats_container = st.empty()
                start_time = st.session_state.get('gen_start_time', time.time())
                stats_container.markdown(
                    render_live_stats(completed_count, num_products, st.session_state.get('gen_total_cost', 0), start_time),
                    unsafe_allow_html=True
                )

                # Current product info
                current_product_container = st.empty()

                # Step indicators
                steps_container = st.empty()

                # Control buttons
                btn_col1, btn_col2, btn_col3 = st.columns(3)

                if gen_state == 'running':
                    with btn_col1:
                        if st.button("⏸️ Pause", use_container_width=True, key="pause_btn"):
                            st.session_state['gen_pause_requested'] = True

                    with btn_col2:
                        if st.button("⏹️ Stop", use_container_width=True, key="stop_btn"):
                            st.session_state['gen_stop_requested'] = True

                    with btn_col3:
                        st.button("Running...", use_container_width=True, disabled=True, key="running_placeholder")

                elif gen_state == 'paused':
                    with btn_col1:
                        if st.button("▶️ Resume", type="primary", use_container_width=True, key="resume_btn"):
                            st.session_state['gen_state'] = 'running'
                            st.rerun()

                    with btn_col2:
                        if st.button("⏹️ Stop", use_container_width=True, key="stop_paused_btn"):
                            st.session_state['gen_state'] = 'stopped'
                            st.rerun()

                    with btn_col3:
                        st.button("Paused", use_container_width=True, disabled=True, key="paused_placeholder")

                elif gen_state == 'stopped':
                    with btn_col1:
                        if st.button("🔄 Start Over", use_container_width=True, key="restart_btn"):
                            st.session_state['gen_state'] = 'idle'
                            st.session_state['gen_results'] = []
                            st.rerun()

                    with btn_col2:
                        if completed_count > 0:
                            if st.button("📥 Download Partial", type="primary", use_container_width=True, key="download_partial_btn"):
                                # Transfer partial results to main results
                                st.session_state['results'] = st.session_state['gen_results']
                                st.session_state['total_cost'] = st.session_state['gen_total_cost']
                                st.session_state['total_input'] = st.session_state['gen_total_input']
                                st.session_state['total_output'] = st.session_state['gen_total_output']
                                st.session_state['image_stats'] = st.session_state['gen_image_stats']
                                st.session_state['gen_state'] = 'idle'
                                st.rerun()

                    with btn_col3:
                        st.button("Stopped", use_container_width=True, disabled=True, key="stopped_placeholder")

                # Run generation if state is 'running'
                if gen_state == 'running':
                    try:
                        # Initialize LLM
                        llm = ChatOpenAI(
                            model="gpt-4o",
                            temperature=0.7,
                            max_tokens=4096,
                            api_key=api_key
                        )

                        # Prepare prompts and limits
                        prompts = {
                            'system': st.session_state['system_prompt'],
                            'brand': st.session_state.get('brand_prompt', ''),
                            'task1': st.session_state['task1_prompt'],
                            'task2': st.session_state['task2_prompt']
                        }

                        char_limits = {
                            'title_min': st.session_state.get('title_min', 30),
                            'title_target': st.session_state.get('title_target', 50),
                            'title_max': st.session_state.get('title_max', 60),
                            'desc_min': st.session_state.get('desc_min', 2000),
                            'desc_target': st.session_state.get('desc_target', 2500),
                            'desc_max': st.session_state.get('desc_max', 3000)
                        }

                        # UI containers
                        ui_containers = {
                            'timeline': timeline_container,
                            'stats': stats_container,
                            'current_product': current_product_container,
                            'steps': steps_container
                        }

                        # Run generation from current index
                        start_idx = st.session_state.get('gen_current_index', 0)
                        completed = run_generation(
                            llm,
                            st.session_state['product_data'],
                            st.session_state['general_info'],
                            prompts,
                            char_limits,
                            ui_containers,
                            start_index=start_idx
                        )

                        if completed:
                            # Transfer results to main session state
                            st.session_state['results'] = st.session_state['gen_results']
                            st.session_state['total_cost'] = st.session_state['gen_total_cost']
                            st.session_state['total_input'] = st.session_state['gen_total_input']
                            st.session_state['total_output'] = st.session_state['gen_total_output']
                            st.session_state['image_stats'] = st.session_state['gen_image_stats']
                            st.session_state['gen_state'] = 'idle'
                            st.rerun()
                        else:
                            # Paused or stopped - rerun to update UI
                            st.rerun()

                    except Exception as e:
                        st.error(f"Error during processing: {str(e)}")
                        st.session_state['gen_state'] = 'stopped'

        # Show results if available
        if 'results' in st.session_state:
            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

            st.markdown("""
            <div class="ui-card" style="background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-color: #22c55e;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 2rem;">✓</div>
                    <div>
                        <div style="font-weight: 600; color: #166534; font-size: 1.25rem;">Generation Complete</div>
                        <div style="color: #166534; font-size: 0.9rem;">Your product content has been generated successfully</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Token usage summary in styled cards
            st.markdown("#### Usage Summary")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="ui-card" style="text-align: center;">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #667eea;">{st.session_state['total_input']:,}</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.25rem;">Input Tokens</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="ui-card" style="text-align: center;">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #764ba2;">{st.session_state['total_output']:,}</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.25rem;">Output Tokens</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="ui-card" style="text-align: center; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #166534;">${st.session_state['total_cost']:.4f}</div>
                    <div style="font-size: 0.85rem; color: #166534; margin-top: 0.25rem;">Total Cost</div>
                </div>
                """, unsafe_allow_html=True)

            # Image processing summary
            if 'image_stats' in st.session_state:
                img_stats = st.session_state['image_stats']

                st.markdown("#### Image Processing")
                img_col1, img_col2, img_col3 = st.columns(3)

                with img_col1:
                    st.markdown(f"""
                    <div class="ui-card" style="text-align: center; border-left: 4px solid #22c55e;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #166534;">{img_stats.get('success', 0)}</div>
                        <div style="font-size: 0.8rem; color: #64748b;">Images Loaded</div>
                    </div>
                    """, unsafe_allow_html=True)

                with img_col2:
                    failed = img_stats.get('failed', 0)
                    st.markdown(f"""
                    <div class="ui-card" style="text-align: center; border-left: 4px solid {'#f59e0b' if failed > 0 else '#e2e8f0'};">
                        <div style="font-size: 1.5rem; font-weight: 700; color: {'#92400e' if failed > 0 else '#64748b'};">{failed}</div>
                        <div style="font-size: 0.8rem; color: #64748b;">Failed</div>
                    </div>
                    """, unsafe_allow_html=True)

                with img_col3:
                    st.markdown(f"""
                    <div class="ui-card" style="text-align: center; border-left: 4px solid #64748b;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #475569;">{img_stats.get('no_images', 0)}</div>
                        <div style="font-size: 0.8rem; color: #64748b;">No Images</div>
                    </div>
                    """, unsafe_allow_html=True)

                if img_stats.get('failed', 0) > 0:
                    st.warning(f"{img_stats['failed']} product(s) had image loading failures. These were processed using text only.")

            # Create download
            results_df = pd.DataFrame(st.session_state['results'])

            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                results_df.to_excel(writer, index=False, sheet_name='Results')
            output.seek(0)

            st.markdown("#### Next Steps")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Results",
                    data=output,
                    file_name="product_content_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                if st.button("👁️ Review Content", use_container_width=True, type="secondary"):
                    st.session_state['review_data'] = results_df.copy()
                    st.session_state['review_statuses'] = {}
                    st.session_state['current_review_index'] = 0
                    st.session_state['review_in_progress'] = True
                    st.rerun()

    # Tab 5: Review
    with tab5:
        st.markdown('<p class="section-header">Review Content</p>', unsafe_allow_html=True)

        # File upload for review (separate from generation)
        with st.expander("📁 Upload Results File", expanded=st.session_state.get('review_data') is None):
            review_upload = st.file_uploader(
                "Upload results Excel file",
                type=['xlsx', 'xls'],
                key="review_file_upload",
                help="Upload a previously generated results file or resume a review in progress"
            )

            if review_upload:
                # Check if review is in progress
                if st.session_state.get('review_in_progress') and st.session_state.get('review_data') is not None:
                    st.warning("⚠️ You have a review in progress. Uploading a new file will discard your current progress.")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Continue with current review", use_container_width=True):
                            st.rerun()
                    with col2:
                        if st.button("Load new file (discard progress)", type="primary", use_container_width=True):
                            st.session_state['review_in_progress'] = False
                            st.session_state['review_statuses'] = {}
                            st.session_state['current_review_index'] = 0
                            # Will load the file below
                else:
                    st.session_state['review_in_progress'] = False

                if not st.session_state.get('review_in_progress') or st.session_state.get('review_data') is None:
                    try:
                        # Try to load as multi-sheet (resumed review)
                        xlsx = pd.ExcelFile(review_upload, engine='openpyxl')
                        sheet_names = xlsx.sheet_names

                        if 'Reviewed' in sheet_names and 'Incorrect' in sheet_names and 'Un-Reviewed' in sheet_names:
                            # Resume review from categorized file
                            reviewed_df = pd.read_excel(xlsx, sheet_name='Reviewed')
                            incorrect_df = pd.read_excel(xlsx, sheet_name='Incorrect')
                            unreviewed_df = pd.read_excel(xlsx, sheet_name='Un-Reviewed')

                            # Filter out empty dataframes and combine
                            dfs_to_concat = [df for df in [reviewed_df, incorrect_df, unreviewed_df] if not df.empty]
                            if dfs_to_concat:
                                all_data = pd.concat(dfs_to_concat, ignore_index=True)
                            else:
                                all_data = pd.DataFrame()

                            if all_data.empty:
                                st.warning("The uploaded file contains no product data.")
                            else:
                                st.session_state['review_data'] = all_data
                                total_loaded = len(all_data)

                                # Reconstruct review statuses based on original positions
                                statuses = {}
                                approved_count = len(reviewed_df) if not reviewed_df.empty else 0
                                rejected_count = len(incorrect_df) if not incorrect_df.empty else 0
                                unreviewed_count = len(unreviewed_df) if not unreviewed_df.empty else 0

                                # Map indices: approved items first, then rejected, then un-reviewed
                                idx = 0
                                for i in range(approved_count):
                                    statuses[idx] = 'approved'
                                    idx += 1
                                for i in range(rejected_count):
                                    statuses[idx] = 'rejected'
                                    idx += 1
                                # Un-reviewed items don't have a status

                                st.session_state['review_statuses'] = statuses

                                # Start at first un-reviewed item, or at beginning if all reviewed
                                first_unreviewed = approved_count + rejected_count
                                if first_unreviewed >= total_loaded:
                                    # All items reviewed - start at beginning for re-review
                                    st.session_state['current_review_index'] = 0
                                else:
                                    st.session_state['current_review_index'] = first_unreviewed

                                st.session_state['review_in_progress'] = True

                                if unreviewed_count > 0:
                                    st.success(f"Resumed review: {approved_count} approved, {rejected_count} rejected, {unreviewed_count} remaining")
                                else:
                                    st.success(f"Loaded completed review: {approved_count} approved, {rejected_count} rejected. Starting from beginning for re-review.")
                                st.rerun()

                        elif 'Results' in sheet_names or 'Product Content' in sheet_names:
                            # Fresh results file
                            sheet_name = 'Results' if 'Results' in sheet_names else 'Product Content'
                            review_df = pd.read_excel(xlsx, sheet_name=sheet_name)
                            if review_df.empty:
                                st.warning("The uploaded file contains no product data.")
                            else:
                                st.session_state['review_data'] = review_df
                                st.session_state['review_statuses'] = {}
                                st.session_state['current_review_index'] = 0
                                st.session_state['review_in_progress'] = True
                                st.success(f"Loaded {len(review_df)} products for review")
                                st.rerun()
                        else:
                            # Try first sheet
                            review_df = pd.read_excel(xlsx, sheet_name=0)
                            if review_df.empty:
                                st.warning("The uploaded file contains no product data.")
                            else:
                                st.session_state['review_data'] = review_df
                                st.session_state['review_statuses'] = {}
                                st.session_state['current_review_index'] = 0
                                st.session_state['review_in_progress'] = True
                                st.success(f"Loaded {len(review_df)} products for review")
                                st.rerun()

                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")

        # Main review interface
        if st.session_state.get('review_data') is not None and len(st.session_state['review_data']) > 0:
            review_df = st.session_state['review_data']
            total_products = len(review_df)
            current_idx = st.session_state['current_review_index']
            statuses = st.session_state['review_statuses']

            # Calculate stats
            approved_count = sum(1 for s in statuses.values() if s == 'approved')
            rejected_count = sum(1 for s in statuses.values() if s == 'rejected')
            reviewed_count = approved_count + rejected_count
            unreviewed_count = total_products - reviewed_count

            # Progress header
            st.markdown(f"""
            <div class="ui-card" style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Reviewing</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b;">Product {current_idx + 1} of {total_products}</div>
                    </div>
                    <div style="display: flex; gap: 2rem; align-items: center;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: 700; color: #22c55e;">{approved_count}</div>
                            <div style="font-size: 0.75rem; color: #64748b;">Approved</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: 700; color: #ef4444;">{rejected_count}</div>
                            <div style="font-size: 0.75rem; color: #64748b;">Rejected</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: 700; color: #64748b;">{unreviewed_count}</div>
                            <div style="font-size: 0.75rem; color: #64748b;">Remaining</div>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 1rem; height: 6px; background: #e2e8f0; border-radius: 999px; overflow: hidden;">
                    <div style="display: flex; height: 100%;">
                        <div style="width: {(approved_count/total_products)*100}%; background: linear-gradient(90deg, #22c55e, #16a34a);"></div>
                        <div style="width: {(rejected_count/total_products)*100}%; background: linear-gradient(90deg, #ef4444, #dc2626);"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Get current product
            if current_idx < total_products:
                product = review_df.iloc[current_idx]
                current_status = statuses.get(current_idx)

                # Product card
                with st.container(border=True):
                    # Product header with status badge
                    status_html = ""
                    if current_status == 'approved':
                        status_html = '<span class="status-badge status-success">✓ Approved</span>'
                    elif current_status == 'rejected':
                        status_html = '<span class="status-badge status-error">✗ Rejected</span>'

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div>
                            <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">Product Name</div>
                            <h3 style="margin: 0; font-size: 1.35rem; font-weight: 600; color: #1e293b;">{product.get('Product Name', 'Unknown Product')}</h3>
                        </div>
                        {status_html}
                    </div>
                    """, unsafe_allow_html=True)

                    # Images
                    review_images = product.get('Review Images', '')
                    if pd.notna(review_images) and review_images:
                        image_urls = [url.strip() for url in str(review_images).split('\n') if url.strip()]
                        if image_urls:
                            st.markdown('<div style="font-size: 0.85rem; font-weight: 600; color: #64748b; margin-bottom: 0.75rem;">PRODUCT IMAGES</div>', unsafe_allow_html=True)
                            img_cols = st.columns(min(3, len(image_urls)))
                            for i, url in enumerate(image_urls[:3]):
                                with img_cols[i]:
                                    st.image(url, use_container_width=True)

                    # Title section
                    title_text = product.get('Product Title', '')
                    st.markdown(f"""
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.85rem; font-weight: 600; color: #64748b; margin-bottom: 0.5rem;">GENERATED TITLE</div>
                        <div class="product-title-display">
                            <div class="product-title-text">{title_text}</div>
                            <div class="char-count">{len(str(title_text))} characters</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Description section
                    st.markdown('<div style="font-size: 0.85rem; font-weight: 600; color: #64748b; margin-bottom: 0.5rem;">GENERATED DESCRIPTION</div>', unsafe_allow_html=True)
                    desc_text = product.get('Product Description', '')
                    st.text_area(
                        "Description",
                        value=desc_text,
                        height=280,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    st.markdown(f'<div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">{len(str(desc_text))} characters</div>', unsafe_allow_html=True)

                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

                # Action buttons in a card
                with st.container(border=True):
                    st.markdown('<div style="font-size: 0.85rem; font-weight: 600; color: #64748b; margin-bottom: 0.75rem;">REVIEW ACTIONS</div>', unsafe_allow_html=True)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        approve_clicked = st.button("✓ Approve", use_container_width=True, key="approve_btn")
                        if approve_clicked:
                            st.session_state['review_statuses'][current_idx] = 'approved'
                            if current_idx < total_products - 1:
                                st.session_state['current_review_index'] = current_idx + 1
                            st.rerun()

                    with col2:
                        reject_clicked = st.button("✗ Reject", use_container_width=True, key="reject_btn")
                        if reject_clicked:
                            st.session_state['review_statuses'][current_idx] = 'rejected'
                            if current_idx < total_products - 1:
                                st.session_state['current_review_index'] = current_idx + 1
                            st.rerun()

                    with col3:
                        skip_clicked = st.button("⏭ Skip", use_container_width=True, key="skip_btn")
                        if skip_clicked:
                            if current_idx in st.session_state['review_statuses']:
                                del st.session_state['review_statuses'][current_idx]
                            if current_idx < total_products - 1:
                                st.session_state['current_review_index'] = current_idx + 1
                            st.rerun()

                    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
                    st.markdown('<div style="font-size: 0.85rem; font-weight: 600; color: #64748b; margin-bottom: 0.75rem;">NAVIGATION</div>', unsafe_allow_html=True)

                    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])

                    with nav_col1:
                        if st.button("← Previous", use_container_width=True, disabled=current_idx == 0, key="prev_btn"):
                            st.session_state['current_review_index'] = current_idx - 1
                            st.rerun()

                    with nav_col2:
                        st.markdown(f"<div style='text-align: center; padding: 8px 0; color: #475569; font-weight: 600; font-size: 1.1rem;'>{current_idx + 1} / {total_products}</div>", unsafe_allow_html=True)

                    with nav_col3:
                        if st.button("Next →", use_container_width=True, disabled=current_idx >= total_products - 1, key="next_btn"):
                            st.session_state['current_review_index'] = current_idx + 1
                            st.rerun()

                    # Jump to specific product
                    jump_col1, jump_col2, jump_col3 = st.columns([1, 1, 1])
                    with jump_col2:
                        jump_to = st.number_input(
                            "Jump to",
                            min_value=1,
                            max_value=total_products,
                            value=current_idx + 1,
                            key="jump_to_input",
                            label_visibility="visible"
                        )
                        if jump_to != current_idx + 1:
                            st.session_state['current_review_index'] = jump_to - 1
                            st.rerun()

            # Download section
            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("**📥 Export Results**")

                # Prepare categorized data
                approved_indices = [i for i, s in statuses.items() if s == 'approved']
                rejected_indices = [i for i, s in statuses.items() if s == 'rejected']
                unreviewed_indices = [i for i in range(total_products) if i not in statuses]

                reviewed_df_out = review_df.iloc[approved_indices] if approved_indices else pd.DataFrame()
                incorrect_df_out = review_df.iloc[rejected_indices] if rejected_indices else pd.DataFrame()
                unreviewed_df_out = review_df.iloc[unreviewed_indices] if unreviewed_indices else pd.DataFrame()

                exp_col1, exp_col2, exp_col3 = st.columns(3)

                with exp_col1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0;">
                        <div style="font-size: 1.75rem; font-weight: 700; color: #166534;">{len(approved_indices)}</div>
                        <div style="font-size: 0.8rem; color: #166534;">Approved</div>
                    </div>
                    """, unsafe_allow_html=True)

                with exp_col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: #fef2f2; border-radius: 8px; border: 1px solid #fecaca;">
                        <div style="font-size: 1.75rem; font-weight: 700; color: #991b1b;">{len(rejected_indices)}</div>
                        <div style="font-size: 0.8rem; color: #991b1b;">Rejected</div>
                    </div>
                    """, unsafe_allow_html=True)

                with exp_col3:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <div style="font-size: 1.75rem; font-weight: 700; color: #475569;">{len(unreviewed_indices)}</div>
                        <div style="font-size: 0.8rem; color: #64748b;">Remaining</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

                # Create downloadable Excel with three sheets
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if not reviewed_df_out.empty:
                        reviewed_df_out.to_excel(writer, index=False, sheet_name='Reviewed')
                    else:
                        pd.DataFrame().to_excel(writer, index=False, sheet_name='Reviewed')

                    if not incorrect_df_out.empty:
                        incorrect_df_out.to_excel(writer, index=False, sheet_name='Incorrect')
                    else:
                        pd.DataFrame().to_excel(writer, index=False, sheet_name='Incorrect')

                    if not unreviewed_df_out.empty:
                        unreviewed_df_out.to_excel(writer, index=False, sheet_name='Un-Reviewed')
                    else:
                        pd.DataFrame().to_excel(writer, index=False, sheet_name='Un-Reviewed')

                output.seek(0)

                st.download_button(
                    label="📥 Download Categorized Results",
                    data=output,
                    file_name="product_content_reviewed.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )

                if len(unreviewed_indices) > 0:
                    st.caption(f"💡 Download includes {len(unreviewed_indices)} un-reviewed items in a separate sheet")

        else:
            # Empty state for Review tab
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">👁️</div>
                <div class="empty-state-title">No content to review</div>
                <div class="empty-state-text">Upload a results file above, or generate content in the Generate tab and click "Review Content"</div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
