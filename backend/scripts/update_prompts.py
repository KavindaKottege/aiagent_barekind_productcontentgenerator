"""
One-time script to update the default prompts in the database.
Run from backend directory: python scripts/update_prompts.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from app.database import async_session_maker
from app.models.settings import AppSettings


SYSTEM_PROMPT = """You are an expert product copywriter for online marketplaces. You create compelling, SEO-optimized content that drives sales while maintaining brand voice and accuracy."""

TASK1_PROMPT = """Craft a product title using relevant keywords from the product information and following this format: "Existing Product Name | Relevant Keyword #1 | Relevant Keyword #2" (e.g., "Octopus Figurine | Antique Brass Figure | Miniature Display")"""

TASK2_PROMPT = """Craft a product description based on the product title above following this format for product "Octopus Figurine | Antique Brass Figure | Miniature Display":

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
#5 No bold letters! No em dashes!


Here is an example product description for a different product but can be used as a starting point:


"Sleek, timeless, and effortlessly elevated, the Josie Twist Herringbone Bracelet is a waterproof, tarnish-proof essential designed for modern everyday wear.


This bracelet features a subtle twist on the classic herringbone pattern, crafted from 316L stainless steel and coated in 18K gold PVD for enduring shine and hypoallergenic comfort.


Wear it solo as a minimalist statement or layer it with other gold pieces for a polished, trend-forward look that transitions seamlessly from day to night.


Key Features:


- Elegant herringbone chain with a modern twist detail
- Waterproof, tarnish-proof, and hypoallergenic
- 316L stainless steel with durable 18K gold PVD finish
- Adjustable fit: 6.5" + 1.25" extender with secure clasp
- Designed in Vancouver, crafted in South Korea
- Lightweight, comfortable, and built for all-day wear


Construction & Materials:


- Made in South Korea
- Materials Used: 316L Stainless Steel, 18K Gold PVD Coating
- Dimensions: 6.5" + 1.25" Extender
- Care: Waterproof and tarnish-proof; simply wipe clean after wear


Style Guide:


- Colors: Gold
- Style: Minimalist, classic, and refined
- Theme: Everyday luxury and effortless confidence
- Occasion: Daily wear, work, gifting, travel, or layering collections
- Seasonality: Year-round essential with high gifting appeal


Retailer Information:


- Why We Made This: To offer a versatile waterproof bracelet that embodies timeless design and everyday practicality.
- Why You'll Love This: It's a proven bestseller material combination (18K Gold PVD on stainless steel), appealing to customers who want long-lasting jewelry that requires zero maintenance.
- Pairs Well With: Waterproof hoops, minimalist necklaces, or mixed metal stacks.
- Suitable for Retailers Such As: Fashion boutiques, gift shops, jewelry retailers, and lifestyle stores seeking durable, high-margin essentials that perform well year-round.


Lover's Tempo is a women-founded, Vancouver-based jewelry brand creating delicate, design-led pieces that bring a little romance to everyday life. Every collection is crafted to spark delight through thoughtful design, ethical production, and accessible luxury.


Offer effortless shine, year-round wearability, and unbeatable value to your customers with the Josie Twist Herringbone Bracelet."
"""

TASK3_PROMPT = """You are reviewing a product title written for this brand. Your role is to act as a strict editor, brand guardian, and compliance checker.

Review the product title below against the brands product title, brand story and description and complies with all the checks below.
If it does comply, then suggest that it is rejected and also pass back your suggested description which is an edited version of the generated description that complies with all of the below requirements.

Review the product title below against the brands product title brand story and description.

Evaluate the title on the following criteria:
    1.    Structure
Confirm it follows this format exactly:
Product Name | Primary Keyword | Secondary Keyword
    2.    Keyword quality
Check that keywords are specific, SEO Friendly, and shopper-friendly.
    3.    Clarity and hierarchy
Confirm the core product name is immediately clear and not overshadowed by descriptors.
    4.    Brand alignment
Assess whether the title feels connected to the brand story information. It doesnt have to be super close, but consider it
    5.    Readability
Confirm it sounds natural when read out loud and avoids robotic phrasing."""

TASK4_PROMPT = """You are reviewing a wholesale product description written for this brand. Your role is to act as a strict editor, brand guardian, and compliance checker.

Review the full output and check if the generated description complies with all the checks below.
If it does comply, then suggest that it is rejected and also pass back your suggested description which is an edited version of the generated description that complies with all of the below requirements. Do NOT rewrite everything from scratch unless absolutely necessary. Instead, identify issues and make precise corrections so the final copy fully meets the original prompt requirements.

Step 1: Structural & Compliance Check

Confirm the following and correct anything that is wrong:
    •    All required sections appear in the correct order.
    •    Paragraph 9 copies the Brand Story & CTA word-for-word with no edits.
    •    Paragraphs 10 and 11 exist and are formatted as single-line, comma-separated keyword lists.
    •    Paragraphs 10 and 11 each contain exactly 7 keyword phrases.

Step 2: Language & Style Audit

Check for common issues and fix them:
    •    Remove any bold text.
    •    Remove any em dashes and replace with periods or commas.
    •    Reduce overly poetic or vague language. Keep it clear, grounded, and retail-focused.
    •    Ensure the product name is treated as a proper noun throughout.
    •    Remove filler adjectives that do not help sell the product.

Step 3: Content Accuracy & Consistency

Verify that:
    •    Materials, dimensions, finishes, and country of origin match the input exactly. If these details do not exist in the input ensure that that the generated description has not made them up.
    •    Eco-friendly claims only appear if supported by the input.
    •    Use cases align with how a retailer would realistically merchandise the item.
    •    No features, benefits, or claims are invented or exaggerated.

Step 4: Retailer Lens Check
Ensure:
    •    The copy speaks to retailers, not just end consumers.
    •    Benefits emphasize ease of selling, gifting appeal, display value, and upsell potential.
    •    Language supports wholesale goals such as repeat orders, add-on sales, and broad customer appeal."""


async def update_prompts():
    async with async_session_maker() as session:
        result = await session.execute(select(AppSettings).where(AppSettings.id == 1))
        settings = result.scalar_one_or_none()

        if not settings:
            print("No settings found in database!")
            return

        # Update all prompts
        settings.default_system_prompt = SYSTEM_PROMPT
        settings.default_task1_prompt = TASK1_PROMPT
        settings.default_task2_prompt = TASK2_PROMPT
        settings.default_task3_prompt = TASK3_PROMPT
        settings.default_task4_prompt = TASK4_PROMPT

        await session.commit()

        print("✓ Prompts updated successfully!")
        print(f"  - System prompt: {len(SYSTEM_PROMPT)} chars")
        print(f"  - Task 1 prompt: {len(TASK1_PROMPT)} chars")
        print(f"  - Task 2 prompt: {len(TASK2_PROMPT)} chars")
        print(f"  - Task 3 prompt: {len(TASK3_PROMPT)} chars")
        print(f"  - Task 4 prompt: {len(TASK4_PROMPT)} chars")


if __name__ == "__main__":
    asyncio.run(update_prompts())
