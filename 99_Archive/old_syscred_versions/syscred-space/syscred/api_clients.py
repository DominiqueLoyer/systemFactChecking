# -*- coding: utf-8 -*-
"""
API Clients Module - SysCRED
============================
Handles all external API calls for the credibility verification system.

APIs intégrées:
- Web content fetching (requests + BeautifulSoup)
- WHOIS lookup for domain age
- Google Fact Check Tools API
- Backlinks estimation via CommonCrawl

(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerModelingHybridSystem2025
"""

import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import re
import json
from functools import lru_cache

# Optional imports with fallbacks
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Warning: BeautifulSoup not installed. Run: pip install beautifulsoup4")

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False
    print("Warning: python-whois not installed. Run: pip install python-whois")


# --- Data Classes for Structured Results ---

@dataclass
class WebContent:
    """Represents fetched web content."""
    url: str
    title: Optional[str]
    text_content: str
    meta_description: Optional[str]
    meta_keywords: List[str]
    links: List[str]
    fetch_timestamp: str
    success: bool
    error: Optional[str] = None


@dataclass
class DomainInfo:
    """Represents domain WHOIS information."""
    domain: str
    creation_date: Optional[datetime]
    expiration_date: Optional[datetime]
    registrar: Optional[str]
    age_days: Optional[int]
    success: bool
    error: Optional[str] = None


@dataclass
class FactCheckResult:
    """Represents a single fact-check claim review."""
    claim: str
    claimant: Optional[str]
    rating: str
    publisher: str
    url: str
    review_date: Optional[str]


@dataclass
class ExternalData:
    """Combined external data for credibility analysis."""
    fact_checks: List[FactCheckResult]
    source_reputation: str
    domain_age_days: Optional[int]
    domain_info: Optional[DomainInfo]
    related_articles: List[Dict[str, str]]
    backlinks_count: int
    backlinks_sample: List[Dict[str, str]]


class ExternalAPIClients:
    """
    Central class for all external API integrations.
    Replaces simulated functions with real API calls.
    """
    
    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize API clients.
        
        Args:
            google_api_key: API key for Google Fact Check Tools API (optional)
        """
        self.google_api_key = google_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Referer': 'https://www.google.com/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
        
        # Reputation database (can be extended or loaded from file)
        self.known_reputations = {
            # High credibility sources
            'lemonde.fr': 'High',
            'nytimes.com': 'High',
            'reuters.com': 'High',
            'bbc.com': 'High',
            'theguardian.com': 'High',
            'apnews.com': 'High',
            'nature.com': 'High',
            'sciencedirect.com': 'High',
            'scholar.google.com': 'High',
            'factcheck.org': 'High',
            'snopes.com': 'High',
            'politifact.com': 'High',
            # Medium credibility
            'wikipedia.org': 'Medium',
            'medium.com': 'Medium',
            'huffpost.com': 'Medium',
            # Low credibility (known misinformation spreaders)
            'infowars.com': 'Low',
            'naturalnews.com': 'Low',
        }
    
    def fetch_web_content(self, url: str, timeout: int = 10) -> WebContent:
        """
        Fetch and parse web content from a URL.
        
        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            WebContent dataclass with extracted information
        """
        timestamp = datetime.now().isoformat()
        
        if not HAS_BS4:
            return WebContent(
                url=url, title=None, text_content="",
                meta_description=None, meta_keywords=[],
                links=[], fetch_timestamp=timestamp,
                success=False, error="BeautifulSoup not installed"
            )
        
        try:
            try:
                response = self.session.get(url, timeout=timeout, allow_redirects=True)
                response.raise_for_status()
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
                print(f"[SysCRED] SSL/Connection error for {url}. Retrying without verification...")
                # Suppress warnings for unverified HTTPS request
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = self.session.get(url, timeout=timeout, allow_redirects=True, verify=False)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string.strip() if soup.title else None
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc.get('content', '') if meta_desc else None
            
            # Extract meta keywords
            meta_kw = soup.find('meta', attrs={'name': 'keywords'})
            meta_keywords = []
            if meta_kw and meta_kw.get('content'):
                meta_keywords = [k.strip() for k in meta_kw.get('content', '').split(',')]
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Extract main text content
            text_content = soup.get_text(separator=' ', strip=True)
            # Clean up excessive whitespace
            text_content = re.sub(r'\s+', ' ', text_content)
            
            # Extract links
            links = []
            for a_tag in soup.find_all('a', href=True)[:50]:  # Limit to 50 links
                href = a_tag['href']
                if href.startswith('http'):
                    links.append(href)
            
            return WebContent(
                url=url,
                title=title,
                text_content=text_content[:10000],  # Limit text size
                meta_description=meta_description,
                meta_keywords=meta_keywords,
                links=links,
                fetch_timestamp=timestamp,
                success=True
            )
            
        except requests.exceptions.Timeout:
            return WebContent(
                url=url, title=None, text_content="",
                meta_description=None, meta_keywords=[], links=[],
                fetch_timestamp=timestamp, success=False,
                error=f"Timeout after {timeout}s"
            )
        except requests.exceptions.RequestException as e:
            return WebContent(
                url=url, title=None, text_content="",
                meta_description=None, meta_keywords=[], links=[],
                fetch_timestamp=timestamp, success=False,
                error=str(e)
            )
        except Exception as e:
            return WebContent(
                url=url, title=None, text_content="",
                meta_description=None, meta_keywords=[], links=[],
                fetch_timestamp=timestamp, success=False,
                error=f"Parsing error: {str(e)}"
            )
    
    @lru_cache(maxsize=128)
    def whois_lookup(self, url_or_domain: str) -> DomainInfo:
        """
        Perform WHOIS lookup to get domain registration information.
        
        Args:
            url_or_domain: URL or domain name
            
        Returns:
            DomainInfo dataclass with domain details
        """
        # Extract domain from URL if needed
        if url_or_domain.startswith('http'):
            domain = urlparse(url_or_domain).netloc
        else:
            domain = url_or_domain
        
        # Remove 'www.' prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        if not HAS_WHOIS:
            return DomainInfo(
                domain=domain,
                creation_date=None, expiration_date=None,
                registrar=None, age_days=None,
                success=False, error="python-whois not installed"
            )
        
        try:
            w = whois.whois(domain)
            
            # Handle creation_date (can be a list or single value)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            
            # Handle expiration_date
            expiration_date = w.expiration_date
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]
            
            # Calculate age in days
            age_days = None
            if creation_date:
                if isinstance(creation_date, datetime):
                    age_days = (datetime.now() - creation_date).days
            
            return DomainInfo(
                domain=domain,
                creation_date=creation_date,
                expiration_date=expiration_date,
                registrar=w.registrar,
                age_days=age_days,
                success=True
            )
            
        except Exception as e:
            return DomainInfo(
                domain=domain,
                creation_date=None, expiration_date=None,
                registrar=None, age_days=None,
                success=False, error=str(e)
            )
    
    def google_fact_check(self, query: str, language: str = "fr") -> List[FactCheckResult]:
        """
        Query Google Fact Check Tools API.
        
        Args:
            query: The claim or text to check
            language: Language code (default: French)
            
        Returns:
            List of FactCheckResult objects
        """
        results = []
        
        if not self.google_api_key:
            print("[Info] Google Fact Check API key not configured. Using simulation.")
            return self._simulate_fact_check(query)
        
        try:
            api_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            params = {
                'key': self.google_api_key,
                'query': query[:200],  # API has character limit
                # 'languageCode': language  # Removed to allow all languages (e.g. English queries)
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            claims = data.get('claims', [])
            for claim in claims[:5]:  # Limit to 5 results
                text = claim.get('text', '')
                claimant = claim.get('claimant')
                
                for review in claim.get('claimReview', []):
                    results.append(FactCheckResult(
                        claim=text,
                        claimant=claimant,
                        rating=review.get('textualRating', 'Unknown'),
                        publisher=review.get('publisher', {}).get('name', 'Unknown'),
                        url=review.get('url', ''),
                        review_date=review.get('reviewDate')
                    ))
            
            return results
            
        except Exception as e:
            print(f"[Warning] Google Fact Check API error: {e}")
            return self._simulate_fact_check(query)
    
    def _simulate_fact_check(self, query: str) -> List[FactCheckResult]:
        """Fallback simulation when API is not available."""
        # Check for known misinformation patterns
        misinformation_keywords = [
            'conspiracy', 'hoax', 'fake', 'miracle cure', 'they don\'t want you to know',
            'mainstream media lies', 'deep state', 'plandemic'
        ]
        
        query_lower = query.lower()
        for keyword in misinformation_keywords:
            if keyword in query_lower:
                return [FactCheckResult(
                    claim=f"Text contains potential misinformation marker: '{keyword}'",
                    claimant=None,
                    rating="Needs Verification",
                    publisher="SysCRED Heuristic",
                    url="",
                    review_date=datetime.now().isoformat()
                )]
        
        return []  # No fact checks found
    
    @lru_cache(maxsize=128)
    def get_source_reputation(self, url: str) -> str:
        """
        Get reputation score for a source/domain.
        
        Args:
            url: URL or domain to check
            
        Returns:
            Reputation level: 'High', 'Medium', 'Low', or 'Unknown'
        """
        if url.startswith('http'):
            domain = urlparse(url).netloc
        else:
            domain = url
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check known reputations
        for known_domain, reputation in self.known_reputations.items():
            if domain.endswith(known_domain) or known_domain in domain:
                return reputation
        
        # Heuristics for unknown domains
        # Academic domains tend to be more credible
        if domain.endswith('.edu') or domain.endswith('.gov') or domain.endswith('.ac.uk'):
            return 'High'
        
        # Personal sites and free hosting are less credible
        if any(x in domain for x in ['.blogspot.', '.wordpress.', '.wix.', '.weebly.']):
            return 'Low'
        
        return 'Unknown'
    
    def estimate_backlinks(self, url: str) -> Dict[str, Any]:
        """
        Estimate relative authority/backlinks based on available signals.
        
        Since real backlink databases (Ahrefs, Moz) are paid/proprietary,
        we use a composite heuristic based on:
        1. Domain age (older domains tend to have more backlinks)
        2. Known reputation (High reputation sources imply high backlinks)
        3. Google Fact Check mentions (as a proxy for visibility in fact-checks)
        """
        domain = urlparse(url).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # 1. Base Score from Reputation
        reputation = self.get_source_reputation(domain)
        base_count = 0
        if reputation == 'High':
            base_count = 10000  # High authority
        elif reputation == 'Medium':
            base_count = 1000   # Medium authority
        elif reputation == 'Low':
            base_count = 50     # Low authority
        else:
            base_count = 100    # Unknown
            
        # 2. Multiplier from Domain Age
        age_multiplier = 1.0
        domain_info = self.whois_lookup(domain)
        if domain_info.success and domain_info.age_days:
            # Add 10% for every year of age, max 5x
            years = domain_info.age_days / 365
            age_multiplier = min(5.0, 1.0 + (years * 0.1))
            
        estimated_count = int(base_count * age_multiplier)
        
        # 3. Adjust for specific TLDs
        if domain.endswith('.edu') or domain.endswith('.gov'):
            estimated_count *= 2
            
        return {
            'estimated_count': estimated_count,
            'sample_backlinks': [], # Real sample requires SERP API
            'method': 'heuristic_v2.1',
            'note': 'Estimated from domain age and reputation (Proxy)'
        }
    
    def fetch_external_data(self, input_data: str, fc_query: str = None) -> ExternalData:
        """
        Main method to fetch all external data for credibility analysis.
        This replaces the simulated fetch_external_data function.
        
        Args:
            input_data: URL or text to analyze
            
        Returns:
            ExternalData with all gathered information
        """
        from urllib.parse import urlparse
        
        # Determine if input is URL
        is_url = False
        try:
            result = urlparse(input_data)
            is_url = all([result.scheme, result.netloc])
        except:
            pass
        
        # Initialize results
        domain_age_days = None
        domain_info = None
        source_reputation = 'Unknown'
        fact_checks = []
        backlinks_data = {'estimated_count': 0, 'sample_backlinks': []}
        
        if is_url:
            # Get domain information
            domain_info = self.whois_lookup(input_data)
            if domain_info.success:
                domain_age_days = domain_info.age_days
            
            # Get source reputation
            source_reputation = self.get_source_reputation(input_data)
            
            # Get backlink estimation
            backlinks_data = self.estimate_backlinks(input_data)
        
        # Perform fact check on the content/URL
        # Use provided query or fall back to input_data
        query_to_use = fc_query if fc_query else input_data
        fact_checks = self.google_fact_check(query_to_use)
        
        return ExternalData(
            fact_checks=fact_checks,
            source_reputation=source_reputation,
            domain_age_days=domain_age_days,
            domain_info=domain_info,
            related_articles=[],  # TODO: Implement related article search
            backlinks_count=backlinks_data.get('estimated_count', 0),
            backlinks_sample=backlinks_data.get('sample_backlinks', [])
        )


# --- Testing ---
if __name__ == "__main__":
    print("=== Testing ExternalAPIClients ===\n")
    
    client = ExternalAPIClients()
    
    # Test 1: Web content fetching
    print("Test 1: Fetching web content from Le Monde...")
    content = client.fetch_web_content("https://www.lemonde.fr")
    print(f"  Success: {content.success}")
    print(f"  Title: {content.title}")
    print(f"  Text length: {len(content.text_content)} chars")
    print(f"  Links found: {len(content.links)}")
    print()
    
    # Test 2: WHOIS lookup
    print("Test 2: WHOIS lookup for lemonde.fr...")
    domain_info = client.whois_lookup("https://www.lemonde.fr")
    print(f"  Success: {domain_info.success}")
    print(f"  Domain: {domain_info.domain}")
    print(f"  Age: {domain_info.age_days} days")
    print(f"  Registrar: {domain_info.registrar}")
    print()
    
    # Test 3: Source reputation
    print("Test 3: Source reputation checks...")
    test_urls = [
        "https://www.nytimes.com/article",
        "https://www.infowars.com/post",
        "https://random-blog.wordpress.com"
    ]
    for url in test_urls:
        rep = client.get_source_reputation(url)
        print(f"  {url}: {rep}")
    print()
    
    # Test 4: Full external data
    print("Test 4: Full external data fetch...")
    external_data = client.fetch_external_data("https://www.bbc.com/news")
    print(f"  Source reputation: {external_data.source_reputation}")
    print(f"  Domain age: {external_data.domain_age_days} days")
    print(f"  Fact checks found: {len(external_data.fact_checks)}")
    
    print("\n=== Tests Complete ===")
