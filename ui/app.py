import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import (
    and_,
    create_engine,
    func,
    inspect,
    literal,
    or_,
    select,
    text,
    Table,
    MetaData,
)
from sqlalchemy.sql.sqltypes import (
    String,
    Text as SqlText,
    Unicode,
    UnicodeText,
    Date,
    DateTime,
    TIMESTAMP,
    Integer,
    BigInteger,
    SmallInteger,
    Boolean,
    Float,
    Numeric,
    JSON,
    LargeBinary,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Configuration
DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://admin:admin123@localhost:5432/mydb",
)

app = FastAPI(title="PG Explorer", version="0.1.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Templates
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

# Static
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# DB
_engine: Optional[Engine] = None
_metadata = MetaData()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(DEFAULT_DB_URL, pool_pre_ping=True)
    return _engine


def get_inspector():
    return inspect(get_engine())


# Helpers

def get_tables() -> List[str]:
    insp = get_inspector()
    tables = []
    for schema in insp.get_schema_names():
        if schema in ("pg_catalog", "information_schema"):  # skip system
            continue
        for t in insp.get_table_names(schema=schema):
            tables.append(f"{schema}.{t}")
    # If no schemas found (or only public), fall back to public
    if not tables:
        tables = insp.get_table_names(schema="public")
        tables = [f"public.{t}" for t in tables]
    return sorted(tables)


def get_views() -> List[str]:
    with get_engine().connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.views WHERE table_schema = 'public'"))
        return sorted([row[0] for row in res if row[0] is not None])


def get_procedures_with_params() -> Dict[str, List[Dict[str, str]]]:
    procedures = {}
    with get_engine().connect() as conn:
        res = conn.execute(text("SELECT routine_name, specific_name FROM information_schema.routines WHERE routine_type = 'PROCEDURE' AND specific_schema = 'public'"))
        for row in res:
            if row[0] is None:
                continue
            proc_name = row[0]
            specific_name = row[1]
            params_res = conn.execute(text(f"SELECT parameter_name, data_type FROM information_schema.parameters WHERE specific_name = '{specific_name}'"))
            params = []
            for p_row in params_res:
                params.append({"name": p_row[0], "type": p_row[1]})
            procedures[proc_name] = params
    return procedures


def _all_table_name_candidates() -> Dict[str, str]:
    """Map base names (singular/plural variants) -> full table name (schema.table)."""
    out: Dict[str, str] = {}
    for full in get_tables():
        _, name = parse_table(full)
        base = name.lower()
        # add direct name
        out[base] = full
        # singular/plural heuristics
        if base.endswith('ies'):
            out[base[:-3] + 'y'] = full  # companies -> company
        elif base.endswith('s') and not base.endswith('ss'):
            out[base[:-1]] = full  # investors -> investor
        else:
            out[base + 's'] = full  # investor -> investors
            out[base + 'es'] = full # box -> boxes
    return out


def guess_ref_table_for_param(param_name: str) -> Optional[str]:
    if not param_name:
        return None
    name = param_name.lower()
    if name.endswith('_id'):
        base = name[:-3]
        # Strip common directional/context prefixes
        for pref in ('new_', 'old_', 'src_', 'dst_', 'from_', 'to_', 'target_', 'source_', 'current_', 'prev_', 'next_'):
            if base.startswith(pref):
                base = base[len(pref):]
                break
        candidates = _all_table_name_candidates()
        # Try direct
        if base in candidates:
            return candidates[base]
        # Try last token if multi-word (e.g., new_leader -> leader)
        if '_' in base:
            last = base.split('_')[-1]
            if last in candidates:
                return candidates[last]
        # Try by primary key name match: base_id
        def find_by_pk(base_key: str) -> Optional[str]:
            for full in get_tables():
                pk = get_primary_key(full) or []
                if len(pk) == 1 and (pk[0] or '').lower() == f"{base_key}_id":
                    return full
            return None
        match = find_by_pk(base)
        if match:
            return match
        if '_' in base:
            match2 = find_by_pk(base.split('_')[-1])
            if match2:
                return match2
        return candidates.get(base)
    return None


# Explicit overrides for procedure parameter -> referenced table
PROCEDURE_PARAM_TABLE_OVERRIDES: Dict[str, Dict[str, str]] = {
    # procedure_name: { param_name: 'schema.table' }
    "leader_transfer": {
        "new_leader_id": "public.young_people",
        "target_id": "public.projects",
    }
}


def enrich_procedures_with_options(procedures: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Attempt to attach options to params like *_id based on table name guesses."""
    enriched: Dict[str, List[Dict[str, Any]]] = {}
    for proc, params in procedures.items():
        new_params: List[Dict[str, Any]] = []
        for p in params:
            p2 = dict(p)
            # explicit override first
            ref_full = PROCEDURE_PARAM_TABLE_OVERRIDES.get(proc, {}).get(p.get('name'))
            if not ref_full:
                ref_full = guess_ref_table_for_param(p.get('name'))
            if ref_full:
                id_col = get_primary_key(ref_full)
                if id_col and len(id_col) >= 1:
                    id_name = id_col[0]
                    label_col = pick_label_column(ref_full)
                    try:
                        p2['options'] = fetch_fk_options(ref_full, id_name, label_col)
                    except Exception:
                        p2['options'] = []
                    p2['ref_fullname'] = ref_full
                    p2['id_col'] = id_name
                    p2['label_col'] = label_col
            new_params.append(p2)
        enriched[proc] = new_params
    return enriched


def parse_table(fullname: str) -> Tuple[str, str]:
    if "." in fullname:
        schema, name = fullname.split(".", 1)
    else:
        schema, name = "public", fullname
    return schema, name


def reflect_table(fullname: str) -> Table:
    schema, name = parse_table(fullname)
    table = Table(name, _metadata, autoload_with=get_engine(), schema=schema)
    return table


def get_primary_key(fullname: str) -> Optional[List[str]]:
    schema, name = parse_table(fullname)
    return get_inspector().get_pk_constraint(name, schema=schema).get("constrained_columns")


def get_columns(fullname: str) -> List[Dict[str, Any]]:
    """Return column metadata with type info."""
    schema, name = parse_table(fullname)
    insp = get_inspector()
    cols = insp.get_columns(name, schema=schema)
    pks = set(get_primary_key(fullname) or [])
    for c in cols:
        c["is_pk"] = c.get("name") in pks
        # normalize some hints
        c["nullable"] = bool(c.get("nullable", True))
    return cols


def get_foreign_keys(fullname: str) -> Dict[str, Dict[str, Any]]:
    """Return a mapping of local column name -> FK info.
    FK info: { 'ref_schema': str, 'ref_table': str, 'ref_fullname': str, 'ref_column': str }
    """
    schema, name = parse_table(fullname)
    insp = get_inspector()
    fks = insp.get_foreign_keys(name, schema=schema)
    mapping: Dict[str, Dict[str, Any]] = {}
    for fk in fks:
        local_cols = fk.get("constrained_columns") or []
        ref_schema = fk.get("referred_schema") or schema or "public"
        ref_table = fk.get("referred_table")
        ref_cols = fk.get("referred_columns") or []
        if not ref_table or not local_cols or not ref_cols:
            continue
        for i, lcol in enumerate(local_cols):
            rcol = ref_cols[i] if i < len(ref_cols) else ref_cols[0]
            mapping[lcol] = {
                "ref_schema": ref_schema,
                "ref_table": ref_table,
                "ref_fullname": f"{ref_schema}.{ref_table}",
                "ref_column": rcol,
            }
    return mapping


def pick_label_column(fullname: str) -> str:
    """Choose a human-friendly label column for a referenced table.
    Prefers common name-like columns among text types; falls back to PK.
    """
    cols = get_columns(fullname)
    pk_cols = get_primary_key(fullname) or []
    # candidates by name preference
    preferred = [
        "name",
        "full_name",
        "title",
        "label",
        "display_name",
        "username",
        "email",
        "description",
    ]
    text_cols = [c for c in cols if _is_text_type(c.get("type"))]
    # Prefer combined first + last name when present
    names_map = { (c.get("name") or "").lower(): c for c in text_cols }
    if "first_name" in names_map and "last_name" in names_map:
        return "first_name last_name"
    for pname in preferred:
        for c in text_cols:
            if (c.get("name") or "").lower() == pname:
                return c.get("name")
    # first text column
    if text_cols:
        return text_cols[0].get("name")
    # fallback to first PK
    if pk_cols:
        return pk_cols[0]
    # fallback to first column
    return cols[0].get("name") if cols else "id"


def fetch_fk_options(fullname: str, id_col: str, label_col: str, limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch a small list of options for a referenced table: [{id, label}]"""
    table = reflect_table(fullname)
    id_c = table.c.get(id_col)
    # Support composite label like "first_name last_name"
    label_c = None
    if " " in (label_col or ""):
        parts = [p for p in label_col.split(" ") if p]
        if len(parts) == 2 and table.c.get(parts[0]) is not None and table.c.get(parts[1]) is not None:
            label_c = func.concat(table.c.get(parts[0]), literal(" "), table.c.get(parts[1]))
    if label_c is None:
        label_c = table.c.get(label_col)
    if id_c is None or label_c is None:
        return []
    stmt = select(id_c.label("id"), label_c.label("label")).order_by(label_c.asc()).limit(limit)
    options: List[Dict[str, Any]] = []
    with get_engine().connect() as conn:
        for m in conn.execute(stmt).mappings().all():
            options.append({"id": m["id"], "label": m["label"]})
    return options


def build_insert_columns(fullname: str) -> List[Dict[str, Any]]:
    """Prepare visible column metadata for insert form, including FK option lists."""
    table = reflect_table(fullname)
    cols_meta = get_columns(fullname)
    fk_map = get_foreign_keys(fullname)
    visible_cols: List[Dict[str, Any]] = []
    for c in cols_meta:
        name = c.get("name")
        col = table.c.get(name)
        if col is None:
            continue
        if c.get("is_pk") and c.get("autoincrement"):
            continue
        default = c.get("default")
        if default is not None and str(default).lower().startswith("nextval("):
            continue
        try:
            if getattr(col, "identity", None) is not None:
                continue
        except Exception:
            pass
        fk = fk_map.get(name)
        if fk:
            ref_full = fk["ref_fullname"]
            ref_id = fk["ref_column"]
            ref_label = pick_label_column(ref_full)
            try:
                options = fetch_fk_options(ref_full, ref_id, ref_label)
            except Exception:
                options = []
            c = dict(c)
            c["fk"] = {
                "ref_fullname": ref_full,
                "id_col": ref_id,
                "label_col": ref_label,
                "options": options,
            }
        visible_cols.append(c)
    return visible_cols


def _is_text_type(col_type: Any) -> bool:
    return isinstance(col_type, (String, SqlText, Unicode, UnicodeText))


def _is_date_type(col_type: Any) -> bool:
    return isinstance(col_type, (Date, DateTime, TIMESTAMP))


def _is_int_type(t: Any) -> bool:
    return isinstance(t, (Integer, BigInteger, SmallInteger))


def _is_num_type(t: Any) -> bool:
    return isinstance(t, (Float, Numeric))


def _is_bool_type(t: Any) -> bool:
    return isinstance(t, Boolean)


def _is_json_type(t: Any) -> bool:
    return isinstance(t, JSON)


def _is_binary_type(t: Any) -> bool:
    return isinstance(t, LargeBinary)


def build_filters(fullname: str, q: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, date_col: Optional[str] = None):
    table = reflect_table(fullname)
    filters: List[Any] = []
    # Text search across text columns
    if q:
        like = f"%{q}%"
        text_conds: List[Any] = []
        for c in table.columns:
            if _is_text_type(c.type):
                text_conds.append(c.ilike(like))
        if text_conds:
            filters.append(or_(*text_conds))
    # Date range filter using detected/provided date column
    if (date_from or date_to):
        # pick provided date_col or first date column
        dcol = None
        if date_col and date_col in table.c and _is_date_type(table.c[date_col].type):
            dcol = table.c[date_col]
        else:
            for c in table.columns:
                if _is_date_type(c.type):
                    dcol = c
                    break
        if dcol is not None:
            if date_from:
                filters.append(dcol >= text(":date_from"))
            if date_to:
                filters.append(dcol <= text(":date_to"))
    return table, filters


def select_rows(
    fullname: str,
    limit: int = 50,
    offset: int = 0,
    order_by_pk_desc: bool = True,
    q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    date_col: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    table, filters = build_filters(fullname, q=q, date_from=date_from, date_to=date_to, date_col=date_col)
    columns = [c.name for c in table.columns]
    stmt = select(table)
    if filters:
        stmt = stmt.where(and_(*filters))
    # Prefer ordering by PK desc to show latest-looking rows first.
    if order_by_pk_desc:
        pk_cols = [table.c[cname] for cname in (get_primary_key(fullname) or []) if cname in table.c]
        if pk_cols:
            stmt = stmt.order_by(*[c.desc() for c in pk_cols])
    stmt = stmt.limit(limit).offset(offset)
    rows: List[Dict[str, Any]] = []
    bind_params: Dict[str, Any] = {}
    if date_from:
        bind_params["date_from"] = date_from
    if date_to:
        bind_params["date_to"] = date_to
    with get_engine().connect() as conn:
        res = conn.execute(stmt, bind_params)
        for r in res.mappings().all():
            rows.append(dict(r))
    return rows, columns


def select_new_rows_after_pk(fullname: str, last_pk: Any, max_rows: int = 50) -> List[Dict[str, Any]]:
    table = reflect_table(fullname)
    pk_cols = get_primary_key(fullname) or []
    if len(pk_cols) != 1:
        return []
    pk_name = pk_cols[0]
    pk_col = table.c.get(pk_name)
    if pk_col is None:
        return []
    stmt = select(table).where(pk_col > text(":last_pk")).order_by(pk_col.asc()).limit(max_rows)
    rows: List[Dict[str, Any]] = []
    with get_engine().connect() as conn:
        res = conn.execute(stmt, {"last_pk": last_pk})
        for r in res.mappings().all():
            rows.append(dict(r))
    return rows


# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        tables = get_tables()
        template = jinja_env.get_template("index.html")
        return template.render(request=request, tables=tables, db_url=DEFAULT_DB_URL)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/operations", response_class=HTMLResponse)
async def list_operations(request: Request):
    try:
        views = get_views()
        procedures_raw = get_procedures_with_params()
        procedures = enrich_procedures_with_options(procedures_raw)
        template = jinja_env.get_template("operations.html")
        return template.render(request=request, views=views, procedures=procedures, db_url=DEFAULT_DB_URL)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/insert/{table_name}", response_class=HTMLResponse)
async def insert_get(request: Request, table_name: str):
    fullname = table_name if "." in table_name else f"public.{table_name}"
    try:
        visible_cols = build_insert_columns(fullname)
        template = jinja_env.get_template("insert.html")
        return template.render(
            request=request,
            table=fullname,
            cols=visible_cols,
            prev={},
            errors={},
            db_url=DEFAULT_DB_URL,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/insert/{table_name}", response_class=HTMLResponse)
async def insert_post(request: Request, table_name: str):
    import json as pyjson
    fullname = table_name if "." in table_name else f"public.{table_name}"
    try:
        table = reflect_table(fullname)
        form = await request.form()
        values: Dict[str, Any] = {}
        errors: Dict[str, str] = {}
        for col in table.columns:
            name = col.name
            raw = form.get(name)
            # skip identity/serial pk when blank
            if name in (get_primary_key(fullname) or []) and (raw is None or raw == ""):
                continue
            if raw is None or raw == "":
                # handle checkbox false
                if _is_bool_type(col.type):
                    values[name] = False if raw in (None, "") else bool(raw)
                else:
                    values[name] = None
                continue
            try:
                if _is_int_type(col.type):
                    values[name] = int(raw)
                elif _is_num_type(col.type):
                    values[name] = float(raw)
                elif _is_bool_type(col.type):
                    values[name] = raw in ("on", "true", "1", "True")
                elif _is_date_type(col.type):
                    # allow date or datetime-local
                    values[name] = raw  # send as text; PG will cast from ISO string
                elif _is_json_type(col.type):
                    values[name] = pyjson.loads(raw)
                elif _is_binary_type(col.type):
                    values[name] = raw.encode("utf-8")
                else:
                    values[name] = str(raw)
            except Exception as ex:
                errors[name] = f"Invalid value: {ex}"

        if errors:
            cols_meta = build_insert_columns(fullname)
            template = jinja_env.get_template("insert.html")
            return template.render(request=request, table=fullname, cols=cols_meta, errors=errors, prev=dict(form), db_url=DEFAULT_DB_URL)

        try:
            with get_engine().connect() as conn:
                ins = table.insert().values(**values)
                conn.execute(ins)
                conn.commit()
        except SQLAlchemyError as e:
            # Try to extract useful error info from DB constraints
            from sqlalchemy.exc import IntegrityError, DataError
            prev = dict(form)
            err_map: Dict[str, str] = {}
            orig = getattr(e, "orig", None)
            sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
            diag = getattr(orig, "diag", None)
            col = getattr(diag, "column_name", None) if diag else None
            cons = getattr(diag, "constraint_name", None) if diag else None
            primary = getattr(diag, "message_primary", None) if diag else None
            detail = getattr(diag, "message_detail", None) if diag else None
            hint = getattr(diag, "message_hint", None) if diag else None
            # Build a readable message
            msg = primary or str(e)
            if detail:
                msg = f"{msg} — {detail}"
            if hint:
                msg = f"{msg} (hint: {hint})"
            if isinstance(e, IntegrityError) or isinstance(e, DataError) or sqlstate:
                if sqlstate == "23502" and col:  # not_null_violation
                    err_map[col] = "Required (NOT NULL)."
                elif sqlstate == "23505":  # unique_violation
                    err_map["_global"] = f"Unique constraint violated{f' ({cons})' if cons else ''}. {msg}"
                elif sqlstate == "23503":  # foreign_key_violation
                    if col:
                        err_map[col] = "Invalid reference (foreign key)."
                    else:
                        err_map["_global"] = f"Foreign key constraint violated{f' ({cons})' if cons else ''}. {msg}"
                elif sqlstate == "23514":  # check_violation
                    err_map["_global"] = f"Check constraint violated{f' ({cons})' if cons else ''}. {msg}"
                elif sqlstate == "22001":  # string_data_right_truncation
                    if col:
                        err_map[col] = "Value too long for this column."
                    else:
                        err_map["_global"] = msg
                elif sqlstate == "22003":  # numeric_value_out_of_range
                    if col:
                        err_map[col] = "Numeric value out of range."
                    else:
                        err_map["_global"] = msg
                else:
                    if col:
                        err_map[col] = msg
                    else:
                        err_map["_global"] = msg
            else:
                err_map["_global"] = str(e)

            cols_meta = build_insert_columns(fullname)
            template = jinja_env.get_template("insert.html")
            return template.render(request=request, table=fullname, cols=cols_meta, errors=err_map, prev=prev, db_url=DEFAULT_DB_URL)

        # show success page with link back
        template = jinja_env.get_template("insert_success.html")
        return template.render(request=request, table=fullname, values=values, db_url=DEFAULT_DB_URL)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug-operations", response_class=JSONResponse)
async def debug_operations(request: Request):
    try:
        views = get_views()
        procedures = get_procedures_with_params()
        return {"views": views, "procedures": procedures}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/operations/call/{proc_name}", response_class=JSONResponse)
async def call_procedure(request: Request, proc_name: str):
    try:
        form_data = await request.form()
        params = dict(form_data)
        
        # Construct the CALL statement
        param_names = ", ".join([f":{p}" for p in params.keys()])
        stmt = text(f"CALL {proc_name}({param_names})")

        with get_engine().connect() as conn:
            conn.execute(stmt, params)
            conn.commit() # Procedures might have side effects that need to be committed

        return {"status": "success", "message": f"Procedure '{proc_name}' executed successfully."}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/table/{table_name}", response_class=HTMLResponse)
async def view_table(
    request: Request,
    table_name: str,
    limit: int = Query(50, ge=1, le=500),
    page: int = Query(1, ge=1),
    q: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_col: Optional[str] = Query(None),
):
    fullname = table_name if "." in table_name else f"public.{table_name}"
    offset = (page - 1) * limit
    try:
        rows, columns = select_rows(fullname, limit=limit, offset=offset, q=q, date_from=date_from, date_to=date_to, date_col=date_col)
        pk_cols = get_primary_key(fullname) or []
        cols_meta = get_columns(fullname)
        template = jinja_env.get_template("table.html")
        return template.render(
            request=request,
            table=fullname,
            columns=columns,
            rows=rows,
            limit=limit,
            page=page,
            pk_cols=pk_cols,
            q=q,
            date_from=date_from,
            date_to=date_to,
            date_col=date_col,
            cols_meta=cols_meta,
            db_url=DEFAULT_DB_URL,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/{table_name}", response_class=HTMLResponse)
async def view_cards(
    request: Request,
    table_name: str,
    limit: int = Query(24, ge=1, le=200),
):
    fullname = table_name if "." in table_name else f"public.{table_name}"
    try:
        rows, columns = select_rows(fullname, limit=limit, offset=0, order_by_pk_desc=True)
        pk_cols = get_primary_key(fullname) or []
        # Prefer custom template per table when available
        custom_template_name = f"cards_{table_name.split('.')[-1]}.html"
        template_name = custom_template_name if os.path.exists(os.path.join(TEMPLATES_DIR, custom_template_name)) else "cards.html"
        template = jinja_env.get_template(template_name)
        return template.render(
            request=request,
            table=fullname,
            columns=columns,
            rows=rows,
            pk_cols=pk_cols,
            db_url=DEFAULT_DB_URL,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tables", response_class=JSONResponse)
async def api_tables():
    try:
        return {"tables": get_tables()}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/columns/{table_name}", response_class=JSONResponse)
async def api_columns(table_name: str):
    fullname = table_name if "." in table_name else f"public.{table_name}"
    try:
        # Return a JSON-serializable projection of column metadata
        safe_cols: List[Dict[str, Any]] = []
        for c in get_columns(fullname):
            safe_cols.append({
                "name": c.get("name"),
                "nullable": bool(c.get("nullable", True)),
                "is_pk": bool(c.get("is_pk", False)),
                "autoincrement": bool(c.get("autoincrement") in (True, "auto")),
                "default": (str(c.get("default")) if c.get("default") is not None else None),
                "type": str(c.get("type")),
                "comment": c.get("comment"),
            })
        return {"columns": safe_cols}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/{table_name}/new", response_class=JSONResponse)
async def api_new_rows(table_name: str, after_pk: Optional[int] = None, max_rows: int = 50):
    fullname = table_name if "." in table_name else f"public.{table_name}"
    pk_cols = get_primary_key(fullname) or []
    if len(pk_cols) != 1:
        return JSONResponse({"rows": [], "message": "Watching requires a single-column primary key."})
    if after_pk is None:
        return JSONResponse({"rows": [], "message": "Provide after_pk to watch for new rows."})
    try:
        rows = select_new_rows_after_pk(fullname, last_pk=after_pk, max_rows=max_rows)
        return {"rows": rows, "pk": pk_cols[0]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/{table_name}")
async def export_csv(
    table_name: str,
    q: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    date_col: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=200000),
):
    import csv
    import io

    fullname = table_name if "." in table_name else f"public.{table_name}"
    try:
        table, filters = build_filters(fullname, q=q, date_from=date_from, date_to=date_to, date_col=date_col)
        stmt = select(table)
        if filters:
            stmt = stmt.where(and_(*filters))
        if limit:
            stmt = stmt.limit(limit)
        bind_params: Dict[str, Any] = {}
        if date_from:
            bind_params["date_from"] = date_from
        if date_to:
            bind_params["date_to"] = date_to

        def row_iter() -> Iterable[bytes]:
            output = io.StringIO()
            writer = None
            with get_engine().connect() as conn:
                res = conn.execute(stmt, bind_params)
                for m in res.mappings():
                    row = dict(m)
                    if writer is None:
                        writer = csv.DictWriter(output, fieldnames=list(row.keys()))
                        writer.writeheader()
                        data = output.getvalue()
                        output.seek(0)
                        output.truncate(0)
                        yield data.encode("utf-8")
                    writer.writerow(row)
                    data = output.getvalue()
                    output.seek(0)
                    output.truncate(0)
                    yield data.encode("utf-8")

        filename = table_name.replace(".", "_") + ".csv"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(row_iter(), media_type="text/csv", headers=headers)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/timeline/{table_name}", response_class=HTMLResponse)
async def timeline(
    request: Request,
    table_name: str,
    date_col: Optional[str] = Query(None),
    day: Optional[str] = Query(None, description="YYYY-MM-DD"),
    q: Optional[str] = Query(None),
):
    fullname = table_name if "." in table_name else f"public.{table_name}"
    try:
        table = reflect_table(fullname)
        # choose date column
        dcol = None
        if date_col and date_col in table.c and _is_date_type(table.c[date_col].type):
            dcol = table.c[date_col]
        else:
            for c in table.columns:
                if _is_date_type(c.type):
                    dcol = c
                    date_col = c.name
                    break
        if dcol is None:
            raise HTTPException(status_code=400, detail="No date/datetime column found. Provide ?date_col=")

        # buckets: latest 60 days with counts
        day_expr = func.date_trunc("day", dcol).cast(Date)
        buckets_stmt = select(
            day_expr.label("day"),
            func.count().label("n"),
        ).group_by(day_expr).order_by(day_expr.desc()).limit(60)

        # apply q across text cols
        if q:
            like = f"%{q}%"
            text_conds = [c.ilike(like) for c in table.columns if _is_text_type(c.type)]
            if text_conds:
                buckets_stmt = buckets_stmt.where(or_(*text_conds))

        buckets: List[Dict[str, Any]] = []
        with get_engine().connect() as conn:
            for r in conn.execute(buckets_stmt).mappings().all():
                buckets.append(dict(r))

        # choose day to show rows
        selected_day = day or (buckets[0]["day"].isoformat() if buckets else None)
        rows: List[Dict[str, Any]] = []
        columns = [c.name for c in table.columns]
        if selected_day:
            stmt = select(table).where(func.date(dcol) == text(":sel_day")).order_by(dcol.desc()).limit(200)
            bind = {"sel_day": selected_day}
            if q:
                like = f"%{q}%"
                text_conds = [c.ilike(like) for c in table.columns if _is_text_type(c.type)]
                if text_conds:
                    stmt = stmt.where(or_(*text_conds))
            with get_engine().connect() as conn:
                res = conn.execute(stmt, bind)
                for m in res.mappings().all():
                    rows.append(dict(m))

        template = jinja_env.get_template("timeline.html")
        return template.render(
            request=request,
            table=fullname,
            date_col=date_col,
            buckets=buckets,
            selected_day=selected_day,
            rows=rows,
            columns=columns,
            q=q,
            pk_cols=get_primary_key(fullname) or [],
            db_url=DEFAULT_DB_URL,
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple health
@app.get("/healthz")
async def healthz():
    try:
        # quick probe
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
