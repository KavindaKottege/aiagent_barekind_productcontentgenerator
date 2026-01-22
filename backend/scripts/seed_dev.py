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

        # Ensure settings row exists
        result = await session.execute(
            select(AppSettings).where(AppSettings.id == 1)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = AppSettings(id=1)
            session.add(settings)
            print("✓ Created settings row")
        else:
            print("ℹ Settings row already exists")

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
