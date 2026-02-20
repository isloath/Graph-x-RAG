from __future__ import annotations

from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass

from neo4j import GraphDatabase

from app.models.schemas import ApplicationIn


@dataclass
class GraphRepository:
    uri: str
    user: str
    password: str

    def __post_init__(self) -> None:
        auth = (self.user, self.password) if self.user else None
        self.driver = GraphDatabase.driver(self.uri, auth=auth)

    def close(self) -> None:
        with suppress(Exception):
            self.driver.close()

    async def ensure_indexes(self) -> None:
        queries = [
            "CREATE INDEX ON :Application(application_id);",
            "CREATE INDEX ON :Phone(value);",
            "CREATE INDEX ON :Email(value);",
            "CREATE INDEX ON :Document(value);",
            "CREATE INDEX ON :Device(value);",
            "CREATE INDEX ON :Account(value);",
            "CREATE INDEX ON :Wallet(value);",
        ]
        with self.driver.session() as session:
            for query in queries:
                with suppress(Exception):
                    session.run(query).consume()

    async def reset(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n;").consume()

    async def ingest_applications(self, applications: Iterable[ApplicationIn]) -> int:
        count = 0
        with self.driver.session() as session:
            for app in applications:
                session.run(
                    """
                    MERGE (a:Application {application_id: $application_id})
                    SET a.customer_id=$customer_id,
                        a.created_at=datetime($created_at),
                        a.loan_amount=$loan_amount,
                        a.status=$status,
                        a.phone=$phone,
                        a.email=$email,
                        a.document_id=$document_id,
                        a.device_id=$device_id,
                        a.bank_account=$bank_account,
                        a.wallet_id=$wallet_id
                    """,
                    application_id=app.application_id,
                    customer_id=app.customer_id,
                    created_at=app.created_at.isoformat(),
                    loan_amount=app.loan_amount,
                    status=app.status.value,
                    phone=app.phone,
                    email=app.email,
                    document_id=app.document_id,
                    device_id=app.device_id,
                    bank_account=app.bank_account,
                    wallet_id=app.wallet_id,
                ).consume()
                self._link_identifier(session, app.application_id, "Phone", app.phone)
                self._link_identifier(session, app.application_id, "Email", app.email)
                self._link_identifier(session, app.application_id, "Document", app.document_id)
                self._link_identifier(session, app.application_id, "Device", app.device_id)
                self._link_identifier(session, app.application_id, "Account", app.bank_account)
                self._link_identifier(session, app.application_id, "Wallet", app.wallet_id)
                count += 1
        return count

    def _link_identifier(self, session, application_id: str, label: str, value: str | None) -> None:
        if not value:
            return
        session.run(
            f"""
            MATCH (a:Application {{application_id: $application_id}})
            MERGE (i:{label} {{value: $value}})
            MERGE (a)-[:HAS_IDENTIFIER]->(i)
            MERGE (i)-[:IDENTIFIES]->(a)
            """,
            application_id=application_id,
            value=value,
        ).consume()

    async def list_applications(self, page: int, page_size: int) -> tuple[list[dict], int]:
        skip = (page - 1) * page_size
        with self.driver.session() as session:
            total = (
                session.run("MATCH (a:Application) RETURN count(a) as total")
                .single()["total"]
            )
            rows = session.run(
                """
                MATCH (a:Application)
                RETURN a
                ORDER BY a.created_at DESC
                SKIP $skip LIMIT $limit
                """,
                skip=skip,
                limit=page_size,
            )
            apps = [record["a"] for record in rows]
            return apps, int(total)

    async def get_application(self, application_id: str) -> dict | None:
        with self.driver.session() as session:
            record = session.run(
                "MATCH (a:Application {application_id: $application_id}) RETURN a",
                application_id=application_id,
            ).single()
            return dict(record["a"]) if record else None

    async def identifier_degree(self, label: str, value: str) -> int:
        with self.driver.session() as session:
            record = session.run(
                f"MATCH (i:{label} {{value: $value}})<-[:HAS_IDENTIFIER]-(a:Application) RETURN count(a) as degree",
                value=value,
            ).single()
            return int(record["degree"]) if record else 0

    async def run_louvain(self) -> None:
        query = """
        CALL community_detection.get_subgraph(
            "MATCH (n) RETURN id(n) as id",
            "MATCH (a:Application)-[:HAS_IDENTIFIER]->(i) RETURN id(a) as source, id(i) as target"
        ) YIELD graph
        CALL community_detection_online.louvain(graph) YIELD node, community_id
        WITH node, community_id
        MATCH (a:Application) WHERE id(a)=node
        SET a.community_id = toString(community_id)
        RETURN count(*) as updated;
        """
        with self.driver.session() as session:
            session.run(query).consume()

    async def get_community(self, application_id: str) -> tuple[str | None, int]:
        with self.driver.session() as session:
            record = session.run(
                """
                MATCH (a:Application {application_id:$application_id})
                OPTIONAL MATCH (x:Application {community_id: a.community_id})
                RETURN a.community_id as cid, count(x) as size
                """,
                application_id=application_id,
            ).single()
            if not record:
                return None, 0
            return record["cid"], int(record["size"])

    async def list_fraud_rings(self, min_size: int = 5) -> list[dict]:
        with self.driver.session() as session:
            rows = session.run(
                """
                MATCH (a:Application)
                WHERE a.community_id IS NOT NULL
                WITH a.community_id as cid, collect(a.application_id) as apps
                WHERE size(apps) >= $min_size
                RETURN cid, size(apps) as size, apps
                ORDER BY size DESC
                """,
                min_size=min_size,
            )
            return [
                {"community_id": r["cid"], "size": int(r["size"]), "applications": r["apps"]}
                for r in rows
            ]

    async def subgraph_for_application(self, application_id: str, hops: int = 2) -> list[str]:
        with self.driver.session() as session:
            rows = session.run(
                """
                MATCH p=(a:Application {application_id:$application_id})-[*1..2]-(n)
                RETURN DISTINCT p LIMIT 25
                """,
                application_id=application_id,
            )
            texts: list[str] = []
            for row in rows:
                texts.append(str(row["p"]))
            return texts
