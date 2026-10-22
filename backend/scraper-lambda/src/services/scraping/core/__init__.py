"""
Shared building blocks for config-driven scrapers.

- models:          dataclasses describing sources, discovered documents and results
- config_loader:   loads source definitions from config/sources/*.yaml
- fetchers:        HTTP / browser fetchers behind a common interface
- storage:         S3 / local storage behind a common interface
- file_detector:   file type detection from content
- text_extractor:  HTML -> markdown conversion
"""
