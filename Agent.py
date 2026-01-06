# Import Libraries
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from tqdm import tqdm

# Character limits for each task (adjust these as needed)
TITLE_CHAR_MIN = 30
TITLE_CHAR_TARGET = 50
TITLE_CHAR_MAX = 60
DESCRIPTION_CHAR_MIN = 2000
DESCRIPTION_CHAR_TARGET = 2500
DESCRIPTION_CHAR_MAX = 3000

# Token pricing for GPT-4o (USD per token) - adjust if pricing changes
INPUT_TOKEN_COST = 2.50 / 1_000_000   # $2.50 per 1M input tokens
OUTPUT_TOKEN_COST = 10.00 / 1_000_000  # $10.00 per 1M output tokens

# Token usage tracking
token_usage = {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "total_cost": 0.0
}

# Initialize the model (GPT-4 Vision)
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4096,
)

# Import data
## Excel sheets
excel_path = "test_data.xlsx"
product_data = pd.read_excel(excel_path, sheet_name="Products")
general_data = pd.read_excel(excel_path, sheet_name="General Details", header=None)

## Text Files
with open("main_prompt_task1.txt", "r") as f:
    main_prompt_task1 = f.read()

with open("main_prompt_task2.txt", "r") as f:
    main_prompt_task2 = f.read()

with open("system_prompt.txt", "r") as f:
    system_prompt = f.read()

# Get general details (data stored as key-value pairs in columns A and B)
general_dict = dict(zip(general_data[0], general_data[1]))
language = general_dict["Language"]
brand_name = general_dict["Brand"]
brand_story = general_dict["Story"]


def create_image_content(image_urls_str):
    """Parse image URLs (space or newline separated) and create content list for vision model."""
    if pd.isna(image_urls_str) or not image_urls_str:
        return []

    # Replace newlines with spaces, then split by space and filter for URLs
    text = str(image_urls_str).replace("\n", " ")
    urls = [url.strip() for url in text.split() if url.strip().startswith("http")]

    image_content = []
    for url in urls:
        image_content.append({
            "type": "image_url",
            "image_url": {"url": url}
        })
    return image_content


def create_prompt_content(row, task_prompt):
    """Create the text content for the prompt."""
    text_content = f"""Input English Language to be used: {language}
Brand Name: {brand_name}
Brand Story: {brand_story}
Product Name: {row['Product Name']}
Product Category: {row['Product Category']}
Existing Product Description: {row['Product Description']}
SEO Key words input list: {row['SEO Details']}
Made in Country: {row['Made In']}

{task_prompt}"""
    return text_content


def invoke_agent(row, task_prompt):
    """Invoke the agent with text and images. Returns content and tracks token usage."""
    # Create text content
    text_content = create_prompt_content(row, task_prompt)

    # Create image content
    image_content = create_image_content(row.get('Images', ''))

    # Build the message content
    content = [{"type": "text", "text": text_content}]
    content.extend(image_content)

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=content)
    ]

    # Invoke the model
    response = llm.invoke(messages)

    # Track token usage
    usage = response.usage_metadata
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    call_cost = (input_tokens * INPUT_TOKEN_COST) + (output_tokens * OUTPUT_TOKEN_COST)

    token_usage["total_input_tokens"] += input_tokens
    token_usage["total_output_tokens"] += output_tokens
    token_usage["total_cost"] += call_cost

    return response.content, input_tokens, output_tokens, call_cost


def invoke_retry(previous_output, char_min, char_max, char_target, content_type="text"):
    """Lightweight retry that only sends the previous output for rewriting. Much cheaper than full invoke."""
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
        SystemMessage(content=f"You are a helpful assistant that rewrites text to meet character limits while preserving meaning."),
        HumanMessage(content=retry_prompt)
    ]

    response = llm.invoke(messages)

    # Track token usage
    usage = response.usage_metadata
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    call_cost = (input_tokens * INPUT_TOKEN_COST) + (output_tokens * OUTPUT_TOKEN_COST)

    token_usage["total_input_tokens"] += input_tokens
    token_usage["total_output_tokens"] += output_tokens
    token_usage["total_cost"] += call_cost

    return response.content, input_tokens, output_tokens, call_cost


# Loop Through Data - for each row in product_data
results = []

print(f"\n{'='*60}")
print(f"Starting product processing - {len(product_data)} products to process")
print(f"{'='*60}\n")

for idx, row in tqdm(product_data.iterrows(), total=len(product_data), desc="Overall Progress", unit="product"):
    product_name = row['Product Name']
    tqdm.write(f"\n[{idx + 1}/{len(product_data)}] Processing: {product_name}")

    # Get response for Prompt 1 (Product Title)
    tqdm.write("  ├─ Generating product title...")
    title_prompt_with_limit = main_prompt_task1 + f"\n\nSTRICT CHARACTER LIMIT: Your response MUST be between {TITLE_CHAR_MIN}-{TITLE_CHAR_MAX} characters. Aim for approximately {TITLE_CHAR_TARGET} characters."
    product_title, in_tok, out_tok, cost = invoke_agent(row, title_prompt_with_limit)
    tqdm.write(f"  │  Tokens: {in_tok} in / {out_tok} out | Cost: ${cost:.4f} | Running total: ${token_usage['total_cost']:.4f}")
    # Clean quotation marks from title
    product_title = product_title.strip().strip('"').strip("'")
    title_char_count = len(product_title)
    tqdm.write(f"  │  Character count: {title_char_count}")

    # Retry if title is not within character limits (lightweight retry - no images/full prompt)
    title_retry_count = 0
    title_max_retries = 3
    while (title_char_count < TITLE_CHAR_MIN or title_char_count > TITLE_CHAR_MAX) and title_retry_count < title_max_retries:
        title_retry_count += 1
        tqdm.write(f"  │  ⚠ Outside {TITLE_CHAR_MIN}-{TITLE_CHAR_MAX} range, retrying ({title_retry_count}/{title_max_retries})...")
        product_title, in_tok, out_tok, cost = invoke_retry(
            product_title, TITLE_CHAR_MIN, TITLE_CHAR_MAX, TITLE_CHAR_TARGET, "product title"
        )
        tqdm.write(f"  │  Tokens: {in_tok} in / {out_tok} out | Cost: ${cost:.4f} | Running total: ${token_usage['total_cost']:.4f}")
        product_title = product_title.strip().strip('"').strip("'")
        title_char_count = len(product_title)
        tqdm.write(f"  │  Character count: {title_char_count}")

    if title_char_count < TITLE_CHAR_MIN or title_char_count > TITLE_CHAR_MAX:
        tqdm.write(f"  │  ⚠ Warning: Final count {title_char_count} still outside range")
    else:
        tqdm.write("  │  ✓ Title generated")

    # Get response for Prompt 2 (Product Description)
    tqdm.write("  ├─ Generating product description...")
    desc_prompt_with_limit = main_prompt_task2 + f"\n\nSTRICT CHARACTER LIMIT: Your response MUST be between {DESCRIPTION_CHAR_MIN}-{DESCRIPTION_CHAR_MAX} characters. Aim for approximately {DESCRIPTION_CHAR_TARGET} characters."
    product_description, in_tok, out_tok, cost = invoke_agent(row, desc_prompt_with_limit)
    tqdm.write(f"  │  Tokens: {in_tok} in / {out_tok} out | Cost: ${cost:.4f} | Running total: ${token_usage['total_cost']:.4f}")
    char_count = len(product_description)
    tqdm.write(f"  │  Character count: {char_count}")

    # Retry if description is not within character limits (lightweight retry - no images/full prompt)
    retry_count = 0
    max_retries = 3
    while (char_count < DESCRIPTION_CHAR_MIN or char_count > DESCRIPTION_CHAR_MAX) and retry_count < max_retries:
        retry_count += 1
        tqdm.write(f"  │  ⚠ Outside {DESCRIPTION_CHAR_MIN}-{DESCRIPTION_CHAR_MAX} range, retrying ({retry_count}/{max_retries})...")
        product_description, in_tok, out_tok, cost = invoke_retry(
            product_description, DESCRIPTION_CHAR_MIN, DESCRIPTION_CHAR_MAX, DESCRIPTION_CHAR_TARGET, "product description"
        )
        tqdm.write(f"  │  Tokens: {in_tok} in / {out_tok} out | Cost: ${cost:.4f} | Running total: ${token_usage['total_cost']:.4f}")
        char_count = len(product_description)
        tqdm.write(f"  │  Character count: {char_count}")

    if char_count < DESCRIPTION_CHAR_MIN or char_count > DESCRIPTION_CHAR_MAX:
        tqdm.write(f"  │  ⚠ Warning: Final count {char_count} still outside range")
    else:
        tqdm.write("  │  ✓ Description generated")

    # Extract first 3 image URLs for review
    image_urls_str = row.get('Images', '')
    if pd.isna(image_urls_str) or not image_urls_str:
        review_images = ""
    else:
        text = str(image_urls_str).replace("\n", " ")
        urls = [url.strip() for url in text.split() if url.strip().startswith("http")]
        review_images = "\n".join(urls[:3])

    # Save response
    results.append({
        "Product Token": row["Product Token"],
        "Product Name": product_name,
        "Product Title": product_title,
        "Product Description": product_description,
        "Review Images": review_images
    })

    tqdm.write(f"  └─ ✓ Product complete!")

# Create response dataframe
product_data_response = pd.DataFrame(results)

# Write Data to file
output_path = "product_data_response.xlsx"
product_data_response.to_excel(output_path, index=False)
print(f"\nResults saved to {output_path}")

# Print token usage summary
print(f"\n{'='*60}")
print("TOKEN USAGE SUMMARY")
print(f"{'='*60}")
print(f"Total input tokens:  {token_usage['total_input_tokens']:,}")
print(f"Total output tokens: {token_usage['total_output_tokens']:,}")
print(f"Total tokens:        {token_usage['total_input_tokens'] + token_usage['total_output_tokens']:,}")
print(f"{'─'*60}")
print(f"TOTAL COST:          ${token_usage['total_cost']:.4f}")
print(f"{'='*60}")

# Finish
print("\nProcessing complete!")
