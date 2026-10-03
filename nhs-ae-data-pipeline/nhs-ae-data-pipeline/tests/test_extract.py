import pandas as pd, pytest
from pipeline.extract import read_source, file_hash, RAW_COLUMNS

def make_csv(tmp_path, extra_cols=False, drop=None):
    row = {c: "1" for c in RAW_COLUMNS}; row["Period"] = "MSitAE-APRIL-2025"
    df = pd.DataFrame([row])
    if extra_cols: df["Unnamed: 22"] = None
    if drop: df = df.drop(columns=[drop])
    p = tmp_path / "file.csv"; df.to_csv(p, index=False); return p

def test_unexpected_columns_are_dropped(tmp_path):
    df = read_source(make_csv(tmp_path, extra_cols=True))
    assert "Unnamed: 22" not in df.columns and "source_file" in df.columns
    assert len(df.columns) == len(RAW_COLUMNS) + 1

def test_missing_column_fails_loudly(tmp_path):
    with pytest.raises(ValueError):
        read_source(make_csv(tmp_path, drop="Attendances over 4hrs Type 1"))

def test_file_hash_is_stable(tmp_path):
    p = make_csv(tmp_path)
    assert file_hash(p) == file_hash(p)
