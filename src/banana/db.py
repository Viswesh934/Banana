import time
from typing import Any, Optional
import falkordb
from banana.config import Settings, get_settings


class DatabaseConnectionError(Exception):
    """Raised when connecting or performing health check with FalkorDB fails."""
    pass


class FalkorDBClient:
    """Manager for FalkorDB connections and graph operations."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._client: Optional[falkordb.FalkorDB] = None

    @property
    def client(self) -> falkordb.FalkorDB:
        """Lazily initialize and return FalkorDB client instance (local or cloud)."""
        if self._client is None:
            if self.settings.falkordb_url:
                self._client = falkordb.FalkorDB.from_url(self.settings.falkordb_url)
            else:
                self._client = falkordb.FalkorDB(
                    host=self.settings.falkordb_host,
                    port=self.settings.falkordb_port,
                    username=self.settings.falkordb_username,
                    password=self.settings.falkordb_password,
                    ssl=self.settings.falkordb_ssl,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
        return self._client

    def get_graph(self, name: str) -> falkordb.Graph:
        """Return a Graph handle for the given graph name."""
        return self.client.select_graph(name)

    def get_demand_graph(self) -> falkordb.Graph:
        """Return the demand graph handle."""
        return self.get_graph(self.settings.demand_graph_name)

    def get_knowledge_graph(self) -> falkordb.Graph:
        """Return the knowledge graph handle."""
        return self.get_graph(self.settings.knowledge_graph_name)

    def check_connection(self) -> dict[str, Any]:
        """Verify connectivity and read/write capabilities on FalkorDB.

        Performs:
        1. Ping/connection check.
        2. Test node write (`BananaHealthCheck`).
        3. Test node read.
        4. Test node cleanup.
        5. Roundtrip latency measurement.

        Returns:
            dict containing status, latency_ms, read_write_verified, host, port, error.
        """
        start_time = time.perf_counter()
        test_graph_name = f"{self.settings.demand_graph_name}_health"
        test_id = f"health_check_{int(time.time() * 1000)}"

        try:
            # 1. Connect and select temporary graph
            graph = self.get_graph(test_graph_name)

            # 2. Write test node
            create_query = (
                "CREATE (n:BananaHealthCheck {id: $id, timestamp: timestamp(), status: 'active'}) "
                "RETURN n.id AS id"
            )
            create_res = graph.query(create_query, {"id": test_id})
            if not create_res.result_set or create_res.result_set[0][0] != test_id:
                raise DatabaseConnectionError(
                    f"FalkorDB write verification failed: expected id {test_id}"
                )

            # 3. Read back test node
            read_query = "MATCH (n:BananaHealthCheck {id: $id}) RETURN n.id AS id, n.status AS status"
            read_res = graph.query(read_query, {"id": test_id})
            if (
                not read_res.result_set
                or read_res.result_set[0][0] != test_id
                or read_res.result_set[0][1] != "active"
            ):
                raise DatabaseConnectionError(
                    f"FalkorDB read verification failed for test node id {test_id}"
                )

            # 4. Clean up test node and delete temporary test graph
            graph.query("MATCH (n:BananaHealthCheck {id: $id}) DELETE n", {"id": test_id})
            graph.delete()

            duration_ms = (time.perf_counter() - start_time) * 1000
            import re
            target_display = self.settings.falkordb_url or f"{self.settings.falkordb_host}:{self.settings.falkordb_port}"
            masked_target = re.sub(r":([^@/]+)@", r":***@", target_display) if "@" in target_display else target_display

            return {
                "status": "ok",
                "host": masked_target,
                "port": self.settings.falkordb_port,
                "latency_ms": round(duration_ms, 2),
                "read_write_verified": True,
                "error": None,
            }

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            import re
            target_display = self.settings.falkordb_url or f"{self.settings.falkordb_host}:{self.settings.falkordb_port}"
            masked_target = re.sub(r":([^@/]+)@", r":***@", target_display) if "@" in target_display else target_display
            err_msg = str(exc)
            hint = ""
            if "Connection refused" in err_msg or "Cannot connect" in err_msg:
                hint = f" Ensure FalkorDB is reachable at {masked_target}."
            return {
                "status": "error",
                "host": masked_target,
                "port": self.settings.falkordb_port,
                "latency_ms": round(duration_ms, 2),
                "read_write_verified": False,
                "error": f"{err_msg}.{hint}",
            }


_db_client_instance: Optional[FalkorDBClient] = None


def get_db_client() -> FalkorDBClient:
    """Return a singleton FalkorDBClient instance."""
    global _db_client_instance
    if _db_client_instance is None:
        _db_client_instance = FalkorDBClient()
    return _db_client_instance
