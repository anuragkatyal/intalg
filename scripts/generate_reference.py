from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import quote


SCRIPT_PATH = Path(__file__).resolve()
INTALG_ROOT = SCRIPT_PATH.parent.parent
WORKSPACE_ROOT = INTALG_ROOT.parent
DOENET_ROOT = WORKSPACE_ROOT / "DoenetML"
OUTPUT_PATH = INTALG_ROOT / "DOENETML_INTALG_REFERENCE.md"

IGNORE_DIR_NAMES = {
    ".git",
    ".next",
    ".turbo",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "dist-ssr",
    "node_modules",
    "pkg",
    "runner-results",
    "target",
}

IGNORE_FILE_NAMES = {
    ".DS_Store",
    "Cargo.lock",
    "package-lock.json",
    OUTPUT_PATH.name,
}

IGNORE_PATH_FRAGMENTS = {
    "cypress/screenshots/",
    "cypress/videos/",
    "packages/doenetml-worker-rust/lib-js-wasm-binding/pkg/",
    "packages/parser/src/generated-assets/",
    "packages/static-assets/src/generated/",
}

TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mdx",
    ".mjs",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".doenet",
    "",
}

DOC_SKIP_LINE_PREFIXES = (
    "import ",
    "export ",
)


@dataclass(frozen=True)
class ScannedFile:
    repo: str
    relative_path: str
    absolute_path: Path
    bucket: str
    size_bytes: int
    extension: str


def main() -> None:
    doenet_scan = scan_repo(DOENET_ROOT, "DoenetML")
    intalg_scan = scan_repo(INTALG_ROOT, "intalg")

    root_package = json.loads((DOENET_ROOT / "package.json").read_text(encoding="utf-8"))
    schema_path = DOENET_ROOT / "packages/static-assets/src/generated/doenet-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    docs_pages = parse_docs_pages(doenet_scan["files"])
    component_descriptions = parse_component_index(
        DOENET_ROOT / "packages/docs-nextra/pages/reference/componentIndex.mdx"
    )
    component_sources = parse_component_sources(doenet_scan["files"])
    package_readmes = parse_readmes(
        [
            scanned_file
            for scanned_file in doenet_scan["files"]
            if scanned_file.relative_path == "README.md"
            or scanned_file.relative_path == "AGENTS.md"
            or scanned_file.relative_path == "TEST_RUN_INSTRUCTIONS_FOR_AGENTS.md"
            or re.fullmatch(r"packages/[^/]+/README\.md", scanned_file.relative_path)
        ]
    )

    component_catalog = build_component_catalog(
        schema=schema,
        component_sources=component_sources,
        docs_pages=docs_pages,
        component_descriptions=component_descriptions,
    )
    intalg_index = parse_intalg_files(intalg_scan["files"])

    markdown = render_markdown(
        root_package=root_package,
        schema_path=schema_path,
        doenet_scan=doenet_scan,
        intalg_scan=intalg_scan,
        package_readmes=package_readmes,
        docs_pages=docs_pages,
        component_catalog=component_catalog,
        component_sources=component_sources,
        intalg_index=intalg_index,
    )
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")

    summary = {
        "output": str(OUTPUT_PATH),
        "doenet_files": len(doenet_scan["files"]),
        "intalg_files": len(intalg_scan["files"]),
        "docs_pages": len(docs_pages),
        "schema_components": len(component_catalog["schema_components"]),
        "source_component_types": len(component_sources["by_component"]),
        "intalg_activities": len(intalg_index["activities"]),
    }
    print(json.dumps(summary, indent=2))


def scan_repo(root: Path, repo_name: str) -> dict:
    included: list[ScannedFile] = []
    excluded_counts: Counter[str] = Counter()

    def visit(current_dir: Path) -> None:
        for child in sorted(current_dir.iterdir(), key=lambda path: path.name.lower()):
            relative_path = child.relative_to(root).as_posix()
            reason = get_exclusion_reason(relative_path, child)
            if reason:
                excluded_counts[reason] += 1
                continue
            if child.is_dir():
                visit(child)
                continue
            stat = child.stat()
            included.append(
                ScannedFile(
                    repo=repo_name,
                    relative_path=relative_path,
                    absolute_path=child,
                    bucket=classify_file(repo_name, relative_path),
                    size_bytes=stat.st_size,
                    extension=child.suffix.lower(),
                )
            )

    visit(root)
    return {
        "root": root,
        "files": included,
        "excluded_counts": excluded_counts,
    }


def get_exclusion_reason(relative_path: str, path_obj: Path) -> str | None:
    if path_obj.name in IGNORE_FILE_NAMES:
        return f"ignored-file:{path_obj.name}"
    if path_obj.is_dir() and path_obj.name in IGNORE_DIR_NAMES:
        return f"ignored-dir:{path_obj.name}"
    for fragment in IGNORE_PATH_FRAGMENTS:
        if fragment in f"{relative_path}/" or relative_path.startswith(fragment):
            return f"ignored-path:{fragment.rstrip('/')}"
    return None


def classify_file(repo_name: str, relative_path: str) -> str:
    if repo_name == "DoenetML":
        if relative_path in {"README.md", "AGENTS.md", "TEST_RUN_INSTRUCTIONS_FOR_AGENTS.md"}:
            return "root-doc"
        if re.fullmatch(r"packages/[^/]+/README\.md", relative_path):
            return "package-readme"
        if relative_path.startswith("packages/docs-nextra/pages/reference/"):
            return "docs-reference"
        if relative_path.startswith("packages/docs-nextra/pages/tutorials/"):
            return "docs-tutorial"
        if relative_path.startswith("packages/docs-nextra/pages/document_structure/"):
            return "docs-structure"
        if relative_path.startswith("packages/docs-nextra/pages/sandbox/"):
            return "docs-sandbox"
        if relative_path.startswith("packages/docs-nextra/pages/"):
            return "docs-page-other"
        if relative_path.startswith("packages/docs-nextra/components/"):
            return "docs-component"
        if relative_path.startswith("packages/docs-nextra/scripts/"):
            return "docs-script"
        if relative_path.startswith("packages/doenetml-worker-javascript/src/components/abstract/"):
            return "worker-abstract-component-source"
        if relative_path.startswith("packages/doenetml-worker-javascript/src/components/"):
            return "worker-component-source"
        if relative_path.startswith("packages/doenetml-worker-javascript/src/utils/"):
            return "worker-utils"
        if relative_path.startswith("packages/static-assets/scripts/"):
            return "schema-script"
        if relative_path.startswith("packages/static-assets/src/"):
            return "schema-source"
        if relative_path.startswith("packages/parser/src/"):
            return "parser-source"
        if relative_path.startswith("packages/lsp-tools/src/") or relative_path.startswith("packages/lsp/src/"):
            return "lsp-source"
        if "/test/" in relative_path or relative_path.startswith("packages/test-"):
            return "test-source"
        if "/src/" in relative_path:
            return "package-source"
        return "other"

    if relative_path.endswith(".doenet"):
        return "activity"
    if relative_path == "book.html":
        return "book"
    if relative_path == "LICENSE":
        return "repo-meta"
    return "other"


def parse_readmes(files: Iterable[ScannedFile]) -> list[dict]:
    parsed = []
    for scanned_file in sorted(files, key=lambda item: item.relative_path.lower()):
        text = scanned_file.absolute_path.read_text(encoding="utf-8", errors="replace")
        parsed.append(
            {
                "path": scanned_file.absolute_path,
                "relative_path": scanned_file.relative_path,
                "title": extract_markdown_title(text, scanned_file.absolute_path.stem),
                "excerpt": extract_first_paragraph(text),
            }
        )
    return parsed


def parse_docs_pages(files: Iterable[ScannedFile]) -> list[dict]:
    parsed = []
    for scanned_file in sorted(files, key=lambda item: item.relative_path.lower()):
        if not scanned_file.relative_path.startswith("packages/docs-nextra/pages/"):
            continue
        if scanned_file.absolute_path.suffix.lower() != ".mdx":
            continue
        text = scanned_file.absolute_path.read_text(encoding="utf-8", errors="replace")
        title = extract_markdown_title(text, scanned_file.absolute_path.stem)
        parsed.append(
            {
                "path": scanned_file.absolute_path,
                "relative_path": scanned_file.relative_path,
                "title": title,
                "section": docs_section(scanned_file.relative_path),
                "component_name": derive_component_name(
                    slug=scanned_file.absolute_path.stem,
                    title=title,
                    section=docs_section(scanned_file.relative_path),
                ),
                "excerpt": extract_first_paragraph(text),
                "example_count": count_examples(text),
                "has_attr_display": "<AttrDisplay" in text,
                "has_prop_display": "<PropDisplay" in text,
            }
        )
    return parsed


def parse_component_index(path: Path) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.startswith("|"):
            continue
        columns = [column.strip() for column in raw_line.split("|")[1:-1]]
        if len(columns) < 2:
            continue
        component_cell = columns[0]
        description_cell = columns[1]
        name_match = re.search(r"<\s*([A-Za-z][A-Za-z0-9_]*)", component_cell)
        if not name_match:
            continue
        component_name = name_match.group(1)
        description = clean_inline_text(description_cell)
        if description and description != "Description":
            descriptions[component_name] = description
    return descriptions


def parse_component_sources(files: Iterable[ScannedFile]) -> dict:
    by_component: dict[str, list[dict]] = defaultdict(list)
    all_entries: list[dict] = []
    for scanned_file in sorted(files, key=lambda item: item.relative_path.lower()):
        if not scanned_file.relative_path.startswith(
            "packages/doenetml-worker-javascript/src/components/"
        ):
            continue
        if scanned_file.absolute_path.suffix.lower() != ".js":
            continue
        text = scanned_file.absolute_path.read_text(encoding="utf-8", errors="replace")
        for entry in parse_component_source_file(text):
            full_entry = {
                "component_type": entry["component_type"],
                "class_name": entry["class_name"],
                "extends": entry["extends"],
                "renderer_type": entry["renderer_type"],
                "can_be_in_list": entry["can_be_in_list"],
                "creates_variants": entry["creates_variants"],
                "render_children": entry["render_children"],
                "include_blank_string_children": entry[
                    "include_blank_string_children"
                ],
                "additional_schema_children": entry["additional_schema_children"],
                "path": scanned_file.absolute_path,
                "relative_path": scanned_file.relative_path,
                "internal": entry["component_type"].startswith("_"),
            }
            by_component[entry["component_type"]].append(full_entry)
            all_entries.append(full_entry)
    return {
        "by_component": by_component,
        "all_entries": all_entries,
    }


def parse_component_source_file(text: str) -> list[dict]:
    lines = text.splitlines()
    class_blocks: list[dict] = []
    current_block: dict | None = None

    for line in lines:
        class_match = re.search(
            r"(?:export\s+default\s+)?class\s+([A-Za-z0-9_]+)\s+extends\s+([A-Za-z0-9_]+)",
            line,
        )
        if class_match:
            if current_block:
                class_blocks.append(current_block)
            current_block = {
                "class_name": class_match.group(1),
                "extends": class_match.group(2),
                "lines": [line],
            }
            continue
        if current_block is not None:
            current_block["lines"].append(line)

    if current_block:
        class_blocks.append(current_block)

    entries = []
    for block in class_blocks:
        block_text = "\n".join(block["lines"])
        component_types = re.findall(
            r"static\s+componentType\s*=\s*[\"']([^\"']+)[\"']",
            block_text,
        )
        if not component_types:
            continue
        metadata = {
            "renderer_type": extract_single_quoted_value(
                block_text, r"static\s+rendererType\s*=\s*[\"']([^\"']+)[\"']"
            ),
            "can_be_in_list": bool(
                re.search(r"static\s+canBeInList\s*=\s*true", block_text)
            ),
            "creates_variants": bool(
                re.search(r"static\s+createsVariants\s*=\s*true", block_text)
            ),
            "render_children": bool(
                re.search(r"static\s+renderChildren\s*=\s*true", block_text)
            ),
            "include_blank_string_children": bool(
                re.search(
                    r"static\s+includeBlankStringChildren\s*=\s*true", block_text
                )
            ),
            "additional_schema_children": extract_string_array(
                block_text,
                r"static\s+additionalSchemaChildren\s*=\s*\[(.*?)\]",
            ),
        }
        for component_type in component_types:
            entries.append(
                {
                    "component_type": component_type,
                    "class_name": block["class_name"],
                    "extends": block["extends"],
                    **metadata,
                }
            )
    return entries


def build_component_catalog(
    *,
    schema: dict,
    component_sources: dict,
    docs_pages: list[dict],
    component_descriptions: dict[str, str],
) -> dict:
    docs_by_component: dict[str, list[dict]] = defaultdict(list)
    for docs_page in docs_pages:
        if docs_page["component_name"]:
            docs_by_component[docs_page["component_name"]].append(docs_page)

    schema_components = []
    schema_names = set()
    for element in sorted(schema["elements"], key=lambda item: item["name"].lower()):
        name = element["name"]
        schema_names.add(name)
        schema_components.append(
            {
                "name": name,
                "description": component_descriptions.get(name),
                "docs_pages": sorted(
                    docs_by_component.get(name, []),
                    key=lambda item: item["relative_path"].lower(),
                ),
                "source_entries": sorted(
                    component_sources["by_component"].get(name, []),
                    key=lambda item: item["relative_path"].lower(),
                ),
                "children": element.get("children", []),
                "attributes": element.get("attributes", []),
                "properties": element.get("properties", []),
                "accepts_string_children": bool(element.get("acceptsStringChildren")),
                "top_level": bool(element.get("top")),
            }
        )

    source_only = []
    for name, entries in sorted(
        component_sources["by_component"].items(), key=lambda item: item[0].lower()
    ):
        if name in schema_names:
            continue
        source_only.append(
            {
                "name": name,
                "internal": all(entry["internal"] for entry in entries),
                "entries": sorted(entries, key=lambda item: item["relative_path"].lower()),
                "docs_pages": sorted(
                    docs_by_component.get(name, []),
                    key=lambda item: item["relative_path"].lower(),
                ),
                "description": component_descriptions.get(name),
            }
        )

    docs_only_topics = []
    for docs_page in sorted(docs_pages, key=lambda item: item["relative_path"].lower()):
        component_name = docs_page["component_name"]
        if component_name and component_name in schema_names:
            continue
        if component_name and component_name in component_sources["by_component"]:
            continue
        docs_only_topics.append(docs_page)

    return {
        "schema_components": schema_components,
        "source_only": source_only,
        "docs_only_topics": docs_only_topics,
    }


def parse_intalg_files(files: Iterable[ScannedFile]) -> dict:
    activities = []
    component_usage: Counter[str] = Counter()
    for scanned_file in sorted(files, key=lambda item: item.relative_path.lower()):
        if scanned_file.bucket != "activity":
            continue
        text = scanned_file.absolute_path.read_text(encoding="utf-8", errors="replace")
        title = extract_tag_content(text, "title") or scanned_file.absolute_path.stem
        comment_metadata = extract_leading_comment_metadata(text)
        tags = re.findall(r"<([A-Za-z][A-Za-z0-9]*)\b", text)
        usage_counts = Counter(tags)
        component_usage.update(tags)
        activities.append(
            {
                "path": scanned_file.absolute_path,
                "relative_path": scanned_file.relative_path,
                "title": clean_inline_text(title),
                "folder": scanned_file.absolute_path.parent.name,
                "course": comment_metadata.get("Course"),
                "chapter": comment_metadata.get("Chapter"),
                "section": comment_metadata.get("Section"),
                "author": comment_metadata.get("Author"),
                "contact": comment_metadata.get("Contact"),
                "about": comment_metadata.get("About the activity"),
                "section_count": count_tag(text, "section"),
                "answer_count": count_tag(text, "answer"),
                "graph_count": count_tag(text, "graph"),
                "setup_count": count_tag(text, "setup"),
                "image_count": count_tag(text, "image"),
                "external_urls": sorted(set(extract_external_urls(text))),
                "top_components": usage_counts.most_common(15),
            }
        )
    book_info = None
    book_path = INTALG_ROOT / "book.html"
    if book_path.exists():
        text = book_path.read_text(encoding="utf-8", errors="replace")
        book_info = {
            "path": book_path,
            "title": extract_html_title(text) or "book.html",
            "activity_link_count": len(re.findall(r"\.doenet", text, flags=re.IGNORECASE)),
        }
    return {
        "activities": activities,
        "component_usage": component_usage,
        "book_info": book_info,
    }


def render_markdown(
    *,
    root_package: dict,
    schema_path: Path,
    doenet_scan: dict,
    intalg_scan: dict,
    package_readmes: list[dict],
    docs_pages: list[dict],
    component_catalog: dict,
    component_sources: dict,
    intalg_index: dict,
) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines: list[str] = []

    lines.append("# DoenetML and intalg Ingestion Reference")
    lines.append("")
    lines.append(
        "This file is generated from an exhaustive scan of the non-generated files in the sibling DoenetML and intalg repositories."
    )
    lines.append("")
    lines.append(f"- Generated at: {generated_at}")
    lines.append(f"- Generator: {markdown_link(SCRIPT_PATH)}")
    lines.append(f"- Output path: {OUTPUT_PATH.name}")
    lines.append(
        f"- Authoritative component and schema extraction logic: {markdown_link(DOENET_ROOT / 'packages/static-assets/scripts/get-schema.ts')}"
    )
    lines.append(
        f"- Machine-readable schema projection used for catalog formatting: {markdown_link(schema_path)}"
    )
    lines.append(
        f"- Registry anchor: {markdown_link(DOENET_ROOT / 'packages/doenetml-worker-javascript/src/ComponentTypes.js')}"
    )
    lines.append("")

    lines.extend(render_scope_section(doenet_scan, intalg_scan, root_package))
    lines.extend(render_readme_section(package_readmes))
    lines.extend(render_docs_section(docs_pages))
    lines.extend(render_component_catalog_section(component_catalog))
    lines.extend(render_intalg_section(intalg_index))
    lines.extend(render_manifest_section(doenet_scan, intalg_scan))
    lines.extend(render_exclusion_section(doenet_scan, intalg_scan))
    lines.extend(render_source_only_section(component_catalog, component_sources))

    return "\n".join(lines).rstrip() + "\n"


def render_scope_section(doenet_scan: dict, intalg_scan: dict, root_package: dict) -> list[str]:
    lines = ["## Scope and Provenance", ""]
    lines.append(
        "This reference uses DoenetML documentation files for documented wording and examples, and DoenetML implementation and schema-generation files for component, attribute, property, and child-relationship truth."
    )
    lines.append("")
    lines.append(f"- DoenetML included files: {len(doenet_scan['files'])}")
    lines.append(f"- intalg included files: {len(intalg_scan['files'])}")
    lines.append(
        f"- DoenetML workspaces declared in package.json: {len(root_package.get('workspaces', []))}"
    )
    lines.append("")
    lines.append("### Workspace Inventory")
    lines.append("")
    for workspace in root_package.get("workspaces", []):
        lines.append(f"- {workspace}")
    lines.append("")
    return lines


def render_readme_section(package_readmes: list[dict]) -> list[str]:
    lines = ["## Root and Package Documentation", ""]
    for item in package_readmes:
        lines.append(f"### {item['title']}")
        lines.append("")
        lines.append(f"- Source: {markdown_link(item['path'])}")
        if item["excerpt"]:
            lines.append(f"- Summary: {item['excerpt']}")
        lines.append("")
    return lines


def render_docs_section(docs_pages: list[dict]) -> list[str]:
    lines = ["## DoenetML Documentation Corpus", ""]
    section_counts = Counter(page["section"] for page in docs_pages)
    lines.append("### Documentation Page Counts")
    lines.append("")
    for section_name, count in sorted(section_counts.items()):
        lines.append(f"- {section_name}: {count}")
    lines.append("")
    lines.append("### Page Index")
    lines.append("")
    lines.append(
        "| Title | Section | Component Focus | Examples | Attr Table | Prop Table | Source | Summary |"
    )
    lines.append("| --- | --- | --- | ---: | --- | --- | --- | --- |")
    for page in sorted(docs_pages, key=lambda item: item["relative_path"].lower()):
        component_focus = page["component_name"] or "-"
        summary = truncate(page["excerpt"], 180) or "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_table_text(page["title"]),
                    escape_table_text(page["section"]),
                    escape_table_text(component_focus),
                    str(page["example_count"]),
                    yes_no(page["has_attr_display"]),
                    yes_no(page["has_prop_display"]),
                    markdown_link(page["path"], label=page["relative_path"]),
                    escape_table_text(summary),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def render_component_catalog_section(component_catalog: dict) -> list[str]:
    lines = ["## DoenetML Component Catalog", ""]
    lines.append(
        "Each schema component below lists its documentation pages, source definitions, allowed children, attributes, and public properties."
    )
    lines.append("")
    for component in component_catalog["schema_components"]:
        lines.append(f"### <{component['name']}>")
        lines.append("")
        if component["description"]:
            lines.append(f"- Description: {component['description']}")
        lines.append(f"- Accepts string children: {yes_no(component['accepts_string_children'])}")
        lines.append(f"- Top-level component: {yes_no(component['top_level'])}")
        if component["docs_pages"]:
            lines.append(
                "- Documentation pages: "
                + "; ".join(markdown_link(page["path"], label=page["relative_path"]) for page in component["docs_pages"])
            )
        if component["source_entries"]:
            source_chunks = []
            for entry in component["source_entries"]:
                note_bits = [entry["class_name"], f"extends {entry['extends']}"]
                if entry["renderer_type"]:
                    note_bits.append(f"rendererType={entry['renderer_type']}")
                if entry["can_be_in_list"]:
                    note_bits.append("canBeInList")
                if entry["creates_variants"]:
                    note_bits.append("createsVariants")
                if entry["render_children"]:
                    note_bits.append("renderChildren")
                if entry["include_blank_string_children"]:
                    note_bits.append("includeBlankStringChildren")
                if entry["additional_schema_children"]:
                    note_bits.append(
                        "additionalSchemaChildren="
                        + ", ".join(entry["additional_schema_children"])
                    )
                source_chunks.append(
                    f"{markdown_link(entry['path'], label=entry['relative_path'])} ({'; '.join(note_bits)})"
                )
            lines.append("- Source definitions: " + "; ".join(source_chunks))
        if component["children"]:
            lines.append("- Allowed children: " + ", ".join(component["children"]))
        lines.append("- Attributes:")
        if component["attributes"]:
            for attribute in component["attributes"]:
                lines.append("  - " + format_attribute(attribute))
        else:
            lines.append("  - None listed in schema")
        lines.append("- Properties:")
        if component["properties"]:
            for prop in component["properties"]:
                lines.append("  - " + format_property(prop))
        else:
            lines.append("  - None listed in schema")
        lines.append("")
    return lines


def render_intalg_section(intalg_index: dict) -> list[str]:
    lines = ["## intalg Corpus", ""]
    if intalg_index["book_info"]:
        lines.append("### book.html")
        lines.append("")
        lines.append(f"- Source: {markdown_link(intalg_index['book_info']['path'])}")
        lines.append(f"- Title: {intalg_index['book_info']['title']}")
        lines.append(
            f"- .doenet link count in book.html: {intalg_index['book_info']['activity_link_count']}"
        )
        lines.append("")
    lines.append("### Activity Index")
    lines.append("")
    for activity in intalg_index["activities"]:
        lines.append(f"#### {activity['title']}")
        lines.append("")
        lines.append(f"- Source: {markdown_link(activity['path'])}")
        lines.append(f"- Folder: {activity['folder']}")
        if activity["course"]:
            lines.append(f"- Course: {activity['course']}")
        if activity["chapter"]:
            lines.append(f"- Chapter: {activity['chapter']}")
        if activity["section"]:
            lines.append(f"- Section: {activity['section']}")
        if activity["author"]:
            lines.append(f"- Author: {activity['author']}")
        if activity["contact"]:
            lines.append(f"- Contact: {activity['contact']}")
        if activity["about"]:
            lines.append(f"- About: {activity['about']}")
        lines.append(
            "- Structural counts: "
            f"sections={activity['section_count']}, answers={activity['answer_count']}, "
            f"graphs={activity['graph_count']}, setups={activity['setup_count']}, images={activity['image_count']}"
        )
        if activity["external_urls"]:
            lines.append("- External URLs: " + "; ".join(activity["external_urls"]))
        if activity["top_components"]:
            lines.append(
                "- Top components: "
                + ", ".join(
                    f"{name} ({count})" for name, count in activity["top_components"]
                )
            )
        lines.append("")

    lines.append("### Aggregate Component Usage")
    lines.append("")
    for name, count in intalg_index["component_usage"].most_common(50):
        lines.append(f"- {name}: {count}")
    lines.append("")
    return lines


def render_manifest_section(doenet_scan: dict, intalg_scan: dict) -> list[str]:
    lines = ["## Exhaustive Included File Manifest", ""]
    for scan in (doenet_scan, intalg_scan):
        repo_name = scan["root"].name
        lines.append(f"### {repo_name} Bucket Counts")
        lines.append("")
        bucket_counts = Counter(item.bucket for item in scan["files"])
        for bucket_name, count in sorted(bucket_counts.items()):
            lines.append(f"- {bucket_name}: {count}")
        lines.append("")
        grouped: dict[str, list[ScannedFile]] = defaultdict(list)
        for scanned_file in scan["files"]:
            grouped[scanned_file.bucket].append(scanned_file)
        for bucket_name in sorted(grouped):
            lines.append("<details>")
            lines.append(
                f"<summary>{repo_name} :: {bucket_name} ({len(grouped[bucket_name])} files)</summary>"
            )
            lines.append("")
            for scanned_file in grouped[bucket_name]:
                lines.append(
                    f"- {markdown_link(scanned_file.absolute_path, label=repo_name + '/' + scanned_file.relative_path)}"
                )
            lines.append("")
            lines.append("</details>")
            lines.append("")
    return lines


def render_exclusion_section(doenet_scan: dict, intalg_scan: dict) -> list[str]:
    lines = ["## Excluded Artifact Counts", ""]
    lines.append(
        "These counts show which obvious generated or machine-output paths were intentionally excluded from the ingestion pass."
    )
    lines.append("")
    for scan in (doenet_scan, intalg_scan):
        repo_name = scan["root"].name
        lines.append(f"### {repo_name}")
        lines.append("")
        if not scan["excluded_counts"]:
            lines.append("- No excluded artifacts detected")
            lines.append("")
            continue
        for reason, count in sorted(scan["excluded_counts"].items()):
            lines.append(f"- {reason}: {count}")
        lines.append("")
    return lines


def render_source_only_section(component_catalog: dict, component_sources: dict) -> list[str]:
    lines = ["## Source-Only and Docs-Only Topics", ""]
    lines.append(
        f"- Total source component types discovered in worker source: {len(component_sources['by_component'])}"
    )
    lines.append(
        f"- Source-only component types not present as concrete schema elements: {len(component_catalog['source_only'])}"
    )
    lines.append(
        f"- Docs-only topics without a direct schema or source component mapping: {len(component_catalog['docs_only_topics'])}"
    )
    lines.append("")

    lines.append("### Source-Only Component Types")
    lines.append("")
    for item in component_catalog["source_only"]:
        lines.append(f"#### {item['name']}")
        lines.append("")
        lines.append(f"- Internal component type: {yes_no(item['internal'])}")
        if item["description"]:
            lines.append(f"- Description from component index: {item['description']}")
        if item["docs_pages"]:
            lines.append(
                "- Documentation pages: "
                + "; ".join(markdown_link(page["path"], label=page["relative_path"]) for page in item["docs_pages"])
            )
        lines.append(
            "- Source entries: "
            + "; ".join(
                markdown_link(entry["path"], label=entry["relative_path"])
                + f" ({entry['class_name']} extends {entry['extends']})"
                for entry in item["entries"]
            )
        )
        lines.append("")

    lines.append("### Docs-Only Topics")
    lines.append("")
    for page in component_catalog["docs_only_topics"]:
        lines.append(
            f"- {page['title']}: {markdown_link(page['path'], label=page['relative_path'])}"
        )
    lines.append("")
    return lines


def docs_section(relative_path: str) -> str:
    for section in ("reference", "tutorials", "document_structure", "sandbox"):
        if f"/pages/{section}/" in f"/{relative_path}":
            return section
    return "other"


def extract_markdown_title(text: str, fallback: str) -> str:
    in_code = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith("# "):
            return clean_inline_text(line[2:].strip()) or fallback
    return fallback


def extract_first_paragraph(text: str) -> str:
    sanitized = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    lines = sanitized.splitlines()
    in_code = False
    paragraph_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("```"):
            in_code = not in_code
            if paragraph_lines:
                break
            continue
        if in_code:
            continue
        if not line:
            if paragraph_lines:
                break
            continue
        if line.startswith(DOC_SKIP_LINE_PREFIXES):
            continue
        if line.startswith("#") or line == "---":
            continue
        if line.startswith("<") and re.match(r"</?[A-Z]", line):
            continue
        paragraph_lines.append(line)

    return truncate(clean_inline_text(" ".join(paragraph_lines)), 260)


def derive_component_name(slug: str, title: str, section: str) -> str | None:
    cleaned_title = clean_inline_text(title)
    title_match = re.search(r"<\s*([A-Za-z][A-Za-z0-9_]*)\s*/?>", cleaned_title)
    if title_match:
        return title_match.group(1)
    if section != "reference":
        return None
    if slug in {"componentIndex", "componentTypes", "Sample_Component", "starting"}:
        return None
    if slug in {"row_table", "row_matrix"}:
        return "row"
    leading_alpha = re.match(r"([A-Za-z][A-Za-z0-9_]*?)(?:\d.*)?$", slug)
    if leading_alpha:
        return leading_alpha.group(1)
    return None


def count_examples(text: str) -> int:
    return len(
        re.findall(
            r"```doenet|```doenet-editor|```doenet-example|<DoenetExample|<DoenetEditor|<DoenetViewer",
            text,
            flags=re.IGNORECASE,
        )
    )


def clean_inline_text(text: str) -> str:
    cleaned = unescape(text)
    cleaned = re.sub(r"\{:[^}]+\}", "", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    cleaned = re.sub(
        r"</?([A-Za-z][A-Za-z0-9_]*)(?:\s+[^>]*)?/?>",
        lambda match: f"<{match.group(1)}>" if match.group(1)[0].islower() else " ",
        cleaned,
    )
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def extract_single_quoted_value(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def extract_string_array(text: str, pattern: str) -> list[str]:
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return []
    return re.findall(r"[\"']([^\"']+)[\"']", match.group(1))


def extract_tag_content(text: str, tag_name: str) -> str | None:
    match = re.search(rf"<{tag_name}\b[^>]*>(.*?)</{tag_name}>", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_html_title(text: str) -> str | None:
    return extract_tag_content(text, "title")


def extract_leading_comment_metadata(text: str) -> dict[str, str]:
    match = re.search(r"<!--(.*?)-->", text, flags=re.DOTALL)
    if not match:
        return {}
    metadata: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            metadata[key] = value
    return metadata


def count_tag(text: str, tag_name: str) -> int:
    return len(re.findall(rf"<{tag_name}\b", text))


def extract_external_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s\"'<>]+", text)
    return urls


def format_attribute(attribute: dict) -> str:
    parts = [attribute["name"]]
    values = attribute.get("values") or []
    if values:
        parts.append("values=" + ", ".join(values))
    autocomplete_values = attribute.get("autocompleteValues") or []
    if autocomplete_values:
        parts.append("autocomplete=" + ", ".join(autocomplete_values))
    return "; ".join(parts)


def format_property(prop: dict) -> str:
    type_name = prop.get("type")
    parts = [prop["name"]]
    if type_name:
        parts.append(f"type={type_name}")
    else:
        parts.append("type=omitted-in-schema")
    if prop.get("isArray"):
        dimensions = prop.get("numDimensions")
        if dimensions is not None:
            parts.append(f"array[{dimensions}D]")
        else:
            parts.append("array")
    indexed_entries = prop.get("indexedArrayDescription") or []
    if indexed_entries:
        parts.append(
            "indexedEntries="
            + ", ".join(format_indexed_entry(entry) for entry in indexed_entries)
        )
    return "; ".join(parts)


def format_indexed_entry(entry: dict) -> str:
    if entry.get("type"):
        return entry["type"]
    if entry.get("isArray"):
        dimensions = entry.get("numDimensions")
        if dimensions is not None:
            return f"array[{dimensions}D]"
        return "array"
    return "unspecified"


def markdown_link(path_obj: Path, label: str | None = None) -> str:
    relative_target = path_obj.relative_to(INTALG_ROOT) if path_obj.is_relative_to(INTALG_ROOT) else None
    if relative_target is None:
        relative_target = path_obj.relative_to(WORKSPACE_ROOT)
        target = "../" + relative_target.as_posix()
        display = label or relative_target.as_posix()
    else:
        target = relative_target.as_posix()
        if not target.startswith("."):
            target = "./" + target
        display = label or relative_target.as_posix()
    return f"[{display}]({quote(target, safe='/%#.:_()-')})"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def escape_table_text(text: str) -> str:
    return text.replace("|", "\\|")


if __name__ == "__main__":
    main()