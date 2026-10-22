"""
Query building utilities for knowledge base retrieval.

Retrieval queries are keyword-focused (no instructions).
Generation prompts are in prompts.py.
"""
import logging
from typing import Any

from src.services import retrieval_service


logger = logging.getLogger(__name__)

# Multi-script crop mappings (Cyrillic | Latin | English)
CROP_MULTI_SCRIPT = {
    "corn": "кукуруз | kukuruz | corn | maize",
    "maize": "кукуруз | kukuruz | corn | maize",
    "wheat": "пшеница | pšenica | psenica | wheat",
    "soybean": "соја | soja | soybean | soy",
    "soy": "соја | soja | soybean | soy",
    "sunflower": "сунцокрет | suncokret | sunflower",
}

# Price-related keywords in all scripts
PRICE_KEYWORDS = "цена | cena | price | откупна цена | otkupna cena | purchase price"
PRICE_UNITS = "РСД/кг | RSD/kg | дин/кг | din/kg | дин/kg | динара | dinara"
DOMESTIC_MARKET = "домаће тржиште | domaće tržište | domestic market | Србија | Srbija | Serbia"
PRODUCTION_KEYWORDS = "производња | proizvodnja | production | принос | prinos | yield | површина | површina | area | жетва | žetva | harvest"

# Document header that contains both domestic and foreign market info
REPORT_HEADER = "Производња, прерада и тржиште | Proizvodnja, prerada i tržište | production processing market"

# Foreign/World market keywords for geopolitical analysis (generic, not country-specific)
WORLD_MARKET = "светско тржиште | svetsko tržište | world market | global market | international market"
TRADE_KEYWORDS = "извоз | izvoz | export | увоз | uvoz | import | трговина | trgovina | trade | међународна трговина | međunarodna trgovina | international trade"
POLICY_KEYWORDS = "царине | carine | tariffs | санкције | sankcije | sanctions | трговински споразуми | trgovinski sporazumi | trade agreements | политика | politika | policy"
INTL_PRICES = "USD/t | EUR/t | FOB | CIF | светска цена | svetska cena | world price | international price"


def get_crop_multi_script(crop: str) -> str:
    """
    Get all script variants for a crop name.

    Args:
        crop: English crop name

    Returns:
        String with Cyrillic | Latin | English variants
    """
    return CROP_MULTI_SCRIPT.get(crop.lower(), crop.lower())


def build_production_query(crops: list[str], years: list[int]) -> str:
    """
    Build query focused on production/domestic market data.

    For Market Overview section: area, yield, harvest, production stats.
    """
    crop_terms = " | ".join([get_crop_multi_script(c) for c in crops])
    years_str = " ".join(str(y) for y in sorted(years))

    return f"""
{crop_terms}
{REPORT_HEADER}
{DOMESTIC_MARKET}
{PRODUCTION_KEYWORDS}
биланс | bilans | balance sheet
жетва | žetva | harvest
засејана површина | zasejana površina | planted area
принос по хектару | prinos po hektaru | yield per hectare
Србија | Serbia | Serbian
{years_str}
""".strip()


def build_price_query(crops: list[str], years: list[int]) -> str:
    """
    Build query focused on price data (combined query for all crops).

    For Price Analysis section: RSD/kg prices, exchange trading, price trends.
    Uses document header pattern (Производња, прерада и тржиште + crop + цена) for better retrieval.

    NOTE: For better per-crop coverage, use build_single_crop_price_query instead.
    """
    crop_terms = " | ".join([get_crop_multi_script(c) for c in crops])
    years_str = " ".join(str(y) for y in sorted(years))

    # Crop-specific price search patterns (document header + crop + price)
    crop_price_patterns = " | ".join([
        f"Производња, прерада и тржиште {get_crop_multi_script(c).split(' | ')[0]} цена"
        for c in crops
    ])

    return f"""
{crop_terms}
{crop_price_patterns}
{PRICE_KEYWORDS}
{PRICE_UNITS}
берза Нови Сад | berza Novi Sad | Novi Sad commodity exchange
Продуктна берза | Produktna berza | commodity exchange
трговање | trgovanje | trading
откупна цена | otkupna cena | purchase price
недељни извештај | nedeljni izvestaj | weekly report
котација | kotacija | quotation
форвард | forward | forward contract
{DOMESTIC_MARKET}
{years_str}
""".strip()


# Cyrillic uppercase crop names as they appear in document headers
CROP_CYRILLIC_UPPERCASE = {
    "corn": "КУКУРУЗ",
    "maize": "КУКУРУЗ",
    "wheat": "ПШЕНИЦА",
    "soybean": "СОЈА",
    "soy": "СОЈА",
    "sunflower": "СУНЦОКРЕТ",
}


def build_single_crop_price_query(crop: str, years: list[int]) -> str:
    """
    Build price query for a SINGLE crop.

    Uses the exact document header format that appears in source documents:
    "Производња, прерада и тржиште" + "Производ: ПШЕНИЦА" + price keywords

    This ensures each crop's price data is retrieved without being drowned out
    by more prevalent crops in the combined query.
    """
    crop_multi = get_crop_multi_script(crop)
    crop_upper = CROP_CYRILLIC_UPPERCASE.get(crop.lower(), crop.upper())
    years_str = " ".join(str(y) for y in sorted(years))

    return f"""
{crop_multi}
Производња, прерада и тржиште
Производ: {crop_upper}
{crop_upper} цена | {crop_multi.split(' | ')[0]} цена
{PRICE_KEYWORDS}
{PRICE_UNITS}
берза | berza | exchange
трговање | trgovanje | trading
котација | kotacija | quotation
{years_str}
""".strip()


def build_geopolitical_query(crops: list[str], years: list[int]) -> str:
    """
    Build query focused on world market and geopolitical data.

    For Geopolitical Analysis section: world market, trade, exports, global prices.
    """
    crop_terms = " | ".join([get_crop_multi_script(c) for c in crops])
    years_str = " ".join(str(y) for y in sorted(years))

    return f"""
{crop_terms}
{WORLD_MARKET}
{TRADE_KEYWORDS}
{POLICY_KEYWORDS}
{INTL_PRICES}
USDA | FAO | IGC
светска производња | svetska proizvodnja | world production
глобални биланс | globalni bilans | global balance
извоз | izvoz | export
увоз | uvoz | import
Црно море | Crno more | Black Sea
Украјина | Ukrajina | Ukraine
Русија | Rusija | Russia
ЕУ | EU | European Union
{years_str}
""".strip()


def retrieve_by_section(
    crops: list[str],
    country: str,
    years: list[int],
    results_per_section: int = 50
) -> dict[str, list[dict[str, Any]]]:
    """
    Retrieve documents organized by report section.

    Makes targeted calls instead of mixed retrieval:
    - Production: domestic market, area, yield, harvest data (1 combined call)
    - Price: RSD/kg prices, exchange trading (SEPARATE call per crop to ensure coverage)
    - Geopolitical: world market, trade, exports, global context (1 combined call)

    Args:
        crops: List of crops to analyze
        country: Country context
        years: Years to filter
        results_per_section: Number of chunks per section

    Returns:
        Dict with keys 'production', 'price', 'geopolitical',
        each containing a list of relevant chunks
    """
    sections = {}

    def deduplicate_within_section(chunks: list, section_name: str) -> list:
        """Deduplicate chunks within a section only (allows same chunk in multiple sections)."""
        seen = set()
        unique = []
        for chunk in chunks:
            content_hash = hash(chunk.get("content", "")[:500])
            if content_hash not in seen:
                chunk["section_query"] = section_name
                unique.append(chunk)
                seen.add(content_hash)
        return unique

    # 1. Production/domestic market data
    logger.info("Retrieving production/domestic market chunks...")
    prod_query = build_production_query(crops, years)
    prod_chunks = retrieval_service.retrieve_only(prod_query, num_results=results_per_section)
    sections["production"] = deduplicate_within_section(prod_chunks, "production")
    logger.info(f"  Retrieved {len(sections['production'])} production chunks")

    # 2. Price data - PER-CROP retrieval to ensure each crop gets coverage
    # This prevents corn/soybean from drowning out wheat/sunflower in combined queries
    logger.info("Retrieving price data chunks (per-crop)...")
    all_price_chunks = []
    chunks_per_crop = max(15, results_per_section // len(crops)) if crops else results_per_section

    for crop in crops:
        logger.info(f"  Retrieving price chunks for {crop}...")
        crop_price_query = build_single_crop_price_query(crop, years)
        crop_price_chunks = retrieval_service.retrieve_only(crop_price_query, num_results=chunks_per_crop)
        # Tag each chunk with the crop it was retrieved for
        for chunk in crop_price_chunks:
            chunk["price_query_crop"] = crop
        all_price_chunks.extend(crop_price_chunks)
        logger.info(f"    Retrieved {len(crop_price_chunks)} chunks for {crop}")

    sections["price"] = deduplicate_within_section(all_price_chunks, "price")
    logger.info(f"  Total price chunks after dedup: {len(sections['price'])}")

    # 3. Geopolitical/world market data
    logger.info("Retrieving geopolitical/world market chunks...")
    geo_query = build_geopolitical_query(crops, years)
    geo_chunks = retrieval_service.retrieve_only(geo_query, num_results=results_per_section)
    sections["geopolitical"] = deduplicate_within_section(geo_chunks, "geopolitical")
    logger.info(f"  Retrieved {len(sections['geopolitical'])} geopolitical chunks")

    total = sum(len(v) for v in sections.values())
    logger.info(f"Total chunks across all sections (may include duplicates): {total}")

    return sections
