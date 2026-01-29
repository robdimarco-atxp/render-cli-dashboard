"""Async client for Render API."""
import httpx
from datetime import datetime
from typing import Optional
from dateutil import parser as dateparser

from ..models import Service, Deploy, ServiceStatus, DeployStatus
from ..cache import SimpleCache


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

        # Get custom domain if available
        custom_domain = None

        # Debug: Check both root and serviceDetails for customDomains
        import json
        print(f"DEBUG: Root service_data keys: {list(service_data.keys())}")

        # Check in root level first
        if "customDomains" in service_data:
            print(f"DEBUG: customDomains in ROOT: {json.dumps(service_data['customDomains'], indent=2)}")
            custom_domains = service_data["customDomains"]
            if isinstance(custom_domains, list) and len(custom_domains) > 0:
                domain_obj = custom_domains[0]
                custom_domain = domain_obj.get("name") or domain_obj.get("domain") or domain_obj.get("domainName")
                print(f"DEBUG: Found custom domain in root: {custom_domain}")

        # Also check in envSpecificDetails which might have environment-specific domains
        service_details = service_data.get("serviceDetails", {})
        env_specific = service_details.get("envSpecificDetails", {})
        if env_specific:
            print(f"DEBUG: envSpecificDetails keys: {list(env_specific.keys())}")
            if "customDomains" in env_specific:
                print(f"DEBUG: customDomains in envSpecificDetails: {json.dumps(env_specific['customDomains'], indent=2)}")

        service = Service(
            id=service_data["id"],
            name=service_data.get("name", service_id),
            type=service_data.get("type", "unknown"),
            status=status,
            url=service_data.get("serviceDetails", {}).get("url"),
            custom_domain=custom_domain,
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

            # Get deploy ID with fallback
            deploy_id = deploy_data.get("id") or deploy_data.get("deployId", "unknown")

            # Extract commit information
            commit_sha = None
            commit_message = None
            repo_url = None

            if "commit" in deploy_data and deploy_data["commit"]:
                commit_info = deploy_data["commit"]
                commit_sha = commit_info.get("id") or commit_info.get("sha")
                commit_message = commit_info.get("message")

            # Try to get repo URL from service or commit data
            if "gitRepoUrl" in deploy_data:
                repo_url = deploy_data["gitRepoUrl"]
            elif "commit" in deploy_data and deploy_data["commit"]:
                # Construct from commit data if available
                commit_info = deploy_data["commit"]
                if "gitRepoUrl" in commit_info:
                    repo_url = commit_info["gitRepoUrl"]

            # Clean up GitHub URL (remove .git suffix)
            if repo_url and repo_url.endswith(".git"):
                repo_url = repo_url[:-4]

            return Deploy(
                id=deploy_id,
                status=self._parse_deploy_status(deploy_data.get("status", "created")),
                created_at=self._parse_datetime(deploy_data.get("createdAt")) or datetime.now(),
                finished_at=self._parse_datetime(deploy_data.get("finishedAt")),
                commit_sha=commit_sha,
                commit_message=commit_message,
                repo_url=repo_url,
            )
        except (RenderAPIError, KeyError, IndexError, TypeError):
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

    async def list_services(self, limit: int = 100, use_cache: bool = True) -> list[Service]:
        """List all services for the authenticated user.

        Args:
            limit: Maximum number of services to return (default 100)
            use_cache: Whether to use cached results (default True, 5 min TTL)

        Returns:
            List of Service objects

        Raises:
            RenderAPIError: On API errors
        """
        # Check cache first
        cache = SimpleCache(ttl=300)  # 5 minute cache
        cache_key = f"services_list_{limit}"

        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                # Reconstruct Service objects from cached data
                return [
                    Service(
                        id=s["id"],
                        name=s["name"],
                        type=s["type"],
                        status=ServiceStatus(s["status"]),
                        url=s.get("url"),
                        custom_domain=s.get("custom_domain"),
                    )
                    for s in cached_data
                ]

        try:
            data = await self._request("GET", "/services", params={"limit": limit})

            # Handle different response formats
            if isinstance(data, list):
                services_data = data
            elif isinstance(data, dict):
                # Response might be wrapped in different ways
                services_data = data.get("services", data.get("data", []))
            else:
                services_data = []

            services = []

            for service_data in services_data:
                # Skip if not a dict
                if not isinstance(service_data, dict):
                    continue

                # Get required fields with fallbacks
                service_id = service_data.get("id") or service_data.get("serviceId")
                if not service_id:
                    # Skip services without IDs
                    continue

                # Get custom domain if available
                custom_domain = None
                service_details = service_data.get("serviceDetails", {})
                if service_details.get("customDomains"):
                    custom_domains = service_details["customDomains"]
                    if isinstance(custom_domains, list) and len(custom_domains) > 0:
                        custom_domain = custom_domains[0].get("name") or custom_domains[0].get("domain")

                service = Service(
                    id=service_id,
                    name=service_data.get("name", service_id),
                    type=service_data.get("type", "unknown"),
                    status=self._parse_service_status(service_data.get("status", "unknown")),
                    url=service_data.get("serviceDetails", {}).get("url"),
                    custom_domain=custom_domain,
                )
                services.append(service)

            # Cache the results
            if use_cache and services:
                cache_data = [
                    {
                        "id": s.id,
                        "name": s.name,
                        "type": s.type,
                        "status": s.status.value,
                        "url": s.url,
                        "custom_domain": s.custom_domain,
                    }
                    for s in services
                ]
                cache.set(cache_key, cache_data)

            return services
        except RenderAPIError as e:
            raise e
        except Exception as e:
            raise RenderAPIError(f"Error parsing service list: {e}")
