from datetime import datetime, timezone
from sqlalchemy import DateTime, bindparam, text
from app.infrastructure.database.database import engine

CLOUD_NAME_MAPPING = {
    "cirrus": "Cirros",
    "cirrocumulus": "Cirrocúmulos",
    "cirrostratus": "Cirrostratos",
    "altocumulus": "Altocúmulos",
    "altostratus": "Altoestratos",
    "nimbostratus": "Nimboestratos",
    "stratocumulus": "Estratocúmulos",
    "stratus": "Estratos",
    "cumulus": "Cúmulos",
    "cumulonimbus": "Cumulonimbos",
    "contrail": "Estelas de avión",
    "no_cloud": "Sin nubes"
}

class AnalysisRepository:

    CANCEL_NOT_FOUND = "not_found"
    CANCEL_INVALID_STATUS = "invalid_status"
    CANCEL_CANCELLED = "cancelled"

    def __init__(self, db=None):
        self.db = db

    def _execute(self, query, params=None):
        return self.db.execute(query, params or {})

    def create_analysis(
        self,
        uid: str,
        image_path: str,
        location: str,
        latitude: float | None,
        longitude: float | None,
        is_anon: bool,
    ) -> int:
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).create_analysis(
                    uid=uid,
                    image_path=image_path,
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    is_anon=is_anon,
                )

        # `analysis.datetime` is a TIMESTAMP WITHOUT TIME ZONE. Its DB default
        # (CURRENT_TIMESTAMP) is expressed in the DB session time zone on PostgreSQL,
        # so we always store an explicit naive-UTC value instead. The API layer then
        # reads stored values as UTC.
        result = self._execute(
            text("""
                INSERT INTO analysis (uid, image_path, location, latitude, longitude, is_anon, status, datetime)
                VALUES (:uid, :image_path, :location, :latitude, :longitude, :is_anon, 'analyzing', :datetime)
                RETURNING id
            """).bindparams(bindparam("datetime", type_=DateTime)),
            {
                "uid": uid,
                "image_path": image_path,
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "is_anon": is_anon,
                "datetime": datetime.now(timezone.utc).replace(tzinfo=None),
            },
        )
        return result.scalar()

    _ANALYSIS_ROWS_SELECT = """
            SELECT
                a.id,
                a.status,
                a.datetime,
                a.location,
                a.latitude,
                a.longitude,
                a.image_path,
                ac.box_ymin,
                ac.box_xmin,
                ac.box_ymax,
                ac.box_xmax,
                c.name as cloud_type,
                c.forecast,
                c.warning,
                c.warning_level
            FROM {source} a
            LEFT JOIN analysis_cloud ac ON a.id = ac.analysis_id
            LEFT JOIN clouds c ON ac.cloud_id = c.id
            ORDER BY a.datetime DESC, a.id DESC
        """

    def get_history_rows(self, uid: str, limit: int = 50, offset: int = 0):
        """Rows (analysis x detected clouds) for one page of the user's analyses, newest first."""
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).get_history_rows(uid, limit, offset)

        source = (
            "(SELECT * FROM analysis WHERE uid = :uid "
            "ORDER BY datetime DESC, id DESC LIMIT :limit OFFSET :offset)"
        )
        query = text(self._ANALYSIS_ROWS_SELECT.format(source=source))
        return self._execute(query, {"uid": uid, "limit": limit, "offset": offset}).fetchall()

    def count_user_analyses(self, uid: str) -> int:
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).count_user_analyses(uid)

        return self._execute(
            text("SELECT COUNT(*) FROM analysis WHERE uid = :uid"), {"uid": uid}
        ).scalar() or 0

    def get_analysis_rows(self, analysis_id: int, uid: str):
        """Rows (analysis x detected clouds) for one analysis owned by uid; empty if none."""
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).get_analysis_rows(analysis_id, uid)

        source = "(SELECT * FROM analysis WHERE id = :id AND uid = :uid)"
        query = text(self._ANALYSIS_ROWS_SELECT.format(source=source))
        return self._execute(query, {"id": analysis_id, "uid": uid}).fetchall()

    def delete_user_analyses(self, uid: str) -> list[str]:
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).delete_user_analyses(uid)

        analyses = self._execute(
            text("SELECT id, image_path FROM analysis WHERE uid = :uid"),
            {"uid": uid},
        ).fetchall()

        for row in analyses:
            self._execute(
                text("DELETE FROM analysis_cloud WHERE analysis_id = :id"),
                {"id": row.id},
            )
            self._execute(
                text("DELETE FROM analysis WHERE id = :id"),
                {"id": row.id},
            )

        return [row.image_path for row in analyses if row.image_path]

    def delete_analysis(self, analysis_id: int, uid: str) -> str | None:
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).delete_analysis(analysis_id, uid)

        analysis = self._execute(
            text("SELECT id, image_path FROM analysis WHERE id = :id AND uid = :uid"),
            {"id": analysis_id, "uid": uid},
        ).fetchone()

        if not analysis:
            return None

        self._execute(
            text("DELETE FROM analysis_cloud WHERE analysis_id = :id"),
            {"id": analysis_id},
        )
        self._execute(
            text("DELETE FROM analysis WHERE id = :id"),
            {"id": analysis_id},
        )

        return analysis.image_path

    def get_analysis_status(self, analysis_id: int) -> str | None:
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).get_analysis_status(analysis_id)

        result = self._execute(
            text("SELECT status FROM analysis WHERE id = :id"),
            {"id": analysis_id},
        ).fetchone()
        return result.status if result else None

    def cancel_analysis(self, analysis_id: int, uid: str) -> str:
        if self.db is None:
            with engine.begin() as conn:
                return AnalysisRepository(conn).cancel_analysis(analysis_id, uid)

        analysis = self._execute(
            text("SELECT id, status FROM analysis WHERE id = :id AND uid = :uid"),
            {"id": analysis_id, "uid": uid},
        ).fetchone()

        if not analysis:
            return self.CANCEL_NOT_FOUND

        if analysis.status != "analyzing":
            return self.CANCEL_INVALID_STATUS

        self._execute(
            text("UPDATE analysis SET status = 'cancelled' WHERE id = :id"),
            {"id": analysis_id},
        )
        return self.CANCEL_CANCELLED

    def update_status(self, analysis_id: int, status: str):
        if self.db is not None:
            self._execute(
                text("UPDATE analysis SET status = :status WHERE id = :id"), 
                {"status": status, "id": analysis_id}
            )
            return

        with engine.begin() as conn:
            conn.execute(
                text("UPDATE analysis SET status = :status WHERE id = :id"),
                {"status": status, "id": analysis_id},
            )

    def _mapped_cloud_name(self, prediction: dict) -> str | None:
        label = prediction.get("label")
        return CLOUD_NAME_MAPPING.get(label.lower() if label else "")

    def _get_cloud_id(self, conn, cloud_name: str):
        cloud_query = text("SELECT id FROM clouds WHERE name = :name")
        return conn.execute(cloud_query, {"name": cloud_name}).scalar()

    def _extract_box(self, prediction: dict):
        box_2d = prediction.get("box_2d")
        if isinstance(box_2d, list) and len(box_2d) == 4:
            return box_2d
        return (None, None, None, None)

    def _insert_cloud_association(self, conn, analysis_id: int, prediction: dict, cloud_id: int):
        box_ymin, box_xmin, box_ymax, box_xmax = self._extract_box(prediction)
        insert_assoc = text("""
            INSERT INTO analysis_cloud (analysis_id, cloud_id, confidence, box_ymin, box_xmin, box_ymax, box_xmax)
            VALUES (:analysis_id, :cloud_id, :confidence, :box_ymin, :box_xmin, :box_ymax, :box_xmax)
        """)
        conn.execute(insert_assoc, {
            "analysis_id": analysis_id,
            "cloud_id": cloud_id,
            "confidence": prediction.get("confidence", 0.0),
            "box_ymin": box_ymin,
            "box_xmin": box_xmin,
            "box_ymax": box_ymax,
            "box_xmax": box_xmax
        })

    def _save_cloud_predictions(self, conn, analysis_id: int, predictions: list):
        for prediction in predictions:
            mapped_name = self._mapped_cloud_name(prediction)
            if not mapped_name:
                continue

            cloud_id = self._get_cloud_id(conn, mapped_name)
            if cloud_id:
                self._insert_cloud_association(conn, analysis_id, prediction, cloud_id)

    def save_cloud_analysis(self, analysis_id: int, predictions: list):
        if self.db is not None:
            self._save_cloud_predictions(self.db, analysis_id, predictions)
            return

        with engine.begin() as conn:
            self._save_cloud_predictions(conn, analysis_id, predictions)
