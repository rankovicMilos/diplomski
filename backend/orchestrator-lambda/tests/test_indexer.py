import json

from src.retrieval import indexer


def test_chunks_respect_size_and_overlap():
    text = "\n\n".join(f"Paragraph {i} " + "word " * 80 for i in range(40))

    chunks = indexer.split_into_chunks(text)

    assert len(chunks) > 1
    assert all(len(c) <= indexer.CHUNK_CHARS + indexer.OVERLAP_CHARS + 2 for c in chunks)
    # consecutive chunks share text
    assert chunks[0][-50:] in chunks[1]
    # nothing is lost
    assert "Paragraph 39" in chunks[-1]


def test_headings_start_new_chunks():
    section = "word " * 300
    text = f"# Production\n\n{section}\n\n# Prices\n\n{section}"

    chunks = indexer.split_into_chunks(text)

    assert any(c.startswith("# Prices") for c in chunks)


def test_oversized_paragraph_is_split():
    chunks = indexer.split_into_chunks("x" * (indexer.CHUNK_CHARS * 3))
    assert len(chunks) >= 3


def test_iter_documents_reads_sidecars_and_filters_industry(tmp_path):
    (tmp_path / "raw" / "a").mkdir(parents=True)
    (tmp_path / "_reports").mkdir()
    doc = tmp_path / "raw" / "a" / "report.md"
    doc.write_text("text")
    doc.with_name("report.md.metadata.json").write_text(
        json.dumps({"metadataAttributes": {"industry": "electricity", "sections": ["market_analysis"]}})
    )
    other = tmp_path / "raw" / "a" / "other.md"
    other.write_text("text")
    (tmp_path / "_reports" / "run.json").write_text("{}")

    all_docs = list(indexer.iter_documents(tmp_path, None))
    electricity = list(indexer.iter_documents(tmp_path, "electricity"))

    assert sorted(p.name for p, _ in all_docs) == ["other.md", "report.md"]
    assert [(p.name, m["industry"]) for p, m in electricity] == [("report.md", "electricity")]


def test_extract_text_from_xlsx(tmp_path):
    import openpyxl

    workbook = openpyxl.Workbook()
    workbook.active.append(["Godina", "Proizvodnja"])
    workbook.active.append([2025, 6100])
    path = tmp_path / "bilans.xlsx"
    workbook.save(path)

    text = indexer.extract_text(path)

    assert "| Godina | Proizvodnja |" in text
    assert "| 2025 | 6100 |" in text


def test_unsupported_format(tmp_path):
    path = tmp_path / "slides.pptx"
    path.write_bytes(b"PK")
    assert indexer.extract_text(path) is None
