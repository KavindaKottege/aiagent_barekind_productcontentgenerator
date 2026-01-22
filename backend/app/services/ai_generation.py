"""AI Generation Service - stub for worker infrastructure setup.

Full implementation will be created in plan 04-02.
This stub allows worker infrastructure (04-03) to be set up independently.
"""

from decimal import Decimal
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cost_tracker import CostTracker


class AIGenerationService:
    """
    AI Generation Service stub.

    Real implementation will be in plan 04-02.
    This stub allows imports to work during worker setup.
    """

    def __init__(
        self,
        db: AsyncSession,
        api_key: str,
        model: str,
        temperature: float,
    ):
        self.db = db
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.cost_tracker = CostTracker()

    async def generate_content(
        self,
        product_group: Any,
        client: Any,
        job: Any,
        app_settings: Any,
    ) -> tuple[Any, Any]:
        """Stub method - will be implemented in 04-02."""
        raise NotImplementedError("AIGenerationService.generate_content will be implemented in plan 04-02")
