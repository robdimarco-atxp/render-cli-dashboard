"""Async client for Render API."""
import httpx
from datetime import datetime
from typing import Optional
from dateutil import parser as dateparser

from ..models import Service, Deploy, ServiceStatus, DeployStatus


class RenderAPIError(Exception):
    """Error communicating with Render API."""
    pass


class RenderClient:
    """Async client for Render API."""

    BASE_URL = "https://api.render.com/v1"

    def __init__(self, api_key: str):
        """Initialize client with API key.

        Args:
            api_key: Render API key
        """
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an API request.

        Args:
            method: HTTP method
            path: API path (without base URL)
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response JSON as dict

        Raises:
            RenderAPIError: On API errors
        """
        if not self._client:
            raise RenderAPIError("Client not initialized. Use async context manager.")

        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RenderAPIError(
                    "Authentication failed. Check your RENDER_API_KEY is correct."
                )
            elif e.response.status_code == 404:
                raise RenderAPIError(f"Resource not found: {path}")
            elif e.response.status_code == 429:
                raise RenderAPIError(
                    "Rate limit exceeded. Please wait before refreshing."
                )
            else:
                raise RenderAPIError(
                    f"API error {e.response.status_code}: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise RenderAPIError(f"Network error: {e}")

    def _parse_deploy_status(self, status: str) -> DeployStatus:
        """Parse deploy status from API response."""
        try:
            return DeployStatus(status)
        except ValueError:
            # Unknown status, default to created
            return DeployStatus.CREATED

    def _parse_service_status(self, status: str) -> ServiceStatus:
        """Parse service status from API response."""
        # Map Render API status to our enum
        status_map = {
            "available": ServiceStatus.AVAILABLE,
            "deploying": ServiceStatus.DEPLOYING,
            "suspended": ServiceStatus.SUSPENDED,
            "failed": ServiceStatus.FAILED,
            "unavailable": ServiceStatus.FAILED,
        }
        return status_map.get(status.lower(), ServiceStatus.UNKNOWN)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not dt_str:
            return None
        try:
            return dateparser.isoparse(dt_str)
        except (ValueError, TypeError):
            return None

    async def get_service(self, service_id: str) -> Service:
        """Get service details and current status.

        Args:
            service_id: Render service ID

        Returns:
            Service object

        Raises:
            RenderAPIError: On API errors
        """
        data = await self._request("GET", f"/services/{service_id}")

        service_data = data.get("service", data)  # Handle wrapped or unwrapped response

        # Determine status - if actively deploying, mark as deploying
        status_str = service_data.get("status", "unknown")
        status = self._parse_service_status(status_str)

        service = Service(
            id=service_data["id"],
            name=service_data.get("name", service_id),
            type=service_data.get("type", "unknown"),
            status=status,
            url=service_data.get("serviceDetails", {}).get("url"),
        )

        return service

    async def get_latest_deploy(self, service_id: str) -> Optional[Deploy]:
        """Get the most recent deployment for a service.

        Args:
            service_id: Render service ID

        Returns:
            Deploy object or None if no deploys found

        Raises:
            RenderAPIError: On API errors
        """
        try:
            data = await self._request(
                "GET",
                f"/services/{service_id}/deploys",
                params={"limit": 1}
            )

            deploys = data.get("deploys", data) if isinstance(data, dict) else data
            if not deploys or not isinstance(deploys, list) or len(deploys) == 0:
                return None

            deploy_data = deploys[0]
            return Deploy(
                id=deploy_data["id"],
                status=self._parse_deploy_status(deploy_data.get("status", "created")),
                created_at=self._parse_datetime(deploy_data.get("createdAt")) or datetime.now(),
                finished_at=self._parse_datetime(deploy_data.get("finishedAt")),
            )
        except RenderAPIError:
            # If we can't get deploys, just return None rather than failing
            return None

    async def get_service_with_deploy(self, service_id: str) -> Service:
        """Get service details including latest deployment.

        Args:
            service_id: Render service ID

        Returns:
            Service object with latest_deploy populated

        Raises:
            RenderAPIError: On API errors
        """
        service = await self.get_service(service_id)

        # Override status if deployment is in progress
        latest_deploy = await self.get_latest_deploy(service_id)
        if latest_deploy and latest_deploy.is_in_progress:
            service.status = ServiceStatus.DEPLOYING

        service.latest_deploy = latest_deploy
        return service

    async def list_services(self, limit: int = 100) -> list[Service]:
        """List all services for the authenticated user.

        Args:
            limit: Maximum number of services to return (default 100)

        Returns:
            List of Service objects

        Raises:
            RenderAPIError: On API errors
        """
        try:
            data = await self._request("GET", "/services", params={"limit": limit})

            services_data = data if isinstance(data, list) else data.get("services", [])
            services = []

            for service_data in services_data:
                service = Service(
                    id=service_data["id"],
                    name=service_data.get("name", service_data["id"]),
                    type=service_data.get("type", "unknown"),
                    status=self._parse_service_status(service_data.get("status", "unknown")),
                    url=service_data.get("serviceDetails", {}).get("url"),
                )
                services.append(service)

            return services
        except RenderAPIError as e:
            raise e
