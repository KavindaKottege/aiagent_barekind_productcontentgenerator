import streamlit as st
import pandas as pd
import openpyxl  # Explicit import to ensure it's available
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Product Content Generator",
    page_icon="📝",
    layout="wide"
)

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


def process_products(llm, product_data, general_info, prompts, char_limits, progress_bar, status_text):
    """Process all products and return results."""
    results = []
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    image_stats = {'success': 0, 'failed': 0, 'no_images': 0}

    system_prompt = prompts['system']
    if prompts.get('brand'):
        system_prompt += f"\n\nBrand Guidelines:\n{prompts['brand']}"

    title_prompt = prompts['task1'] + f"\n\nSTRICT CHARACTER LIMIT: Your response MUST be between {char_limits['title_min']}-{char_limits['title_max']} characters. Aim for approximately {char_limits['title_target']} characters."
    desc_prompt = prompts['task2'] + f"\n\nSTRICT CHARACTER LIMIT: Your response MUST be between {char_limits['desc_min']}-{char_limits['desc_max']} characters. Aim for approximately {char_limits['desc_target']} characters."

    for idx, row in product_data.iterrows():
        product_name = row['Product Name']
        progress = (idx + 1) / len(product_data)
        progress_bar.progress(progress)

        # Generate title (with images)
        product_title, in_tok, out_tok, cost, title_img_info = invoke_agent(
            llm, row, title_prompt, system_prompt, general_info
        )
        total_input_tokens += in_tok
        total_output_tokens += out_tok
        total_cost += cost

        # Update status with image info
        img_status_icon = {"success": "✅", "failed": "⚠️", "no_images": "📝"}.get(title_img_info['status'], "❓")
        img_status_text = f"{img_status_icon} Images: {title_img_info['used']}/{title_img_info['available']}"
        if title_img_info['status'] == 'failed':
            img_status_text += " (failed to load, using text only)"
        status_text.text(f"Processing {idx + 1}/{len(product_data)}: {product_name} | {img_status_text}")

        # Track image stats (only count once per product, using title call)
        image_stats[title_img_info['status']] = image_stats.get(title_img_info['status'], 0) + 1

        product_title = product_title.strip().strip('"').strip("'")
        title_char_count = len(product_title)

        # Retry title if needed
        retry_count = 0
        while (title_char_count < char_limits['title_min'] or title_char_count > char_limits['title_max']) and retry_count < 3:
            retry_count += 1
            product_title, in_tok, out_tok, cost = invoke_retry(
                llm, product_title, char_limits['title_min'], char_limits['title_max'],
                char_limits['title_target'], "product title"
            )
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            total_cost += cost
            product_title = product_title.strip().strip('"').strip("'")
            title_char_count = len(product_title)

        # Generate description (with images)
        product_description, in_tok, out_tok, cost, desc_img_info = invoke_agent(
            llm, row, desc_prompt, system_prompt, general_info
        )
        total_input_tokens += in_tok
        total_output_tokens += out_tok
        total_cost += cost

        char_count = len(product_description)

        # Retry description if needed
        retry_count = 0
        while (char_count < char_limits['desc_min'] or char_count > char_limits['desc_max']) and retry_count < 3:
            retry_count += 1
            product_description, in_tok, out_tok, cost = invoke_retry(
                llm, product_description, char_limits['desc_min'], char_limits['desc_max'],
                char_limits['desc_target'], "product description"
            )
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            total_cost += cost
            char_count = len(product_description)

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

        results.append({
            "Product Token": row["Product Token"],
            "Product Name": product_name,
            "Product Title": product_title,
            "Product Description": product_description,
            "Images Status": img_status_str,
            "Review Images": review_images
        })

    return results, total_input_tokens, total_output_tokens, total_cost, image_stats


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
    st.title("📝 Product Content Generator")
    st.markdown("Generate product titles and descriptions using AI")

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📁 Data Upload", "📝 Prompts", "⚙️ Settings", "🚀 Generate", "👁️ Review"])

    # Tab 1: Data Upload
    with tab1:
        st.header("Upload Your Data")

        uploaded_file = st.file_uploader(
            "Upload Excel file with product data",
            type=['xlsx', 'xls'],
            help="Excel file should have 'Products' and 'General Details' sheets"
        )

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

                st.success(f"Loaded {len(product_data)} products")

                with st.expander("Preview Product Data"):
                    st.dataframe(product_data.head(10))

                with st.expander("General Details"):
                    st.write(f"**Language:** {st.session_state['general_info']['language']}")
                    st.write(f"**Brand:** {st.session_state['general_info']['brand_name']}")
                    st.write(f"**Story:** {st.session_state['general_info']['brand_story']}")

            except Exception as e:
                st.error(f"Error loading file: {str(e)}")

    # Tab 2: Prompts
    with tab2:
        st.header("Configure Prompts")

        # System Prompt
        with st.expander("System Prompt", expanded=False):
            system_upload = st.file_uploader("Upload system prompt (optional)", type=['txt'], key="system_upload")
            if system_upload:
                st.session_state['system_prompt'] = system_upload.read().decode('utf-8')
            if 'system_prompt' not in st.session_state:
                st.session_state['system_prompt'] = DEFAULT_SYSTEM_PROMPT
            system_prompt = st.text_area(
                "System prompt",
                value=st.session_state['system_prompt'],
                height=100,
                key="system_prompt_input"
            )
            st.session_state['system_prompt'] = system_prompt

        # Brand Prompt (Optional)
        with st.expander("Brand Guidelines (Optional)", expanded=False):
            st.markdown("*This will be appended to the system prompt if provided*")
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
                key="brand_prompt_input"
            )
            st.session_state['brand_prompt'] = brand_prompt

        # Task 1 Prompt
        with st.expander("Task 1: Product Title Prompt", expanded=False):
            task1_upload = st.file_uploader("Upload title prompt (optional)", type=['txt'], key="task1_upload")
            if task1_upload:
                st.session_state['task1_prompt'] = task1_upload.read().decode('utf-8')
            if 'task1_prompt' not in st.session_state:
                st.session_state['task1_prompt'] = DEFAULT_TASK1_PROMPT
            task1_prompt = st.text_area(
                "Title generation prompt",
                value=st.session_state['task1_prompt'],
                height=150,
                key="task1_prompt_input"
            )
            st.session_state['task1_prompt'] = task1_prompt

        # Task 2 Prompt
        with st.expander("Task 2: Product Description Prompt", expanded=False):
            task2_upload = st.file_uploader("Upload description prompt (optional)", type=['txt'], key="task2_upload")
            if task2_upload:
                st.session_state['task2_prompt'] = task2_upload.read().decode('utf-8')
            if 'task2_prompt' not in st.session_state:
                st.session_state['task2_prompt'] = DEFAULT_TASK2_PROMPT
            task2_prompt = st.text_area(
                "Description generation prompt",
                value=st.session_state['task2_prompt'],
                height=400,
                key="task2_prompt_input"
            )
            st.session_state['task2_prompt'] = task2_prompt

    # Tab 3: Settings
    with tab3:
        st.header("Settings")

        # API Key
        st.subheader("OpenAI API Key")

        # Check if API key is already in session state
        if 'api_key' not in st.session_state:
            st.session_state['api_key'] = ""

        api_key = st.text_input(
            "Enter your API key",
            value=st.session_state.get('api_key', ''),
            type="password",
            help="Your API key is stored in your browser session only",
            key="api_key_input"
        )

        # Store in session state
        st.session_state['api_key'] = api_key

        if api_key:
            st.success("✓ API key provided (stored for this session)")
            st.info("💡 **Tip:** Use your browser's password manager to save your API key for easier access in future sessions.")
        else:
            st.warning("Please enter your OpenAI API key")

        st.divider()

        # Character Limits
        st.subheader("Character Limits")

        st.markdown("**Title**")
        col1, col2, col3 = st.columns(3)
        title_min = col1.number_input("Min", value=30, key="title_min")
        title_target = col2.number_input("Target", value=50, key="title_target")
        title_max = col3.number_input("Max", value=60, key="title_max")

        st.markdown("**Description**")
        col1, col2, col3 = st.columns(3)
        desc_min = col1.number_input("Min", value=2000, key="desc_min")
        desc_target = col2.number_input("Target", value=2500, key="desc_target")
        desc_max = col3.number_input("Max", value=3000, key="desc_max")

    # Tab 4: Generate
    with tab4:
        st.header("Generate Content")

        # Get API key from session state
        api_key = st.session_state.get('api_key', '')

        # Check prerequisites
        ready = True
        if not api_key:
            st.error("Please enter your OpenAI API key in the Settings tab")
            ready = False
        if 'product_data' not in st.session_state:
            st.error("Please upload your product data in the Data Upload tab")
            ready = False

        if ready:
            st.success(f"Ready to process {len(st.session_state['product_data'])} products")

            # Cost estimate
            num_products = len(st.session_state['product_data'])
            est_cost = num_products * 0.05  # Rough estimate
            st.info(f"Estimated cost: ~${est_cost:.2f} (actual cost may vary based on content)")

            if st.button("🚀 Start Generation", type="primary", use_container_width=True):
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
                        'title_min': title_min,
                        'title_target': title_target,
                        'title_max': title_max,
                        'desc_min': desc_min,
                        'desc_target': desc_target,
                        'desc_max': desc_max
                    }

                    # Progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Process products
                    results, total_input, total_output, total_cost, image_stats = process_products(
                        llm,
                        st.session_state['product_data'],
                        st.session_state['general_info'],
                        prompts,
                        char_limits,
                        progress_bar,
                        status_text
                    )

                    status_text.text("Processing complete!")

                    # Store results
                    st.session_state['results'] = results
                    st.session_state['total_cost'] = total_cost
                    st.session_state['total_input'] = total_input
                    st.session_state['total_output'] = total_output
                    st.session_state['image_stats'] = image_stats

                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")

        # Show results if available
        if 'results' in st.session_state:
            st.divider()
            st.subheader("Results")

            # Token usage summary
            col1, col2, col3 = st.columns(3)
            col1.metric("Input Tokens", f"{st.session_state['total_input']:,}")
            col2.metric("Output Tokens", f"{st.session_state['total_output']:,}")
            col3.metric("Total Cost", f"${st.session_state['total_cost']:.4f}")

            # Image processing summary
            if 'image_stats' in st.session_state:
                img_stats = st.session_state['image_stats']
                st.markdown("**Image Processing Summary:**")
                col1, col2, col3 = st.columns(3)
                col1.metric("✅ Images Loaded", img_stats.get('success', 0))
                col2.metric("⚠️ Images Failed", img_stats.get('failed', 0))
                col3.metric("📝 No Images", img_stats.get('no_images', 0))

                if img_stats.get('failed', 0) > 0:
                    st.warning(f"{img_stats['failed']} product(s) had image loading failures. These were processed using text only.")

            # Create download
            results_df = pd.DataFrame(st.session_state['results'])

            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                results_df.to_excel(writer, index=False, sheet_name='Results')
            output.seek(0)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Results (Excel)",
                    data=output,
                    file_name="product_content_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                if st.button("👁️ Send to Review", use_container_width=True):
                    st.session_state['review_data'] = results_df.copy()
                    st.session_state['review_statuses'] = {}
                    st.session_state['current_review_index'] = 0
                    st.session_state['review_in_progress'] = True
                    st.success("Results sent to Review tab!")
                    st.rerun()

    # Tab 5: Review
    with tab5:
        st.header("Review Generated Content")

        # File upload for review (separate from generation)
        with st.expander("📁 Upload Results for Review", expanded=st.session_state.get('review_data') is None):
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

                            # Combine all into one dataframe
                            all_data = pd.concat([reviewed_df, incorrect_df, unreviewed_df], ignore_index=True)
                            st.session_state['review_data'] = all_data

                            # Reconstruct review statuses
                            statuses = {}
                            for i in range(len(reviewed_df)):
                                statuses[i] = 'approved'
                            for i in range(len(reviewed_df), len(reviewed_df) + len(incorrect_df)):
                                statuses[i] = 'rejected'
                            # Un-reviewed items don't have a status

                            st.session_state['review_statuses'] = statuses
                            st.session_state['current_review_index'] = len(reviewed_df) + len(incorrect_df)
                            st.session_state['review_in_progress'] = True

                            st.success(f"Resumed review: {len(reviewed_df)} approved, {len(incorrect_df)} rejected, {len(unreviewed_df)} remaining")

                        elif 'Results' in sheet_names or 'Product Content' in sheet_names:
                            # Fresh results file
                            sheet_name = 'Results' if 'Results' in sheet_names else 'Product Content'
                            review_df = pd.read_excel(xlsx, sheet_name=sheet_name)
                            st.session_state['review_data'] = review_df
                            st.session_state['review_statuses'] = {}
                            st.session_state['current_review_index'] = 0
                            st.session_state['review_in_progress'] = True
                            st.success(f"Loaded {len(review_df)} products for review")
                        else:
                            # Try first sheet
                            review_df = pd.read_excel(xlsx, sheet_name=0)
                            st.session_state['review_data'] = review_df
                            st.session_state['review_statuses'] = {}
                            st.session_state['current_review_index'] = 0
                            st.session_state['review_in_progress'] = True
                            st.success(f"Loaded {len(review_df)} products for review")

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

            # Header with progress
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"Product {current_idx + 1} of {total_products}")
            with col2:
                st.markdown(render_progress_ring(reviewed_count, total_products, approved_count, rejected_count), unsafe_allow_html=True)

            st.divider()

            # Get current product
            if current_idx < total_products:
                product = review_df.iloc[current_idx]

                # Product name
                st.markdown(f"### {product.get('Product Name', 'Unknown Product')}")

                # Images
                review_images = product.get('Review Images', '')
                if pd.notna(review_images) and review_images:
                    image_urls = [url.strip() for url in str(review_images).split('\n') if url.strip()]
                    if image_urls:
                        st.markdown("**Product Images:**")
                        img_cols = st.columns(min(3, len(image_urls)))
                        for i, url in enumerate(image_urls[:3]):
                            with img_cols[i]:
                                st.image(url, use_container_width=True)

                # Title
                st.markdown("**Generated Title:**")
                title_text = product.get('Product Title', '')
                st.info(title_text)
                st.caption(f"Character count: {len(str(title_text))}")

                # Description (scrollable)
                st.markdown("**Generated Description:**")
                desc_text = product.get('Product Description', '')
                st.text_area(
                    "Description",
                    value=desc_text,
                    height=300,
                    disabled=True,
                    label_visibility="collapsed"
                )
                st.caption(f"Character count: {len(str(desc_text))}")

                # Current status indicator
                current_status = statuses.get(current_idx)
                if current_status == 'approved':
                    st.success("✓ Marked as Approved")
                elif current_status == 'rejected':
                    st.error("✗ Marked as Incorrect")

                st.divider()

                # Action buttons with custom styled HTML
                st.markdown("**Review Actions:**")

                # Create custom HTML buttons for consistent styling
                button_html = f'''
                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <div style="flex: 1;" id="approve-container"></div>
                    <div style="flex: 1;" id="reject-container"></div>
                    <div style="flex: 1;" id="skip-container"></div>
                </div>
                <style>
                    /* Target approve button by key */
                    button[key="approve_btn"], div[data-testid="stButton"] button:has(p:contains("Approve")) {{
                        background-color: #28a745 !important;
                        border-color: #28a745 !important;
                        color: white !important;
                    }}
                    /* Green approve button - using aria label */
                    div[data-testid="stHorizontalBlock"] > div:first-child button {{
                        background-color: #28a745 !important;
                        border-color: #28a745 !important;
                        color: white !important;
                    }}
                    div[data-testid="stHorizontalBlock"] > div:first-child button:hover {{
                        background-color: #218838 !important;
                        border-color: #1e7e34 !important;
                    }}
                    /* Red reject button */
                    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {{
                        background-color: #dc3545 !important;
                        border-color: #dc3545 !important;
                        color: white !important;
                    }}
                    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover {{
                        background-color: #c82333 !important;
                        border-color: #bd2130 !important;
                    }}
                    /* Grey skip button */
                    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {{
                        background-color: #6c757d !important;
                        border-color: #6c757d !important;
                        color: white !important;
                    }}
                    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button:hover {{
                        background-color: #5a6268 !important;
                        border-color: #545b62 !important;
                    }}
                </style>
                '''
                st.markdown(button_html, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("✓ Approve", use_container_width=True, key="approve_btn"):
                        st.session_state['review_statuses'][current_idx] = 'approved'
                        if current_idx < total_products - 1:
                            st.session_state['current_review_index'] = current_idx + 1
                        st.rerun()

                with col2:
                    if st.button("✗ Reject", use_container_width=True, key="reject_btn"):
                        st.session_state['review_statuses'][current_idx] = 'rejected'
                        if current_idx < total_products - 1:
                            st.session_state['current_review_index'] = current_idx + 1
                        st.rerun()

                with col3:
                    if st.button("⏭️ Skip", use_container_width=True, key="skip_btn"):
                        # Remove any existing status (keep as un-reviewed)
                        if current_idx in st.session_state['review_statuses']:
                            del st.session_state['review_statuses'][current_idx]
                        if current_idx < total_products - 1:
                            st.session_state['current_review_index'] = current_idx + 1
                        st.rerun()

                # Navigation
                st.markdown("**Navigation:**")

                # Create a container with flexbox alignment
                nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])

                with nav_col1:
                    if st.button("← Previous", use_container_width=True, disabled=current_idx == 0, key="prev_btn"):
                        st.session_state['current_review_index'] = current_idx - 1
                        st.rerun()

                with nav_col2:
                    # Center the text showing current position
                    st.markdown(f"<div style='text-align: center; padding: 8px 0; color: #495057; font-weight: 500;'>{current_idx + 1} / {total_products}</div>", unsafe_allow_html=True)

                with nav_col3:
                    if st.button("Next →", use_container_width=True, disabled=current_idx >= total_products - 1, key="next_btn"):
                        st.session_state['current_review_index'] = current_idx + 1
                        st.rerun()

                # Jump to specific product (separate row)
                jump_col1, jump_col2, jump_col3 = st.columns([1, 1, 1])
                with jump_col2:
                    jump_to = st.number_input(
                        "Jump to product",
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
            st.divider()
            st.markdown("### Download Results")

            # Prepare categorized data
            approved_indices = [i for i, s in statuses.items() if s == 'approved']
            rejected_indices = [i for i, s in statuses.items() if s == 'rejected']
            unreviewed_indices = [i for i in range(total_products) if i not in statuses]

            reviewed_df_out = review_df.iloc[approved_indices] if approved_indices else pd.DataFrame()
            incorrect_df_out = review_df.iloc[rejected_indices] if rejected_indices else pd.DataFrame()
            unreviewed_df_out = review_df.iloc[unreviewed_indices] if unreviewed_indices else pd.DataFrame()

            col1, col2, col3 = st.columns(3)
            col1.metric("Approved", len(approved_indices))
            col2.metric("Incorrect", len(rejected_indices))
            col3.metric("Un-Reviewed", len(unreviewed_indices))

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
                st.info(f"💡 You can download at any time. Un-reviewed items ({len(unreviewed_indices)}) will be in a separate sheet.")

        else:
            st.info("No data to review. Either upload a results file above, or generate content in the Generate tab and click 'Send to Review'.")


if __name__ == "__main__":
    main()
