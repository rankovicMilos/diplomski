from src.config.prompts import build_peer_analysis_prompt
from src.services.industry_config import industry_for_nace, load_industry_profile


def test_industry_for_nace_matches_by_prefix():
    assert industry_for_nace("D35.14")[0] == "electricity"
    assert industry_for_nace("D35")[0] == "electricity"
    assert industry_for_nace("A1.11")[0] == "cereals"
    assert industry_for_nace("Z99.99") is None
    assert industry_for_nace(None) is None


def test_profiles_load_from_the_scraper_configs():
    profile = load_industry_profile("electricity")
    assert profile.config_origin == "bundled:electricity.yaml"
    assert any(s.id == "market_overview" for s in profile.sections)


def test_peer_prompt_sector_is_filled_in():
    prompt = build_peer_analysis_prompt("Electricity", "D35.14")
    assert "companies in the Electricity sector" in prompt
    assert '"sector": "D35.14"' in prompt
    assert "<<" not in prompt
    assert "grain" not in build_peer_analysis_prompt(None, None).lower()
