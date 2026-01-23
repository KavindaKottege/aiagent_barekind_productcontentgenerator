"""
Dev environment seeding script.
Creates admin user and sample data for immediate testing.

Run: python -m scripts.seed_dev

This script is idempotent - safe to run multiple times.
It will create the admin user if it doesn't exist, or skip if it already does.
"""
import asyncio

from sqlalchemy import select

from app.database import async_session_maker, engine
from app.models import AppSettings, Base, User
from app.utils.auth import hash_password


async def seed():
    """Seed the database with initial dev data."""
    print("🌱 Seeding dev environment...")

    # Create tables if they don't exist (for fresh setup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables verified")

    async with async_session_maker() as session:
        # Check if admin exists
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            # Create admin user
            admin = User(
                email="admin@example.com",
                name="Dev Admin",
                hashed_password=hash_password("password123"),
                is_admin=True,
            )
            session.add(admin)
            print("✓ Created admin user: admin@example.com / password123")
        else:
            print("ℹ Admin user already exists")

        # Ensure settings row exists with default prompts
        result = await session.execute(
            select(AppSettings).where(AppSettings.id == 1)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = AppSettings(
                id=1,
                default_task1_prompt='Craft a product title using relevant keywords from the list above and following on the following format: "Existing Product Name | Relevant Keyword #1 | Relevant Keyword #2" (e.g., "Octopus Figurine | Antique Brass Figure | Miniature Display")',
                default_task2_prompt='''Craft a product description based on the product title above following this format for product "Octopus Figurine | Antique Brass Figure | Miniature Display":

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

#5 No bold letters! No em dashes!'''
            )
            session.add(settings)
            print("✓ Created settings row with default prompts")
        else:
            # Update default prompts if they're None
            if settings.default_task1_prompt is None:
                settings.default_task1_prompt = 'Craft a product title using relevant keywords from the list above and following on the following format: "Existing Product Name | Relevant Keyword #1 | Relevant Keyword #2" (e.g., "Octopus Figurine | Antique Brass Figure | Miniature Display")'
            if settings.default_task2_prompt is None:
                settings.default_task2_prompt = '''Craft a product description based on the product title above following this format for product "Octopus Figurine | Antique Brass Figure | Miniature Display":

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

#5 No bold letters! No em dashes!'''
            print("ℹ Settings row already exists (default prompts updated if missing)")

        await session.commit()

    print("\n✨ Seeding complete!")
    print("\nDev credentials:")
    print("  Email: admin@example.com")
    print("  Password: password123")
    print("\nNext steps:")
    print("  1. Start backend: uvicorn app.main:app --reload")
    print("  2. Start frontend: cd frontend && npm run dev")
    print("  3. Login at: http://localhost:3000/login")


if __name__ == "__main__":
    asyncio.run(seed())
