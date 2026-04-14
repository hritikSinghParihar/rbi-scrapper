from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from typing import List, Dict, Any
from app.core.constants import INDEX_URL

def parse_hidden_form_data(html: str) -> Dict[str, str]:
    """Parses hidden input fields from ASP.NET form."""
    tree = HTMLParser(html)
    return {
        tag.attributes.get("name"): tag.attributes.get("value", "") 
        for tag in tree.css("input[type='hidden']") 
        if tag.attributes.get("name")
    }

def parse_circular_links(html: str) -> List[Dict[str, str]]:
    """Extracts circular links and titles from the index page."""
    tree = HTMLParser(html)
    links = {}
    for a in tree.css("a"):
        href = a.attributes.get("href", "")
        if "BS_CircularIndexDisplay.aspx?Id=" in href:
            full_url = urljoin(INDEX_URL, href)
            name = a.text(strip=True) or ("Circular_" + href.split("Id=")[-1])
            links[full_url] = {"url": full_url, "name": name}
    return list(links.values())

def parse_pdf_link(html: str, base_url: str) -> str:
    """Extracts the direct PDF download link from a detail page."""
    tree = HTMLParser(html)
    pdf_tag = tree.css_first('a[id^="APDF_"]')
    if not pdf_tag:
        return ""
    
    pdf_url = pdf_tag.attributes.get("href", "")
    if not pdf_url.startswith('http'):
        pdf_url = urljoin(base_url, pdf_url)
    return pdf_url
