"""Generic, metadata-driven CRUD + import/export engine.

One engine drives editable grids, bulk CSV/Excel import, export and blank
templates for every ORM model in the toolkit. Modules call:

    from core.crud import editable_grid, import_export_panel

editable_grid(MyModel, scope_project_id=p.id)

The engine introspects the SQLAlchemy model, so new models work with zero
extra code. Type coercion is handled centrally so Dates, Integers, Floats and
Booleans round-trip correctly through Streamlit's data_editor and pandas.
"""
from __future__ import annotations

import datetime as _dt
import io

import pandas as pd
import streamlit as st

from core.database import session_scope, Session
from core import models as m

# Columns the user should never edit directly (managed by the system).
_SYSTEM_COLS = {"id", "created_at"}


# --------------------------------------------------------------------------
# Introspection helpers
# --------------------------------------------------------------------------
def _columns(model):
    """Return list of SQLAlchemy Column objects for a model."""
    return list(model.__table__.columns)


def _editable_columns(model, scope_fk: str | None):
    """User-facing editable columns: skip PK, timestamps and the scope FK."""
    skip = set(_SYSTEM_COLS)
    if scope_fk:
        skip.add(scope_fk)
    return [c for c in _columns(model) if c.name not in skip]


def _py_kind(col):
    """Map a SQLAlchemy column type to a coarse python kind."""
    t = col.type.__class__.__name__
    if t in ("Integer", "BigInteger", "SmallInteger"):
        return "int"
    if t in ("Float", "Numeric"):
        return "float"
    if t == "Boolean":
        return "bool"
    if t == "Date":
        return "date"
    if t == "DateTime":
        return "datetime"
    return "str"


def _coerce(value, kind):
    """Coerce a raw cell value into the python type the column expects."""
    if value is None:
        return None
    # pandas NaN / NaT
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        if kind == "int":
            return int(float(value))
        if kind == "float":
            return float(value)
        if kind == "bool":
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "y", "t")
            return bool(value)
        if kind == "date":
            if isinstance(value, _dt.datetime):
                return value.date()
            if isinstance(value, _dt.date):
                return value
            return pd.to_datetime(value).date()
        if kind == "datetime":
            if isinstance(value, _dt.datetime):
                return value
            return pd.to_datetime(value).to_pydatetime()
        return str(value)
    except (ValueError, TypeError):
        return None


# Sensible dropdown options for known enum-like columns.
_ENUMS = {
    "status": ["Open", "In Progress", "Closed", "On Hold", "Approved", "Rejected",
               "Planned", "Active", "Complete", "Cancelled"],
    "health": ["Green", "Amber", "Red"],
    "severity": ["Low", "Medium", "High", "Critical"],
    "category": ["Risk", "Assumption", "Issue", "Dependency"],
    "influence": ["Low", "Medium", "High"],
    "interest": ["Low", "Medium", "High"],
    "sla_status": ["Met", "At Risk", "Breached"],
}


def _column_config(model, cols):
    """Build a Streamlit column_config for nicer editing widgets."""
    cfg = {}
    for c in cols:
        kind = _py_kind(c)
        label = c.name.replace("_", " ").title()
        if c.name in _ENUMS:
            cfg[c.name] = st.column_config.SelectboxColumn(label, options=_ENUMS[c.name])
        elif kind == "bool":
            cfg[c.name] = st.column_config.CheckboxColumn(label)
        elif kind == "date":
            cfg[c.name] = st.column_config.DateColumn(label, format="YYYY-MM-DD")
        elif kind in ("int", "float"):
            cfg[c.name] = st.column_config.NumberColumn(label)
        else:
            cfg[c.name] = st.column_config.TextColumn(label)
    return cfg


# --------------------------------------------------------------------------
# Data <-> DataFrame
# --------------------------------------------------------------------------
def _rows_to_df(rows, cols):
    data = []
    for r in rows:
        rec = {"id": r.id}
        for c in cols:
            rec[c.name] = getattr(r, c.name, None)
        data.append(rec)
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["id"] + [c.name for c in cols])
    return df


def load_df(model, scope_fk=None, scope_id=None):
    s = Session()
    q = s.query(model)
    if scope_fk and scope_id is not None:
        q = q.filter(getattr(model, scope_fk) == scope_id)
    cols = _editable_columns(model, scope_fk)
    return _rows_to_df(q.all(), cols), cols


# --------------------------------------------------------------------------
# Editable grid (add / edit / delete)
# --------------------------------------------------------------------------
def editable_grid(model, scope_fk: str | None = None, scope_id=None, key: str | None = None):
    """Render an inline editable grid for a model and persist changes on save.

    scope_fk/scope_id restrict rows to one parent (e.g. project_id) and inject
    that value on every new row.
    """
    key = key or f"grid_{model.__name__}_{scope_id}"
    df, cols = load_df(model, scope_fk, scope_id)
    kinds = {c.name: _py_kind(c) for c in cols}

    display = df.drop(columns=["id"]) if "id" in df.columns else df.copy()
    edited = st.data_editor(
        display,
        num_rows="dynamic",
        width='stretch',
        hide_index=True,
        column_config=_column_config(model, cols),
        key=key,
    )

    c1, c2 = st.columns([1, 5])
    if c1.button("💾 Save changes", key=f"{key}_save", type="primary"):
        _persist(model, df, edited, cols, kinds, scope_fk, scope_id)
        st.success("Changes saved.")
        st.rerun()
    c2.caption("Add rows at the bottom · edit any cell · clear a row and save to delete it.")


def _persist(model, original_df, edited_df, cols, kinds, scope_fk, scope_id):
    orig_ids = set(int(i) for i in original_df["id"].tolist()) if not original_df.empty else set()
    col_names = [c.name for c in cols]

    with session_scope() as s:
        # The edited frame has no id column; align by row position for existing
        # rows, treat extra trailing rows as inserts.
        orig_id_list = [int(i) for i in original_df["id"].tolist()] if not original_df.empty else []
        seen_ids = set()

        for pos, (_, row) in enumerate(edited_df.iterrows()):
            values = {name: _coerce(row.get(name), kinds[name]) for name in col_names}
            # Skip completely blank rows.
            if all(v is None for v in values.values()):
                continue
            if pos < len(orig_id_list):
                # update existing
                rid = orig_id_list[pos]
                seen_ids.add(rid)
                obj = s.query(model).get(rid)
                if obj:
                    for name, val in values.items():
                        setattr(obj, name, val)
            else:
                # insert new
                if scope_fk and scope_id is not None:
                    values[scope_fk] = scope_id
                s.add(model(**values))

        # rows removed from the grid -> delete
        for rid in orig_ids - seen_ids:
            obj = s.query(model).get(rid)
            if obj:
                s.delete(obj)


# --------------------------------------------------------------------------
# Import / export
# --------------------------------------------------------------------------
def template_df(model, scope_fk=None):
    cols = _editable_columns(model, scope_fk)
    return pd.DataFrame(columns=[c.name for c in cols])


def to_excel_bytes(df: pd.DataFrame, sheet="data") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        df.to_excel(xl, index=False, sheet_name=sheet)
    return buf.getvalue()


def bulk_import(model, df: pd.DataFrame, scope_fk=None, scope_id=None) -> tuple[int, list[str]]:
    """Insert rows from a DataFrame. Returns (inserted_count, warnings)."""
    cols = _editable_columns(model, scope_fk)
    kinds = {c.name: _py_kind(c) for c in cols}
    valid = {c.name for c in cols}
    warnings = []

    unknown = [c for c in df.columns if c not in valid]
    if unknown:
        warnings.append(f"Ignored unknown columns: {', '.join(unknown)}")

    inserted = 0
    with session_scope() as s:
        for _, row in df.iterrows():
            values = {}
            for name in valid:
                if name in df.columns:
                    values[name] = _coerce(row.get(name), kinds[name])
            if all(v is None for v in values.values()):
                continue
            if scope_fk and scope_id is not None:
                values[scope_fk] = scope_id
            s.add(model(**values))
            inserted += 1
    return inserted, warnings


def import_export_panel(model, scope_fk=None, scope_id=None, key=None):
    """Render download-template / import / export controls for a model."""
    key = key or f"io_{model.__name__}_{scope_id}"
    cols = _editable_columns(model, scope_fk)

    with st.expander("⬆ Import / ⬇ Export"):
        tmpl = template_df(model, scope_fk)
        st.download_button("⬇ Download blank template (CSV)",
                           tmpl.to_csv(index=False).encode(),
                           file_name=f"{model.__tablename__}_template.csv",
                           mime="text/csv", key=f"{key}_tmpl")

        df_now, _ = load_df(model, scope_fk, scope_id)
        export_df = df_now.drop(columns=["id"]) if "id" in df_now.columns else df_now
        cc = st.columns(2)
        cc[0].download_button("⬇ Export current data (CSV)",
                              export_df.to_csv(index=False).encode(),
                              file_name=f"{model.__tablename__}.csv",
                              mime="text/csv", key=f"{key}_csv")
        cc[1].download_button("⬇ Export current data (Excel)",
                              to_excel_bytes(export_df, model.__tablename__),
                              file_name=f"{model.__tablename__}.xlsx",
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              key=f"{key}_xlsx")

        st.divider()
        up = st.file_uploader("Upload CSV or Excel to bulk-add rows",
                              type=["csv", "xlsx"], key=f"{key}_up")
        if up is not None:
            try:
                if up.name.lower().endswith(".csv"):
                    imp = pd.read_csv(up)
                else:
                    imp = pd.read_excel(up)
            except Exception as exc:
                st.error(f"Could not read file: {exc}")
                return
            st.caption(f"Preview ({len(imp)} rows):")
            st.dataframe(imp.head(20), width='stretch', hide_index=True)
            if st.button("✅ Import these rows", key=f"{key}_do", type="primary"):
                n, warns = bulk_import(model, imp, scope_fk, scope_id)
                for w in warns:
                    st.warning(w)
                st.success(f"Imported {n} row(s).")
                st.rerun()
