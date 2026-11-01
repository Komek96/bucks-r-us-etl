import pandas as pd
from database import get_connection

STORES_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1LfF4pfY7aPECnZJHiw0YsY_AF7WRoNnB1PuFGnJ6npg/"
    "export?format=csv&gid=1763900964"
)

def validate_store_catalog(stores):
    """Validate incoming store records before database writes."""

    required_columns = {"store_id", "status", "closed_at"}
    missing_columns = required_columns - set(stores.columns)

    if missing_columns:
        raise ValueError(
            f"Missing store columns: {sorted(missing_columns)}"
        )

    if stores["store_id"].isna().any():
        raise ValueError("Store IDs cannot be missing.")

    if stores["store_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Store IDs cannot be blank.")

    if stores["store_id"].duplicated().any():
        raise ValueError("Duplicate store IDs in source data.")

    valid_statuses = {"active", "closed"}

    if not stores["status"].isin(valid_statuses).all():
        raise ValueError(
            "Invalid store status. Expected 'active' or 'closed'."
        )

    active_with_date = (
        stores["status"].eq("active")
        & stores["closed_at"].notna()
    )

    if active_with_date.any():
        raise ValueError(
            "Active stores cannot have a closure date."
        )

    closed_without_date = (
        stores["status"].eq("closed")
        & stores["closed_at"].isna()
    )

    if closed_without_date.any():
        raise ValueError(
            "Closed stores must have a closure date."
        )

    return stores


stores = pd.read_csv(STORES_URL)
try:
    stores["closed_at"] = pd.to_datetime(
        stores["closed_at"],
        errors="raise"
    )
except (ValueError, TypeError) as exc:
    raise ValueError(
        "Invalid closed_at date in store source data."
    ) from exc

validate_store_catalog(stores)
print("STORES READY FOR LOADING:")
print(stores.to_string(index=False))
print(f"\nTotal stores: {len(stores)}")
print("\nCLOSURE DATE CHECK:")
print(stores[["store_id", "closed_at"]].to_string(index=False))
print("\nColumn type:", stores["closed_at"].dtype)

with get_connection() as conn:
    with conn.cursor() as cursor:
        # Protect historical store closures.
        cursor.execute(
            """
            SELECT store_id
            FROM stores
            WHERE status = 'closed';
            """
        )

        closed_store_ids = {
            row[0] for row in cursor.fetchall()
        }

        incoming_active_ids = set(
            stores.loc[
                stores["status"] == "active",
                "store_id"
            ]
        )

        reopened_ids = (
            closed_store_ids & incoming_active_ids
        )

        if reopened_ids:
            raise ValueError(
                "Previously closed stores cannot be reopened: "
                + ", ".join(sorted(reopened_ids))
            )

        # Prevent historical closure dates from changing.
        incoming_closed = stores.loc[
            stores["status"] == "closed"
        ].set_index("store_id")["closed_at"]

        previously_closed_in_source = (
            closed_store_ids & set(incoming_closed.index)
        )

        if previously_closed_in_source:
            cursor.execute(
                """
                SELECT store_id, closed_at
                FROM stores
                WHERE status = 'closed'
                  AND store_id = ANY(%s);
                """,
                (sorted(previously_closed_in_source),),
            )

            changed_closure_dates = [
                store_id
                for store_id, existing_date in cursor.fetchall()
                if pd.Timestamp(existing_date)
                != incoming_closed.loc[store_id]
            ]

            if changed_closure_dates:
                raise ValueError(
                    "Historical store closure date cannot be changed: "
                    + ", ".join(sorted(changed_closure_dates))
                )

        for _, store in stores.iterrows():

            closed_at = (
                None
                if pd.isna(store["closed_at"])
                else store["closed_at"].to_pydatetime()
            )

            cursor.execute(
                """
                INSERT INTO stores (
                    store_id, address, city, state,
                    zip_code, status, closed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (store_id) DO UPDATE SET
                    address = EXCLUDED.address,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    zip_code = EXCLUDED.zip_code,
                    status = EXCLUDED.status,
                    closed_at = EXCLUDED.closed_at
                WHERE (
                    stores.address,
                    stores.city,
                    stores.state,
                    stores.zip_code,
                    stores.status,
                    stores.closed_at
                ) IS DISTINCT FROM (
                    EXCLUDED.address,
                    EXCLUDED.city,
                    EXCLUDED.state,
                    EXCLUDED.zip_code,
                    EXCLUDED.status,
                    EXCLUDED.closed_at
                );
                """,
                (
                    store["store_id"],
                    store["address"],
                    store["city"],
                    store["state"],
                    str(store["zip_code"]),
                    store["status"],
                    closed_at
                )
            )

            print(f"Processed store: {store['store_id']}")